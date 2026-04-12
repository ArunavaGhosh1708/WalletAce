from enum import Enum
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class RewardType(str, Enum):
    cash_back = "cash_back"
    points = "points"
    miles = "miles"


class CreditTier(str, Enum):
    poor = "Poor"
    fair = "Fair"
    good = "Good"
    excellent = "Excellent"


# Alias for backwards compatibility with field names
CreditTierMin = CreditTier


class Card(BaseModel):
    """
    Mirrors the 31-column cards table in cards-service (Neon Postgres).
    Received via GET /cards/all from the cards-service.
    """

    card_id: UUID
    issuer: str
    card_name: str
    credit_tier_min: CreditTierMin
    income_minimum: int | None = None
    annual_fee: float = Field(ge=0)
    intro_apr_months: int = Field(ge=0)
    ongoing_apr_min: float
    ongoing_apr_max: float
    reward_type: RewardType
    reward_network: str | None = None
    cpp_cents: float = Field(ge=0, description="Cents per point/mile valuation")
    base_rate: float = Field(ge=0, description="Default earn rate on non-category spend")

    # Category reward multipliers
    cat_grocery_rate: float = Field(ge=0)
    cat_dining_rate: float = Field(ge=0)
    cat_gas_rate: float = Field(ge=0)
    cat_travel_rate: float = Field(ge=0)
    cat_transit_rate: float = Field(ge=0)
    cat_streaming_rate: float = Field(ge=0)
    cat_online_retail_rate: float = Field(ge=0)
    cat_utilities_rate: float = Field(ge=0)

    # Sign-up bonus
    signup_bonus_value: float = Field(ge=0)
    signup_bonus_spend_req: float = Field(ge=0)
    signup_bonus_months: int = Field(ge=0)

    # Perks
    has_lounge_access: bool = False
    has_global_entry: bool = False

    # Affinity
    airline_affinity: str | None = None
    hotel_affinity: str | None = None

    # Issuer rules
    issuer_rule_524: bool = False

    # Monetisation
    affiliate_link: str

    last_updated: datetime
