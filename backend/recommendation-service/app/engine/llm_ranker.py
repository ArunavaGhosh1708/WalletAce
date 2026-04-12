"""
Phase 3 (LLM) — AI-Powered Ranking Engine

Replaces the rule-based Phase 3 with DeepSeek, which selects the top 2
cards from the EANV-scored eligible set and generates personalised explanations.

Strategy:
  - Phase 1 (eligibility) and Phase 2 (EANV math) remain deterministic.
  - DeepSeek receives the top-N pre-scored cards + the user's full profile,
    then applies holistic reasoning to rank and explain the final picks.
  - If the LLM call fails for any reason, we fall back to the rule-based
    ranking engine so the endpoint never returns an error to the user.
"""

import json
import logging

from openai import AsyncOpenAI

from app.config import settings
from app.engine import ranking as rule_ranker
from app.engine.eanv import EANVResult
from app.engine.ranking import RankedCard
from app.models.survey import UserSurvey

logger = logging.getLogger(__name__)

# Only pass the top N candidates to the LLM to keep the prompt focused
_MAX_CANDIDATES = 15

_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_MODEL = "deepseek-chat"  # DeepSeek-V3 — fast, capable, OpenAI-compatible


# ── Prompt builders ────────────────────────────────────────────────────────────

def _user_summary(survey: UserSurvey) -> dict:
    return {
        "fico_tier": survey.fico_tier.value,
        "annual_income_usd": survey.annual_income,
        "employment_status": survey.employment_status.value,
        "carries_balance": survey.carries_balance,
        "needs_intro_apr": survey.needs_intro_apr,
        "willing_to_pay_annual_fee": survey.willing_to_pay_fee,
        "prefers_cash_back": survey.prefers_cash_back,
        "airline_preference": survey.airline_preference.value if survey.airline_preference else None,
        "hotel_preference": survey.hotel_preference.value if survey.hotel_preference else None,
        "monthly_spending_usd": {
            "groceries": survey.monthly_groceries,
            "dining": survey.monthly_dining,
            "gas": survey.monthly_gas,
            "travel": survey.monthly_travel,
            "transit": survey.monthly_transit,
            "streaming": survey.monthly_streaming,
            "online_retail": survey.monthly_online_retail,
            "utilities": survey.monthly_utilities,
        },
    }


def _card_summary(result: EANVResult, year: int) -> dict:
    card = result.card
    bd = result.breakdown
    return {
        "card_id": str(card.card_id),
        "issuer": card.issuer,
        "card_name": card.card_name,
        "annual_fee": result.annual_fee,
        "reward_type": card.reward_type.value,
        "reward_network": card.reward_network,
        "eanv_usd": result.eanv,
        "rewards_total_usd": result.rewards_total,
        "signup_bonus_usd": result.signup_bonus_applied if year == 1 else 0,
        "annual_rewards_by_category_usd": {
            "groceries": round(bd.groceries, 2),
            "dining": round(bd.dining, 2),
            "gas": round(bd.gas, 2),
            "travel": round(bd.travel, 2),
            "transit": round(bd.transit, 2),
            "streaming": round(bd.streaming, 2),
            "online_retail": round(bd.online_retail, 2),
            "utilities": round(bd.utilities, 2),
        },
        "ongoing_apr": {
            "min_pct": float(card.ongoing_apr_min),
            "max_pct": float(card.ongoing_apr_max),
        },
        "intro_apr_months": card.intro_apr_months,
        "has_lounge_access": card.has_lounge_access,
        "has_global_entry": card.has_global_entry,
        "airline_affinity": card.airline_affinity,
        "hotel_affinity": card.hotel_affinity,
    }


_SYSTEM_PROMPT = """\
You are an expert credit card advisor. Your job is to select the best 2 credit cards \
for a user and write a personalised explanation for each pick.

You will receive:
1. The user's financial profile and preferences.
2. A list of eligible cards already filtered for the user's credit tier, income, and \
eligibility rules. Each card includes its Expected Annual Net Value (EANV = rewards + \
sign-up bonus - annual fee) calculated against the user's actual spending.

Your task:
- Pick the 2 cards that are the best fit for THIS specific user.
- Consider EANV, category spend alignment, their preference for cash back vs points, \
  airline/hotel loyalty, fee tolerance, APR if they carry a balance, lounge access \
  for frequent travellers, and sign-up bonus achievability.
- Write a concise, specific 1–2 sentence "why_this_card" for each pick that references \
  the user's actual spending numbers or preferences. Do not be generic.

Respond ONLY with a JSON object in this exact schema:
{
  "picks": [
    {"card_id": "<uuid string>", "why_this_card": "<explanation>"},
    {"card_id": "<uuid string>", "why_this_card": "<explanation>"}
  ]
}

Rules:
- picks must contain exactly 2 entries.
- card_id must be a card_id from the provided card list.
- Do not include any text outside the JSON object.\
"""


def _build_user_prompt(survey: UserSurvey, candidates: list[EANVResult], year: int) -> str:
    user = _user_summary(survey)
    cards = [_card_summary(r, year) for r in candidates]
    return (
        f"USER PROFILE:\n{json.dumps(user, indent=2)}\n\n"
        f"ELIGIBLE CARDS (pre-sorted by EANV descending, Year {year}):\n"
        f"{json.dumps(cards, indent=2)}"
    )


# ── Main entry point ───────────────────────────────────────────────────────────

async def top_n_llm(
    eanv_results: list[EANVResult],
    survey: UserSurvey,
    year: int,
    n: int = 2,
) -> list[RankedCard]:
    """
    Use DeepSeek to select the top n cards from the EANV-scored candidates
    and generate personalised explanations.

    Falls back to the rule-based ranking engine if the LLM call fails.

    Args:
        eanv_results: EANV results sorted descending (output of Phase 2).
        survey:       Validated UserSurvey.
        year:         1 = include sign-up bonus, 2 = exclude.
        n:            Number of cards to return (default 2).

    Returns:
        List of RankedCard (length ≤ n).
    """
    if not settings.deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY not set — falling back to rule-based ranking")
        return rule_ranker.top_n(eanv_results, survey, n=n)

    candidates = eanv_results[:_MAX_CANDIDATES]
    card_lookup: dict[str, EANVResult] = {str(r.card.card_id): r for r in candidates}

    try:
        client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=_DEEPSEEK_BASE_URL,
        )

        response = await client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(survey, candidates, year)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # low temperature for consistent, factual recommendations
            max_tokens=512,
        )

        raw = response.choices[0].message.content or ""
        data = json.loads(raw)
        picks = data.get("picks", [])

        ranked: list[RankedCard] = []
        for i, pick in enumerate(picks[:n]):
            card_id = pick.get("card_id", "")
            eanv_result = card_lookup.get(card_id)
            if eanv_result is None:
                logger.warning("LLM returned unknown card_id %s — skipping", card_id)
                continue
            ranked.append(
                RankedCard(
                    result=eanv_result,
                    ranking_score=float(n - i),  # ordinal score (not surfaced to user)
                    why_this_card=pick.get("why_this_card", "").strip(),
                )
            )

        if not ranked:
            raise ValueError("LLM returned no valid card picks")

        return ranked

    except Exception:
        logger.exception("LLM ranking failed — falling back to rule-based ranking")
        return rule_ranker.top_n(eanv_results, survey, n=n)
