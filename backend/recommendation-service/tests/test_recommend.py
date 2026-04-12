"""
Milestone 5 — End-to-end integration test for POST /api/v1/recommend.

Uses FastAPI dependency overrides to inject:
  - A fixed card catalogue (no real cards-service call)
  - A no-op Redis client (no real Upstash connection)

All three engine phases run for real — this test verifies the full pipeline.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.cache.redis_client import RedisClient
from app.main import app
from app.models.card import Card, CreditTier, RewardType
from app.models.survey import EmploymentStatus, FicoTier
from app.routers.recommend import get_cards, get_redis


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_card(**overrides) -> Card:
    """Return a minimal valid card, overriding specific fields as needed."""
    defaults = dict(
        card_id=uuid.uuid4(),
        issuer="Chase",
        card_name="Test Card",
        credit_tier_min=CreditTier.good,
        income_minimum=None,
        annual_fee=0.00,
        intro_apr_months=0,
        ongoing_apr_min=20.00,
        ongoing_apr_max=28.00,
        reward_type=RewardType.cash_back,
        reward_network=None,
        cpp_cents=100.000,
        base_rate=0.015,
        cat_grocery_rate=0.015,
        cat_dining_rate=0.015,
        cat_gas_rate=0.015,
        cat_travel_rate=0.015,
        cat_transit_rate=0.015,
        cat_streaming_rate=0.015,
        cat_online_retail_rate=0.015,
        cat_utilities_rate=0.015,
        signup_bonus_value=200.00,
        signup_bonus_spend_req=500.00,
        signup_bonus_months=3,
        has_lounge_access=False,
        has_global_entry=False,
        airline_affinity=None,
        hotel_affinity=None,
        issuer_rule_524=False,
        affiliate_link="https://example.com/apply/test",
        last_updated=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Card(**defaults)


GOOD_CARD = _make_card(
    card_name="Good Card",
    credit_tier_min=CreditTier.good,
    annual_fee=0.00,
    cat_grocery_rate=0.03,
    cat_dining_rate=0.03,
    signup_bonus_value=200.00,
)

EXCELLENT_ONLY_CARD = _make_card(
    card_name="Excellent Only Card",
    credit_tier_min=CreditTier.excellent,
    annual_fee=550.00,
    signup_bonus_value=900.00,
)

INTRO_APR_CARD = _make_card(
    card_name="Balance Transfer Card",
    credit_tier_min=CreditTier.fair,
    intro_apr_months=18,
    ongoing_apr_min=17.99,
    ongoing_apr_max=27.99,
    signup_bonus_value=0.00,
)

ALL_CARDS = [GOOD_CARD, EXCELLENT_ONLY_CARD, INTRO_APR_CARD]


def _make_survey(**overrides) -> dict:
    """Return a minimal valid survey payload as a dict."""
    defaults = dict(
        fico_tier="670_739",
        annual_income=75000,
        employment_status="employed",
        monthly_housing=1500,
        recent_inquiries_6m=1,
        carries_balance=False,
        monthly_groceries=500,
        monthly_dining=300,
        monthly_gas=100,
        monthly_travel=0,
        monthly_transit=0,
        monthly_streaming=50,
        monthly_online_retail=100,
        monthly_utilities=150,
        has_business_spend=False,
        willing_to_pay_fee=True,
        prefers_cash_back=True,
        airline_preference=None,
        hotel_preference=None,
        needs_intro_apr=False,
    )
    defaults.update(overrides)
    return defaults


# No-op Redis mock
class _NoOpRedis:
    async def set_session(self, session_id: str, survey) -> None:
        pass

    async def get_session(self, session_id: str):
        return None

    async def close(self) -> None:
        pass


# ── Client setup with dependency overrides ─────────────────────────────────────

@pytest.fixture
def client():
    async def _override_cards():
        return ALL_CARDS

    def _override_redis(request=None):
        return _NoOpRedis()

    app.dependency_overrides[get_cards] = _override_cards
    app.dependency_overrides[get_redis] = _override_redis

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def client_no_eligible_cards():
    """Client where no cards match the user's eligibility."""
    async def _override_cards():
        return [EXCELLENT_ONLY_CARD]  # only Excellent-tier card

    def _override_redis(request=None):
        return _NoOpRedis()

    app.dependency_overrides[get_cards] = _override_cards
    app.dependency_overrides[get_redis] = _override_redis

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Happy path tests ───────────────────────────────────────────────────────────

class TestRecommendHappyPath:
    def test_returns_200(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        assert response.status_code == 200

    def test_returns_top_cards(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        data = response.json()
        assert "top_cards" in data
        assert len(data["top_cards"]) >= 1
        assert len(data["top_cards"]) <= 2

    def test_response_has_session_id(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        data = response.json()
        assert "session_id" in data
        # Should be a valid UUID
        uuid.UUID(data["session_id"])

    def test_response_has_cards_evaluated(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        data = response.json()
        assert "cards_evaluated" in data
        assert data["cards_evaluated"] > 0

    def test_card_result_has_required_fields(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        card = response.json()["top_cards"][0]
        for field in ("card_id", "card_name", "issuer", "eanv", "why_this_card",
                      "affiliate_link", "category_breakdown", "annual_fee"):
            assert field in card, f"Missing field: {field}"

    def test_category_breakdown_present(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        bd = response.json()["top_cards"][0]["category_breakdown"]
        for cat in ("groceries", "dining", "gas", "travel", "transit",
                    "streaming", "online_retail", "utilities"):
            assert cat in bd


class TestYearParameter:
    def test_year1_default(self, client):
        response = client.post("/api/v1/recommend", json=_make_survey())
        assert response.json()["year"] == 1

    def test_year2_excludes_signup_bonus(self, client):
        r1 = client.post("/api/v1/recommend?year=1", json=_make_survey())
        r2 = client.post("/api/v1/recommend?year=2", json=_make_survey())
        eanv1 = r1.json()["top_cards"][0]["eanv"]
        eanv2 = r2.json()["top_cards"][0]["eanv"]
        # Year 1 should be >= Year 2 (sign-up bonus adds value)
        assert eanv1 >= eanv2

    def test_invalid_year_returns_422(self, client):
        response = client.post("/api/v1/recommend?year=3", json=_make_survey())
        assert response.status_code == 422


class TestEligibilityIntegration:
    def test_good_tier_user_does_not_see_excellent_only_card(self, client):
        """GOOD_CARD and INTRO_APR_CARD are visible; EXCELLENT_ONLY_CARD is not."""
        response = client.post("/api/v1/recommend", json=_make_survey(fico_tier="670_739"))
        card_names = [c["card_name"] for c in response.json()["top_cards"]]
        assert "Excellent Only Card" not in card_names

    def test_needs_intro_apr_only_shows_intro_apr_cards(self, client):
        response = client.post(
            "/api/v1/recommend",
            json=_make_survey(needs_intro_apr=True, fico_tier="580_669"),
        )
        data = response.json()
        for card in data["top_cards"]:
            assert card["intro_apr_months"] > 0

    def test_no_eligible_cards_returns_422(self, client_no_eligible_cards):
        # Good-tier user against only an Excellent-required card
        response = client_no_eligible_cards.post(
            "/api/v1/recommend", json=_make_survey(fico_tier="670_739")
        )
        assert response.status_code == 422


class TestInputValidation:
    def test_missing_required_field_returns_422(self, client):
        survey = _make_survey()
        del survey["fico_tier"]
        response = client.post("/api/v1/recommend", json=survey)
        assert response.status_code == 422

    def test_out_of_range_spend_returns_422(self, client):
        # monthly_groceries max is 2000
        response = client.post(
            "/api/v1/recommend",
            json=_make_survey(monthly_groceries=9999),
        )
        assert response.status_code == 422

    def test_invalid_fico_tier_returns_422(self, client):
        response = client.post(
            "/api/v1/recommend",
            json=_make_survey(fico_tier="not_a_tier"),
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/api/v1/recommend", json={})
        assert response.status_code == 422
