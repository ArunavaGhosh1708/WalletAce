"""
Phase 3 — Ranking Engine

Re-orders the EANV-sorted list based on user preferences.
Does NOT change the displayed EANV values — adjustments are applied to a
separate ranking_score used only for sort order.

Rules applied in priority order:
  1. Balance-carry APR penalty  — APR-first sort if carries_balance=true
  2. Travel perk boost          — +$150 ranking bonus for lounge/GE cards
  3. Reward type preference     — boost cash_back or points/miles cards
  4. Airline affinity boost     — boost matching co-branded airline cards
  5. Hotel affinity boost       — boost matching co-branded hotel cards
  6. Annual fee reluctance      — push fee cards below no-fee cards
"""

from dataclasses import dataclass

from app.engine.eanv import EANVResult
from app.models.card import RewardType
from app.models.survey import UserSurvey

# Ranking-only adjustment constants (dollar amounts added to ranking_score)
_TRAVEL_PERK_BOOST = 150.0
_REWARD_TYPE_BOOST = 100.0
_AFFINITY_BOOST = 120.0
_FEE_RELUCTANCE_PENALTY = 10_000.0  # large enough to always push fee cards below no-fee


@dataclass
class RankedCard:
    result: EANVResult      # Original EANV result — values unchanged
    ranking_score: float    # Adjusted score used only for ordering
    why_this_card: str      # Human-readable explanation of top match reason


def _build_why(result: EANVResult, survey: UserSurvey) -> str:
    """Generate a concise explanation for why this card was recommended."""
    card = result.card

    # Balance carriers: lead with APR
    if survey.carries_balance:
        return (
            f"Because you carry a balance, this card's {card.ongoing_apr_min:.2f}% APR "
            f"minimises your interest costs."
        )

    # Find the category that earned the most dollars
    bd = result.breakdown
    category_values = {
        "groceries": (bd.groceries, survey.monthly_groceries),
        "dining": (bd.dining, survey.monthly_dining),
        "gas": (bd.gas, survey.monthly_gas),
        "travel": (bd.travel, survey.monthly_travel),
        "transit": (bd.transit, survey.monthly_transit),
        "streaming": (bd.streaming, survey.monthly_streaming),
        "online retail": (bd.online_retail, survey.monthly_online_retail),
        "utilities": (bd.utilities, survey.monthly_utilities),
    }

    top_category, (top_earned, top_spend) = max(
        category_values.items(), key=lambda kv: kv[1][0]
    )

    if top_earned > 0 and top_spend > 0:
        return (
            f"Because you spend ${top_spend}/mo on {top_category}, "
            f"earning ${top_earned:.0f}/yr with this card."
        )

    # Fallback: sign-up bonus
    if result.signup_bonus_applied > 0:
        return (
            f"Strong ${result.signup_bonus_applied:.0f} sign-up bonus with "
            f"a ${card.signup_bonus_spend_req:.0f} spend requirement."
        )

    # Last resort
    return f"Best overall net value for your spending profile (${result.eanv:.0f}/yr)."


def rank(results: list[EANVResult], survey: UserSurvey) -> list[RankedCard]:
    """
    Apply preference weights and return a fully ranked list of RankedCard.

    Args:
        results: EANV results sorted descending by EANV (output of Phase 2).
        survey:  Validated UserSurvey.

    Returns:
        List of RankedCard sorted by ranking_score descending.
    """
    ranked: list[RankedCard] = []

    for result in results:
        card = result.card
        score = result.eanv  # Base score = EANV

        # ── Rule 1: Balance-carry APR penalty ──────────────────────────────
        # Handled by changing the sort key entirely (see sort below).
        # Score untouched here; APR sort is applied after all boosts.

        # ── Rule 2: Travel perk boost ───────────────────────────────────────
        if survey.monthly_travel >= 500:
            if card.has_lounge_access or card.has_global_entry:
                score += _TRAVEL_PERK_BOOST

        # ── Rule 3: Reward type preference ─────────────────────────────────
        if survey.prefers_cash_back and card.reward_type == RewardType.cash_back:
            score += _REWARD_TYPE_BOOST
        elif not survey.prefers_cash_back and card.reward_type in (
            RewardType.points,
            RewardType.miles,
        ):
            score += _REWARD_TYPE_BOOST

        # ── Rule 4: Airline affinity boost ─────────────────────────────────
        if (
            survey.airline_preference is not None
            and card.airline_affinity == survey.airline_preference.value
        ):
            score += _AFFINITY_BOOST

        # ── Rule 5: Hotel affinity boost ───────────────────────────────────
        if (
            survey.hotel_preference is not None
            and card.hotel_affinity == survey.hotel_preference.value
        ):
            score += _AFFINITY_BOOST

        # ── Rule 6: Annual fee reluctance ──────────────────────────────────
        if not survey.willing_to_pay_fee and card.annual_fee > 0:
            score -= _FEE_RELUCTANCE_PENALTY

        ranked.append(
            RankedCard(
                result=result,
                ranking_score=score,
                why_this_card=_build_why(result, survey),
            )
        )

    # ── Rule 1 (continued): Balance-carry APR sort ─────────────────────────
    # If the user carries a balance, sort by APR ascending as the primary key,
    # using ranking_score only as tiebreaker.
    if survey.carries_balance:
        ranked.sort(
            key=lambda rc: (
                float(rc.result.card.ongoing_apr_min),
                -rc.ranking_score,
            )
        )
    else:
        ranked.sort(key=lambda rc: rc.ranking_score, reverse=True)

    return ranked


def top_n(results: list[EANVResult], survey: UserSurvey, n: int = 2) -> list[RankedCard]:
    """Convenience wrapper — rank and return only the top n cards."""
    return rank(results, survey)[:n]
