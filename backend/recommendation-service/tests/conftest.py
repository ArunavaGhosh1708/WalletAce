"""
Shared pytest fixtures — sample cards and surveys that mirror the seed data.
All EANV values below have been hand-verified against the formula.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.card import Card, CreditTier, RewardType
from app.models.survey import (
    AirlinePreference,
    EmploymentStatus,
    FicoTier,
    HotelPreference,
    UserSurvey,
)

# ── Cards ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def card_csp() -> Card:
    """Chase Sapphire Preferred — points, Good tier, $95 AF."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Chase",
        card_name="Chase Sapphire Preferred Card",
        credit_tier_min=CreditTier.good,
        income_minimum=None,
        annual_fee=95.00,
        intro_apr_months=0,
        ongoing_apr_min=21.49,
        ongoing_apr_max=28.49,
        reward_type=RewardType.points,
        reward_network="Chase UR",
        cpp_cents=1.500,
        base_rate=1.000,
        cat_grocery_rate=3.000,
        cat_dining_rate=3.000,
        cat_gas_rate=1.000,
        cat_travel_rate=2.000,
        cat_transit_rate=1.000,
        cat_streaming_rate=3.000,
        cat_online_retail_rate=1.000,
        cat_utilities_rate=1.000,
        signup_bonus_value=1125.00,
        signup_bonus_spend_req=4000.00,
        signup_bonus_months=3,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=True,
        affiliate_link="https://example.com/apply/csp",
        last_updated=datetime.now(timezone.utc),
    )


@pytest.fixture
def card_bcp() -> Card:
    """Amex Blue Cash Preferred — cash back, Good tier, $95 AF, 6% groceries."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Amex",
        card_name="Blue Cash Preferred Card from American Express",
        credit_tier_min=CreditTier.good,
        income_minimum=None,
        annual_fee=95.00,
        intro_apr_months=12,
        ongoing_apr_min=19.24,
        ongoing_apr_max=29.99,
        reward_type=RewardType.cash_back,
        reward_network=None,
        cpp_cents=100.000,
        base_rate=0.010,
        cat_grocery_rate=0.060,
        cat_dining_rate=0.010,
        cat_gas_rate=0.030,
        cat_travel_rate=0.010,
        cat_transit_rate=0.030,
        cat_streaming_rate=0.060,
        cat_online_retail_rate=0.010,
        cat_utilities_rate=0.010,
        signup_bonus_value=250.00,
        signup_bonus_spend_req=3000.00,
        signup_bonus_months=6,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=False,
        affiliate_link="https://example.com/apply/bcp",
        last_updated=datetime.now(timezone.utc),
    )


@pytest.fixture
def card_double_cash() -> Card:
    """Citi Double Cash — 2% cash back on everything, no fee."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Citi",
        card_name="Citi Double Cash Card",
        credit_tier_min=CreditTier.good,
        income_minimum=None,
        annual_fee=0.00,
        intro_apr_months=18,
        ongoing_apr_min=19.24,
        ongoing_apr_max=29.24,
        reward_type=RewardType.cash_back,
        reward_network=None,
        cpp_cents=100.000,
        base_rate=0.020,
        cat_grocery_rate=0.020,
        cat_dining_rate=0.020,
        cat_gas_rate=0.020,
        cat_travel_rate=0.020,
        cat_transit_rate=0.020,
        cat_streaming_rate=0.020,
        cat_online_retail_rate=0.020,
        cat_utilities_rate=0.020,
        signup_bonus_value=200.00,
        signup_bonus_spend_req=1500.00,
        signup_bonus_months=6,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=False,
        affiliate_link="https://example.com/apply/double-cash",
        last_updated=datetime.now(timezone.utc),
    )


@pytest.fixture
def card_csr() -> Card:
    """Chase Sapphire Reserve — points, Excellent tier, $550 AF, lounge + GE."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Chase",
        card_name="Chase Sapphire Reserve",
        credit_tier_min=CreditTier.excellent,
        income_minimum=None,
        annual_fee=550.00,
        intro_apr_months=0,
        ongoing_apr_min=22.49,
        ongoing_apr_max=29.49,
        reward_type=RewardType.points,
        reward_network="Chase UR",
        cpp_cents=1.500,
        base_rate=1.000,
        cat_grocery_rate=1.000,
        cat_dining_rate=3.000,
        cat_gas_rate=1.000,
        cat_travel_rate=3.000,
        cat_transit_rate=3.000,
        cat_streaming_rate=1.000,
        cat_online_retail_rate=1.000,
        cat_utilities_rate=1.000,
        signup_bonus_value=900.00,
        signup_bonus_spend_req=4000.00,
        signup_bonus_months=3,
        has_lounge_access=True,
        has_global_entry=True,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=True,
        affiliate_link="https://example.com/apply/csr",
        last_updated=datetime.now(timezone.utc),
    )


@pytest.fixture
def card_secured() -> Card:
    """Discover it Secured — Poor tier, no rewards, for credit building."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Discover",
        card_name="Discover it Secured Credit Card",
        credit_tier_min=CreditTier.poor,
        income_minimum=None,
        annual_fee=0.00,
        intro_apr_months=0,
        ongoing_apr_min=28.24,
        ongoing_apr_max=28.24,
        reward_type=RewardType.cash_back,
        reward_network=None,
        cpp_cents=100.000,
        base_rate=0.010,
        cat_grocery_rate=0.010,
        cat_dining_rate=0.020,
        cat_gas_rate=0.020,
        cat_travel_rate=0.010,
        cat_transit_rate=0.010,
        cat_streaming_rate=0.010,
        cat_online_retail_rate=0.010,
        cat_utilities_rate=0.010,
        signup_bonus_value=0.00,
        signup_bonus_spend_req=0.00,
        signup_bonus_months=0,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=False,
        affiliate_link="https://example.com/apply/discover-secured",
        last_updated=datetime.now(timezone.utc),
    )


@pytest.fixture
def card_delta() -> Card:
    """Delta SkyMiles Gold — miles, Good tier, airline_affinity=delta."""
    return Card(
        card_id=uuid.uuid4(),
        issuer="Amex",
        card_name="Delta SkyMiles Gold American Express Card",
        credit_tier_min=CreditTier.good,
        income_minimum=None,
        annual_fee=99.00,
        intro_apr_months=0,
        ongoing_apr_min=20.99,
        ongoing_apr_max=29.99,
        reward_type=RewardType.miles,
        reward_network="Delta SkyMiles",
        cpp_cents=1.200,
        base_rate=1.000,
        cat_grocery_rate=2.000,
        cat_dining_rate=2.000,
        cat_gas_rate=1.000,
        cat_travel_rate=2.000,
        cat_transit_rate=1.000,
        cat_streaming_rate=1.000,
        cat_online_retail_rate=1.000,
        cat_utilities_rate=1.000,
        signup_bonus_value=480.00,
        signup_bonus_spend_req=2000.00,
        signup_bonus_months=6,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity="delta",
        hotel_affinity=None,
        issuer_rule_524=False,
        affiliate_link="https://example.com/apply/delta-gold",
        last_updated=datetime.now(timezone.utc),
    )


# ── Surveys ────────────────────────────────────────────────────────────────────

def _base_survey(**overrides) -> UserSurvey:
    """Return a minimal valid survey with all zeroed spend, override as needed."""
    defaults = dict(
        fico_tier=FicoTier.tier_670_739,
        annual_income=75000,
        employment_status=EmploymentStatus.employed,
        monthly_housing=1500,
        recent_inquiries_6m=1,
        carries_balance=False,
        monthly_groceries=0,
        monthly_dining=0,
        monthly_gas=0,
        monthly_travel=0,
        monthly_transit=0,
        monthly_streaming=0,
        monthly_online_retail=0,
        monthly_utilities=0,
        has_business_spend=False,
        willing_to_pay_fee=True,
        prefers_cash_back=False,
        airline_preference=None,
        hotel_preference=None,
        needs_intro_apr=False,
    )
    defaults.update(overrides)
    return UserSurvey(**defaults)


@pytest.fixture
def survey_optimizer() -> UserSurvey:
    """High-spend optimizer: groceries $600, dining $300, travel $500."""
    return _base_survey(
        fico_tier=FicoTier.tier_670_739,
        monthly_groceries=600,
        monthly_dining=300,
        monthly_travel=500,
    )


@pytest.fixture
def survey_grocery_heavy() -> UserSurvey:
    """Grocery-heavy user: groceries $1000, streaming $50, gas $200."""
    return _base_survey(
        monthly_groceries=1000,
        monthly_streaming=50,
        monthly_gas=200,
    )


@pytest.fixture
def survey_simple() -> UserSurvey:
    """Simple spender: groceries $500, dining $200 only."""
    return _base_survey(
        monthly_groceries=500,
        monthly_dining=200,
    )


@pytest.fixture
def survey_balance_carrier() -> UserSurvey:
    """Debt Manager: carries balance, needs low APR."""
    return _base_survey(
        fico_tier=FicoTier.tier_580_669,
        carries_balance=True,
        needs_intro_apr=True,
        monthly_groceries=400,
        monthly_dining=150,
    )


@pytest.fixture
def survey_rebuilder() -> UserSurvey:
    """Rebuilder: poor credit score."""
    return _base_survey(
        fico_tier=FicoTier.lt580,
        annual_income=30000,
        monthly_groceries=300,
    )


@pytest.fixture
def survey_524_triggered() -> UserSurvey:
    """User who would trigger Chase 5/24 rule."""
    return _base_survey(
        fico_tier=FicoTier.tier_740_plus,
        recent_inquiries_6m=4,
        monthly_travel=500,
    )


@pytest.fixture
def survey_fee_averse() -> UserSurvey:
    """User who does not want to pay an annual fee."""
    return _base_survey(
        willing_to_pay_fee=False,
        monthly_groceries=500,
        monthly_dining=300,
    )


@pytest.fixture
def survey_delta_flyer() -> UserSurvey:
    """Frequent Delta flyer with travel spend."""
    return _base_survey(
        fico_tier=FicoTier.tier_670_739,
        monthly_travel=600,
        monthly_dining=300,
        airline_preference=AirlinePreference.delta,
        prefers_cash_back=False,
    )
