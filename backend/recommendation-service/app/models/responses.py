from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBreakdown(BaseModel):
    """Dollar value earned per spending category for a given card."""

    groceries: float = 0.0
    dining: float = 0.0
    gas: float = 0.0
    travel: float = 0.0
    transit: float = 0.0
    streaming: float = 0.0
    online_retail: float = 0.0
    utilities: float = 0.0
    base: float = 0.0


class CardResult(BaseModel):
    """A single recommended card with full EANV breakdown."""

    card_id: UUID
    issuer: str
    card_name: str
    annual_fee: float
    reward_type: str
    reward_network: str | None
    affiliate_link: str

    # EANV components
    eanv: float = Field(description="Expected Annual Net Value in USD")
    rewards_total: float = Field(description="Total rewards before annual fee deduction")
    signup_bonus_value: float = Field(description="Sign-up bonus value included (0 if Year 2+)")
    category_breakdown: CategoryBreakdown

    # Ranking metadata
    why_this_card: str = Field(description="Human-readable explanation of the top match reason")

    # Perks surfaced on the card
    has_lounge_access: bool
    has_global_entry: bool
    intro_apr_months: int
    ongoing_apr_min: float
    ongoing_apr_max: float


class RecommendationResponse(BaseModel):
    """Response returned by POST /recommend — always top 2 cards."""

    session_id: str = Field(description="UUID of this recommendation session")
    year: int = Field(description="1 = includes sign-up bonus, 2 = excludes it")
    top_cards: list[CardResult] = Field(
        min_length=1,
        max_length=2,
        description="Ranked list of top 1–2 recommended cards",
    )
    cards_evaluated: int = Field(description="Total cards that passed Phase 1 eligibility")
