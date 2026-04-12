import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import app.database as db

router = APIRouter(prefix="/api/v1", tags=["survey-responses"])


# ── Request model ─────────────────────────────────────────────────────────────

class CategoryBreakdown(BaseModel):
    groceries: float = 0.0
    dining: float = 0.0
    gas: float = 0.0
    travel: float = 0.0
    transit: float = 0.0
    streaming: float = 0.0
    online_retail: float = 0.0
    utilities: float = 0.0


class CardRec(BaseModel):
    card_id: str
    issuer: str
    card_name: str
    annual_fee: float
    reward_type: str
    reward_network: str | None
    affiliate_link: str
    eanv: float
    rewards_total: float
    signup_bonus_value: float
    category_breakdown: CategoryBreakdown
    why_this_card: str
    has_lounge_access: bool
    has_global_entry: bool
    intro_apr_months: int
    ongoing_apr_min: float
    ongoing_apr_max: float


class SurveyInput(BaseModel):
    user_name: str | None = None
    fico_tier: str
    annual_income: int
    employment_status: str
    monthly_housing: int
    recent_inquiries_6m: int
    carries_balance: bool
    monthly_groceries: int
    monthly_dining: int
    monthly_gas: int
    monthly_travel: int
    monthly_transit: int
    monthly_streaming: int
    monthly_online_retail: int
    monthly_utilities: int
    has_business_spend: bool
    willing_to_pay_fee: bool
    max_annual_fee: int = 0
    prefers_cash_back: bool
    airline_preference: str | None = None
    hotel_preference: str | None = None
    needs_intro_apr: bool


class StoreResponseRequest(BaseModel):
    session_id: str | None = None
    survey_input: SurveyInput
    recommended_cards: list[CardRec]
    cards_evaluated: int


# ── Helper ────────────────────────────────────────────────────────────────────

def _card_params(card: CardRec | None) -> dict[str, Any]:
    if card is None:
        return {k: None for k in [
            "card_id", "issuer", "card_name", "annual_fee", "reward_type",
            "reward_network", "eanv", "rewards_total", "signup_bonus",
            "cat_groceries", "cat_dining", "cat_gas", "cat_travel",
            "cat_transit", "cat_streaming", "cat_online_retail", "cat_utilities",
            "why_this_card", "has_lounge_access", "has_global_entry",
            "intro_apr_months", "ongoing_apr_min", "ongoing_apr_max", "affiliate_link",
        ]}
    bd = card.category_breakdown
    return {
        "card_id":           uuid.UUID(card.card_id),
        "issuer":            card.issuer,
        "card_name":         card.card_name,
        "annual_fee":        card.annual_fee,
        "reward_type":       card.reward_type,
        "reward_network":    card.reward_network,
        "eanv":              card.eanv,
        "rewards_total":     card.rewards_total,
        "signup_bonus":      card.signup_bonus_value,
        "cat_groceries":     bd.groceries,
        "cat_dining":        bd.dining,
        "cat_gas":           bd.gas,
        "cat_travel":        bd.travel,
        "cat_transit":       bd.transit,
        "cat_streaming":     bd.streaming,
        "cat_online_retail": bd.online_retail,
        "cat_utilities":     bd.utilities,
        "why_this_card":     card.why_this_card,
        "has_lounge_access": card.has_lounge_access,
        "has_global_entry":  card.has_global_entry,
        "intro_apr_months":  card.intro_apr_months,
        "ongoing_apr_min":   card.ongoing_apr_min,
        "ongoing_apr_max":   card.ongoing_apr_max,
        "affiliate_link":    card.affiliate_link,
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/survey-responses", status_code=201, summary="Store a completed survey + recommendation")
async def store_survey_response(
    body: StoreResponseRequest,
    conn=Depends(db.get_db),
):
    s = body.survey_input
    recs = body.recommended_cards
    r1 = _card_params(recs[0] if len(recs) > 0 else None)
    r2 = _card_params(recs[1] if len(recs) > 1 else None)

    session_uuid = None
    if body.session_id:
        try:
            session_uuid = uuid.UUID(body.session_id)
        except ValueError:
            pass

    # Insert survey input → get the new request ID
    request_id = await conn.fetchval(
        """
        INSERT INTO survey_requests (
            session_id, user_name,
            fico_tier, annual_income, employment_status, monthly_housing,
            recent_inquiries_6m, carries_balance,
            monthly_groceries, monthly_dining, monthly_gas, monthly_travel,
            monthly_transit, monthly_streaming, monthly_online_retail, monthly_utilities,
            has_business_spend, willing_to_pay_fee, max_annual_fee, prefers_cash_back,
            airline_preference, hotel_preference, needs_intro_apr
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
            $21, $22, $23
        )
        RETURNING id
        """,
        session_uuid, s.user_name,
        s.fico_tier, s.annual_income, s.employment_status, s.monthly_housing,
        s.recent_inquiries_6m, s.carries_balance,
        s.monthly_groceries, s.monthly_dining, s.monthly_gas, s.monthly_travel,
        s.monthly_transit, s.monthly_streaming, s.monthly_online_retail, s.monthly_utilities,
        s.has_business_spend, s.willing_to_pay_fee, s.max_annual_fee, s.prefers_cash_back,
        s.airline_preference, s.hotel_preference, s.needs_intro_apr,
    )

    # Insert recommendation output linked to the request
    await conn.execute(
        """
        INSERT INTO survey_results (
            request_id, cards_evaluated,
            rec1_card_id, rec1_issuer, rec1_card_name, rec1_annual_fee,
            rec1_reward_type, rec1_reward_network, rec1_eanv, rec1_rewards_total,
            rec1_signup_bonus, rec1_cat_groceries, rec1_cat_dining, rec1_cat_gas,
            rec1_cat_travel, rec1_cat_transit, rec1_cat_streaming,
            rec1_cat_online_retail, rec1_cat_utilities, rec1_why_this_card,
            rec1_has_lounge_access, rec1_has_global_entry, rec1_intro_apr_months,
            rec1_ongoing_apr_min, rec1_ongoing_apr_max, rec1_affiliate_link,
            rec2_card_id, rec2_issuer, rec2_card_name, rec2_annual_fee,
            rec2_reward_type, rec2_reward_network, rec2_eanv, rec2_rewards_total,
            rec2_signup_bonus, rec2_cat_groceries, rec2_cat_dining, rec2_cat_gas,
            rec2_cat_travel, rec2_cat_transit, rec2_cat_streaming,
            rec2_cat_online_retail, rec2_cat_utilities, rec2_why_this_card,
            rec2_has_lounge_access, rec2_has_global_entry, rec2_intro_apr_months,
            rec2_ongoing_apr_min, rec2_ongoing_apr_max, rec2_affiliate_link
        ) VALUES (
            $1,  $2,  $3,  $4,  $5,  $6,  $7,  $8,  $9,  $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
            $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
            $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
            $41, $42, $43, $44, $45, $46, $47, $48, $49, $50
        )
        """,
        request_id, body.cards_evaluated,
        r1["card_id"], r1["issuer"], r1["card_name"], r1["annual_fee"],
        r1["reward_type"], r1["reward_network"], r1["eanv"], r1["rewards_total"],
        r1["signup_bonus"], r1["cat_groceries"], r1["cat_dining"], r1["cat_gas"],
        r1["cat_travel"], r1["cat_transit"], r1["cat_streaming"],
        r1["cat_online_retail"], r1["cat_utilities"], r1["why_this_card"],
        r1["has_lounge_access"], r1["has_global_entry"], r1["intro_apr_months"],
        r1["ongoing_apr_min"], r1["ongoing_apr_max"], r1["affiliate_link"],
        r2["card_id"], r2["issuer"], r2["card_name"], r2["annual_fee"],
        r2["reward_type"], r2["reward_network"], r2["eanv"], r2["rewards_total"],
        r2["signup_bonus"], r2["cat_groceries"], r2["cat_dining"], r2["cat_gas"],
        r2["cat_travel"], r2["cat_transit"], r2["cat_streaming"],
        r2["cat_online_retail"], r2["cat_utilities"], r2["why_this_card"],
        r2["has_lounge_access"], r2["has_global_entry"], r2["intro_apr_months"],
        r2["ongoing_apr_min"], r2["ongoing_apr_max"], r2["affiliate_link"],
    )

    return {"stored": True, "request_id": str(request_id)}
