import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RewardType(str, enum.Enum):
    cash_back = "cash_back"
    points = "points"
    miles = "miles"


class CreditTier(str, enum.Enum):
    poor = "Poor"
    fair = "Fair"
    good = "Good"
    excellent = "Excellent"


class Card(Base):
    __tablename__ = "cards"

    # Identity
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    issuer: Mapped[str] = mapped_column(String(60), nullable=False)
    card_name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Eligibility
    credit_tier_min: Mapped[CreditTier] = mapped_column(
        Enum(CreditTier, name="credit_tier_enum"), nullable=False
    )
    income_minimum: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Fees & APR
    annual_fee: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    intro_apr_months: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    ongoing_apr_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    ongoing_apr_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    # Reward structure
    reward_type: Mapped[RewardType] = mapped_column(
        Enum(RewardType, name="reward_type_enum"), nullable=False
    )
    reward_network: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cpp_cents: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    base_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)

    # Category reward multipliers
    cat_grocery_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_dining_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_gas_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_travel_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_transit_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_streaming_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_online_retail_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    cat_utilities_rate: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False, default=0)

    # Sign-up bonus
    signup_bonus_value: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    signup_bonus_spend_req: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    signup_bonus_months: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    # Perks
    has_lounge_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_global_entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Affinity
    airline_affinity: Mapped[str | None] = mapped_column(String(40), nullable=True)
    hotel_affinity: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Issuer rules
    issuer_rule_524: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Monetisation
    affiliate_link: Mapped[str] = mapped_column(Text, nullable=False)

    # Sync metadata
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Card {self.issuer} — {self.card_name}>"
