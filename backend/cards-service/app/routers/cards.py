from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import app.database as db

router = APIRouter(prefix="/api/v1", tags=["cards"])


class CardSchema(BaseModel):
    card_id: UUID
    issuer: str
    card_name: str
    credit_tier_min: str
    income_minimum: int | None
    annual_fee: float
    intro_apr_months: int
    ongoing_apr_min: float
    ongoing_apr_max: float
    reward_type: str
    reward_network: str | None
    cpp_cents: float
    base_rate: float
    cat_grocery_rate: float
    cat_dining_rate: float
    cat_gas_rate: float
    cat_travel_rate: float
    cat_transit_rate: float
    cat_streaming_rate: float
    cat_online_retail_rate: float
    cat_utilities_rate: float
    signup_bonus_value: float
    signup_bonus_spend_req: float
    signup_bonus_months: int
    has_lounge_access: bool
    has_global_entry: bool
    airline_affinity: str | None
    hotel_affinity: str | None
    issuer_rule_524: bool
    affiliate_link: str
    last_updated: datetime

    model_config = {"from_attributes": True}


@router.get("/cards", response_model=list[CardSchema])
async def list_cards(conn=Depends(db.get_db)):
    rows = await conn.fetch("SELECT * FROM cards ORDER BY card_name")
    return [dict(row) for row in rows]
