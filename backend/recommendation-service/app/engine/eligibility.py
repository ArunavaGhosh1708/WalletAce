"""
Phase 1 — Eligibility Filter

Removes cards the user cannot realistically obtain.
All filters are pure functions; no I/O.

Filter order (matches architecture spec):
  1. FICO tier mapping
  2. Chase 5/24 rule
  3. Amex once-in-a-lifetime (zeroes SUB, does not filter)
  4. Income minimums
  5. Intro APR override
"""

from app.models.card import Card, CreditTier
from app.models.survey import FicoTier, UserSurvey

# Numeric rank for tier comparison (higher = better credit)
_FICO_RANK: dict[FicoTier, int] = {
    FicoTier.lt580: 1,
    FicoTier.tier_580_669: 2,
    FicoTier.tier_670_739: 3,
    FicoTier.tier_740_799: 4,   # Very Good — qualifies for Excellent-tier cards
    FicoTier.tier_800_850: 5,   # Exceptional — same eligibility, higher sort priority
}

_CARD_TIER_RANK: dict[CreditTier, int] = {
    CreditTier.poor: 1,
    CreditTier.fair: 2,
    CreditTier.good: 3,
    CreditTier.excellent: 4,   # FICO rank 4 (Very Good) and 5 (Exceptional) both meet this
}


def _passes_fico(card: Card, survey: UserSurvey) -> bool:
    """Card passes if the user's FICO tier meets the card's minimum requirement."""
    return _FICO_RANK[survey.fico_tier] >= _CARD_TIER_RANK[card.credit_tier_min]


def _passes_524(card: Card, survey: UserSurvey) -> bool:
    """
    Chase 5/24 rule: Chase cards flagged issuer_rule_524=true are blocked
    if the user has 3+ recent inquiries in 6 months (proxy for 5+ new accounts
    in 24 months).
    """
    if card.issuer_rule_524 and survey.recent_inquiries_6m >= 3:
        return False
    return True


def _passes_income(card: Card, survey: UserSurvey) -> bool:
    """Card is filtered if it has an income_minimum that the user does not meet."""
    if card.income_minimum is not None and survey.annual_income < card.income_minimum:
        return False
    return True


def _passes_max_fee(card: Card, survey: UserSurvey) -> bool:
    """
    If user is willing to pay a fee but specified a maximum, filter out cards above that ceiling.
    When willing_to_pay_fee=False, no eligibility filter is applied here — the ranking engine
    applies a large penalty so no-fee cards rank first, but fee cards remain available for
    rank 2 (per the 'second card can use other preferences' rule).
    """
    if survey.willing_to_pay_fee and survey.max_annual_fee > 0:
        return float(card.annual_fee) <= survey.max_annual_fee
    return True


def _passes_intro_apr(card: Card, survey: UserSurvey) -> bool:
    """
    If the user's primary goal is a 0% intro APR / balance transfer,
    only cards with intro_apr_months > 0 are passed through.
    """
    if survey.needs_intro_apr and card.intro_apr_months == 0:
        return False
    return True


def apply_amex_sub_rule(card: Card, survey: UserSurvey) -> Card:
    """
    Amex once-in-a-lifetime rule: if the user previously held the same Amex
    product their sign-up bonus is zeroed.

    The UserSurvey does not yet capture previously-held cards, so this is
    implemented as a no-op stub ready for when that field is added.
    """
    return card


def filter_eligible(cards: list[Card], survey: UserSurvey) -> list[Card]:
    """
    Run all Phase 1 filters and return only cards the user can realistically obtain.

    Args:
        cards:  Full card catalogue fetched from cards-service.
        survey: Validated UserSurvey submitted by the user.

    Returns:
        Subset of cards that pass every eligibility check.
    """
    eligible: list[Card] = []

    for card in cards:
        if not _passes_fico(card, survey):
            continue
        if not _passes_524(card, survey):
            continue
        if not _passes_income(card, survey):
            continue
        if not _passes_max_fee(card, survey):
            continue
        if not _passes_intro_apr(card, survey):
            continue

        # Apply non-filtering mutations (e.g. Amex SUB zeroing)
        card = apply_amex_sub_rule(card, survey)

        eligible.append(card)

    return eligible
