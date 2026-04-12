"""
POST /api/v1/recommend

Request lifecycle:
  1. Validate UserSurvey (Pydantic)
  2. Generate session UUID; cache survey in Redis (non-blocking)
  3. Fetch full card catalogue from cards-service
  4. Phase 1 — eligibility filter
  5. Phase 2 — EANV calculation
  6. Phase 3 — ranking + top 2
  7. Return RecommendationResponse
"""

import asyncio
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.cache.redis_client import RedisClient
from app.clients.cards_client import CardsServiceError, fetch_all_cards, store_survey_response
from app.config import settings
from app.engine import eligibility, eanv as eanv_engine
from app.engine import ranking as rule_ranker
from app.engine.eanv import EANVResult
from app.engine.llm_ranker import top_n_llm
from app.engine.ranking import RankedCard
from app.models.card import Card
from app.models.responses import (
    CardResult,
    CategoryBreakdown,
    RecommendationResponse,
)
from app.models.survey import UserSurvey

router = APIRouter(prefix="/api/v1", tags=["recommend"])


# ── Credit tier rank (higher = better) ────────────────────────────────────────

_TIER_RANK = {"Poor": 1, "Fair": 2, "Good": 3, "Excellent": 4}
# Very Good (740-799) and Exceptional (800-850) both qualify for Excellent-tier cards.
# The FICO rank (4 and 5) is used only for sorting within the eligible set — not for filtering.


def _tier_score(result: EANVResult) -> int:
    """Cards that require a HIGHER credit tier are more prestigious — rank them first."""
    return _TIER_RANK.get(result.card.credit_tier_min.value, 0)


def _is_co_branded(card) -> bool:
    return card.airline_affinity is not None or card.hotel_affinity is not None


def _make_ranked(result: EANVResult, llm_picks: list[RankedCard], fallback_why: str) -> RankedCard:
    why = next(
        (rc.why_this_card for rc in llm_picks if rc.result.card.card_id == result.card.card_id),
        fallback_why,
    )
    return RankedCard(result=result, ranking_score=result.eanv, why_this_card=why)


# ── Post-processing rules ──────────────────────────────────────────────────────

def _apply_recommendation_rules(
    llm_picks: list[RankedCard],
    eanv_results: list[EANVResult],
    survey,
) -> list[RankedCard]:
    """
    Determines the final two recommendations after LLM/rule ranking.

    Priority logic:
      - Credit tier is the primary filter (already enforced by Phase 1 eligibility).
        Within eligible cards, prefer cards targeting the highest matching tier first.
      - Rank 1: Best general (non-co-branded) card by credit tier + EANV.
                If no-annual-fee preference, restrict rank 1 to $0-fee cards.
      - Rank 2: If user has airline/hotel preference → best matching co-branded card.
                Otherwise → next-best general card (different from rank 1).
    """
    if not eanv_results:
        return llm_picks

    has_preference = bool(survey.airline_preference or survey.hotel_preference)
    airline_pref = survey.airline_preference.value if survey.airline_preference else None
    hotel_pref = survey.hotel_preference.value if survey.hotel_preference else None

    # ── Pool A: General cards (non-co-branded) ─────────────────────────────────
    # Sorted by credit_tier_min desc (better tier first), then EANV desc
    general = sorted(
        [r for r in eanv_results if not _is_co_branded(r.card)],
        key=lambda r: (_tier_score(r), r.eanv),
        reverse=True,
    )

    # ── Pool B: Preference-matched co-branded cards ────────────────────────────
    preference_cards = sorted(
        [
            r for r in eanv_results
            if _is_co_branded(r.card)
            and (
                (airline_pref and r.card.airline_affinity == airline_pref)
                or (hotel_pref and r.card.hotel_affinity == hotel_pref)
            )
        ],
        key=lambda r: (_tier_score(r), r.eanv),
        reverse=True,
    )

    # ── Rank 1: Best general card ───────────────────────────────────────────────
    if not survey.willing_to_pay_fee:
        no_fee_general = [r for r in general if float(r.card.annual_fee) == 0]
        rank1_pool = no_fee_general or general
    else:
        rank1_pool = general

    if not rank1_pool:
        return llm_picks  # Nothing to override — return LLM picks as-is

    rank1_result = rank1_pool[0]
    rank1 = _make_ranked(
        rank1_result,
        llm_picks,
        f"Best match for your credit profile — earns ${rank1_result.eanv:.0f}/yr net value.",
    )

    # ── Rank 2: Preference card or next-best general ───────────────────────────
    rank1_id = rank1_result.card.card_id

    if has_preference and preference_cards:
        # User has airline/hotel preference → show the best matching co-branded card
        rank2_result = preference_cards[0]
        pref_label = (
            f"{airline_pref.title()} airline" if airline_pref
            else f"{hotel_pref.title()} hotel"
        )
        rank2 = _make_ranked(
            rank2_result,
            llm_picks,
            f"Matches your {pref_label} preference — earn bonus rewards and unlock exclusive cardholder benefits.",
        )
    else:
        # No preference → next-best general card
        next_general = next((r for r in general if r.card.card_id != rank1_id), None)
        if next_general:
            rank2 = _make_ranked(
                next_general,
                llm_picks,
                f"Strong alternative — earns ${next_general.eanv:.0f}/yr net value.",
            )
        elif len(llm_picks) > 1:
            rank2 = llm_picks[1]
        else:
            return [rank1]

    return [rank1, rank2]


# ── Dependencies ───────────────────────────────────────────────────────────────

def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_redis(request: Request) -> RedisClient:
    return request.app.state.redis


async def get_cards(
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> list[Card]:
    """Fetch the full card catalogue from cards-service."""
    try:
        return await fetch_all_cards(client, settings.cards_service_url)
    except CardsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


# ── Response mapper ────────────────────────────────────────────────────────────

def _to_card_result(ranked: RankedCard) -> CardResult:
    result = ranked.result
    card = result.card
    bd = result.breakdown

    return CardResult(
        card_id=card.card_id,
        issuer=card.issuer,
        card_name=card.card_name,
        annual_fee=float(card.annual_fee),
        reward_type=card.reward_type.value,
        reward_network=card.reward_network,
        affiliate_link=card.affiliate_link,
        eanv=result.eanv,
        rewards_total=result.rewards_total,
        signup_bonus_value=result.signup_bonus_applied,
        category_breakdown=CategoryBreakdown(
            groceries=bd.groceries,
            dining=bd.dining,
            gas=bd.gas,
            travel=bd.travel,
            transit=bd.transit,
            streaming=bd.streaming,
            online_retail=bd.online_retail,
            utilities=bd.utilities,
        ),
        why_this_card=ranked.why_this_card,
        has_lounge_access=card.has_lounge_access,
        has_global_entry=card.has_global_entry,
        intro_apr_months=card.intro_apr_months,
        ongoing_apr_min=float(card.ongoing_apr_min),
        ongoing_apr_max=float(card.ongoing_apr_max),
    )


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get top credit card recommendations",
    description=(
        "Accepts a completed 20-question survey, runs eligibility filtering, "
        "EANV calculation, and preference ranking, and returns the top 2 cards."
    ),
)
async def recommend(
    request: Request,
    survey: UserSurvey,
    cards: Annotated[list[Card], Depends(get_cards)],
    redis: Annotated[RedisClient, Depends(get_redis)],
    year: Annotated[int, Query(ge=1, le=2, description="1 = include sign-up bonus, 2 = exclude")] = 1,
) -> RecommendationResponse:
    session_id = str(uuid.uuid4())

    # Cache survey (fire-and-forget — Redis failure must not block the response)
    await redis.set_session(session_id, survey)

    # Phase 1 — Eligibility filter
    eligible = eligibility.filter_eligible(cards, survey)

    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No cards match your eligibility profile. "
                "This may be due to your credit tier or recent inquiry count."
            ),
        )

    # Phase 2 — EANV calculation
    eanv_results: list[EANVResult] = eanv_engine.calculate_all(eligible, survey, year)

    # Phase 3 — AI ranking (DeepSeek) with rule-based fallback
    top: list[RankedCard] = await top_n_llm(eanv_results, survey, year, n=2)

    # Enforce business rules: #13 (no-fee rank 1) and #16 (hotel preference rank 2)
    top = _apply_recommendation_rules(top, eanv_results, survey)

    response = RecommendationResponse(
        session_id=session_id,
        year=year,
        top_cards=[_to_card_result(rc) for rc in top],
        cards_evaluated=len(eligible),
    )

    # Clear Redis session so stale data is never replayed
    asyncio.create_task(redis.delete_session(session_id))

    # Persist survey + results — fire-and-forget, never blocks the response
    asyncio.create_task(store_survey_response(
        client=request.app.state.http_client,
        base_url=settings.cards_service_url,
        payload={
            "session_id": session_id,
            "survey_input": survey.model_dump(mode="json"),
            "recommended_cards": [c.model_dump(mode="json") for c in response.top_cards],
            "cards_evaluated": response.cards_evaluated,
        },
    ))

    return response
