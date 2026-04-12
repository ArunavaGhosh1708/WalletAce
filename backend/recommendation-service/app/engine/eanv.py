"""
Phase 2 — EANV Calculator

Computes the Expected Annual Net Value for every card that survived Phase 1.
Pure mathematical function — no preference weighting (that is Phase 3).

Formula:
    EANV = (S1×R1 + S2×R2 + ... + Sn×Rn) + SB - AF

Where:
    Si  = monthly_spend_i × 12
    Ri  = effective_rate_i × (cpp_cents / 100)
    SB  = signup_bonus_value  (Year 1) or 0 (Year 2+)
    AF  = annual_fee

Effective rate per category:
    cat_rate if cat_rate > 0 else base_rate
"""

from dataclasses import dataclass, field

from app.models.card import Card
from app.models.survey import UserSurvey


@dataclass
class CategoryBreakdown:
    """Dollar value earned per spending category for a given card."""

    groceries: float = 0.0
    dining: float = 0.0
    gas: float = 0.0
    travel: float = 0.0
    transit: float = 0.0
    streaming: float = 0.0
    online_retail: float = 0.0
    utilities: float = 0.0

    def total(self) -> float:
        return (
            self.groceries
            + self.dining
            + self.gas
            + self.travel
            + self.transit
            + self.streaming
            + self.online_retail
            + self.utilities
        )


@dataclass
class EANVResult:
    """Full EANV output for a single card against a specific user profile."""

    card: Card
    eanv: float                              # Net annual value (can be negative)
    rewards_total: float                     # Gross rewards before fee deduction
    signup_bonus_applied: float              # SB included (0 if year=2)
    annual_fee: float
    breakdown: CategoryBreakdown = field(default_factory=CategoryBreakdown)


def _category_reward(
    annual_spend: float,
    cat_rate: float,
    base_rate: float,
    cpp_cents: float,
) -> float:
    """
    Dollar reward value for a single spending category.

    Uses cat_rate if the card offers a specific rate for the category,
    otherwise falls back to base_rate.
    """
    effective_rate = cat_rate if cat_rate > 0 else base_rate
    return annual_spend * effective_rate * (cpp_cents / 100)


def calculate(card: Card, survey: UserSurvey, year: int = 1) -> EANVResult:
    """
    Compute the EANV for one card against the user's survey.

    Args:
        card:   A card that passed Phase 1 eligibility.
        survey: Validated UserSurvey.
        year:   1 = include sign-up bonus, 2 = exclude sign-up bonus.

    Returns:
        EANVResult with full breakdown.
    """
    cpp = float(card.cpp_cents)
    base = float(card.base_rate)

    breakdown = CategoryBreakdown(
        groceries=_category_reward(
            survey.monthly_groceries * 12,
            float(card.cat_grocery_rate),
            base,
            cpp,
        ),
        dining=_category_reward(
            survey.monthly_dining * 12,
            float(card.cat_dining_rate),
            base,
            cpp,
        ),
        gas=_category_reward(
            survey.monthly_gas * 12,
            float(card.cat_gas_rate),
            base,
            cpp,
        ),
        travel=_category_reward(
            survey.monthly_travel * 12,
            float(card.cat_travel_rate),
            base,
            cpp,
        ),
        transit=_category_reward(
            survey.monthly_transit * 12,
            float(card.cat_transit_rate),
            base,
            cpp,
        ),
        streaming=_category_reward(
            survey.monthly_streaming * 12,
            float(card.cat_streaming_rate),
            base,
            cpp,
        ),
        online_retail=_category_reward(
            survey.monthly_online_retail * 12,
            float(card.cat_online_retail_rate),
            base,
            cpp,
        ),
        utilities=_category_reward(
            survey.monthly_utilities * 12,
            float(card.cat_utilities_rate),
            base,
            cpp,
        ),
    )

    rewards_total = breakdown.total()
    signup_bonus = float(card.signup_bonus_value) if year == 1 else 0.0
    annual_fee = float(card.annual_fee)
    eanv = rewards_total + signup_bonus - annual_fee

    return EANVResult(
        card=card,
        eanv=round(eanv, 2),
        rewards_total=round(rewards_total, 2),
        signup_bonus_applied=round(signup_bonus, 2),
        annual_fee=annual_fee,
        breakdown=breakdown,
    )


def calculate_all(
    cards: list[Card],
    survey: UserSurvey,
    year: int = 1,
) -> list[EANVResult]:
    """
    Run calculate() for every eligible card.

    Returns results sorted by EANV descending (Phase 3 may re-order further).
    """
    results = [calculate(card, survey, year) for card in cards]
    results.sort(key=lambda r: r.eanv, reverse=True)
    return results
