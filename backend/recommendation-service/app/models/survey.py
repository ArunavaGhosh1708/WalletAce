from enum import Enum

from pydantic import BaseModel, Field, model_validator


class FicoTier(str, Enum):
    lt580 = "lt580"
    tier_580_669 = "580_669"
    tier_670_739 = "670_739"
    tier_740_799 = "740_799"
    tier_800_850 = "800_850"


class EmploymentStatus(str, Enum):
    employed = "employed"
    self_employed = "self_employed"
    student = "student"
    unemployed = "unemployed"


class AirlinePreference(str, Enum):
    delta = "delta"
    united = "united"
    aa = "aa"
    southwest = "southwest"
    alaska = "alaska"
    jetblue = "jetblue"


class HotelPreference(str, Enum):
    marriott = "marriott"
    hilton = "hilton"
    hyatt = "hyatt"
    ihg = "ihg"


class UserSurvey(BaseModel):
    # --- Intro ---
    user_name: str | None = Field(default=None, description="User's name")

    # --- Group 1: Eligibility & Financial Health ---

    fico_tier: FicoTier = Field(
        ...,
        description="Self-reported FICO score range",
    )
    annual_income: int = Field(
        ...,
        ge=0,
        description="Pre-tax household income in USD",
    )
    employment_status: EmploymentStatus = Field(
        ...,
        description="Current employment situation",
    )
    monthly_housing: int = Field(
        ...,
        ge=0,
        le=10000,
        description="Monthly rent or mortgage payment in USD",
    )
    recent_inquiries_6m: int = Field(
        ...,
        ge=0,
        le=10,
        description="Number of credit card applications in the last 6 months",
    )
    carries_balance: bool = Field(
        ...,
        description="True if the user carries a month-to-month balance",
    )

    # --- Group 2: Monthly Spending Habits ---

    monthly_groceries: int = Field(
        ...,
        ge=0,
        le=2000,
        description="Average monthly supermarket spend in USD",
    )
    monthly_dining: int = Field(
        ...,
        ge=0,
        le=3000,
        description="Average monthly restaurant / takeout spend in USD",
    )
    monthly_gas: int = Field(
        ...,
        ge=0,
        le=1000,
        description="Average monthly gas or EV charging spend in USD",
    )
    monthly_travel: int = Field(
        ...,
        ge=0,
        le=5000,
        description="Average monthly flights + hotels spend in USD",
    )
    monthly_transit: int = Field(
        ...,
        ge=0,
        le=1000,
        description="Average monthly rideshare / tolls / transit spend in USD",
    )
    monthly_streaming: int = Field(
        ...,
        ge=0,
        le=500,
        description="Average monthly digital subscriptions spend in USD",
    )
    monthly_online_retail: int = Field(
        ...,
        ge=0,
        le=2000,
        description="Average monthly Amazon / marketplace spend in USD",
    )
    monthly_utilities: int = Field(
        ...,
        ge=0,
        le=1000,
        description="Average monthly phone + internet + electricity spend in USD",
    )

    # --- Group 3: Lifestyle & Preferences ---

    has_business_spend: bool = Field(
        ...,
        description="True if the user has business-related card expenses",
    )
    willing_to_pay_fee: bool = Field(
        ...,
        description="True if user is open to cards with an annual fee",
    )
    max_annual_fee: int = Field(
        default=0,
        ge=0,
        le=1000,
        description="Maximum annual fee the user will pay (0 = no limit, only used when willing_to_pay_fee=True)",
    )
    prefers_cash_back: bool = Field(
        ...,
        description="True = cash back preference; False = points / miles preference",
    )
    airline_preference: AirlinePreference | None = Field(
        default=None,
        description="Preferred airline slug, or null if none",
    )
    hotel_preference: HotelPreference | None = Field(
        default=None,
        description="Preferred hotel chain slug, or null if none",
    )
    needs_intro_apr: bool = Field(
        ...,
        description="True if primary goal is a 0% intro APR / balance transfer card",
    )

    @model_validator(mode="after")
    def balance_implies_intro_apr_awareness(self) -> "UserSurvey":
        """
        If the user carries a balance but hasn't flagged needs_intro_apr,
        that's fine — they may just want the lowest ongoing APR.
        But if they need intro APR they should also be carrying a balance
        or explicitly want a balance transfer. No hard block; just a logical note.
        """
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "fico_tier": "670_739",
                "annual_income": 75000,
                "employment_status": "employed",
                "monthly_housing": 1500,
                "recent_inquiries_6m": 1,
                "carries_balance": False,
                "monthly_groceries": 600,
                "monthly_dining": 300,
                "monthly_gas": 150,
                "monthly_travel": 500,
                "monthly_transit": 100,
                "monthly_streaming": 50,
                "monthly_online_retail": 200,
                "monthly_utilities": 200,
                "has_business_spend": False,
                "willing_to_pay_fee": True,
                "prefers_cash_back": False,
                "airline_preference": "delta",
                "hotel_preference": None,
                "needs_intro_apr": False,
            }
        }
    }
