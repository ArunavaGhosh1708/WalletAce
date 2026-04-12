-- Migration 003: Create survey_requests and survey_results tables
-- survey_requests: stores the user's survey input (flat columns, one row per submission)
-- survey_results:  stores recommendation output, FK → survey_requests

BEGIN;

-- ── Survey input ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS survey_requests (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id                  UUID,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Intro
    user_name                   VARCHAR(100),

    -- Group 1: Eligibility & Financial Health
    fico_tier                   VARCHAR(20)     NOT NULL,
    annual_income               INTEGER         NOT NULL,
    employment_status           VARCHAR(30)     NOT NULL,
    monthly_housing             INTEGER         NOT NULL,
    recent_inquiries_6m         SMALLINT        NOT NULL,
    carries_balance             BOOLEAN         NOT NULL,

    -- Group 2: Monthly Spending
    monthly_groceries           INTEGER         NOT NULL,
    monthly_dining              INTEGER         NOT NULL,
    monthly_gas                 INTEGER         NOT NULL,
    monthly_travel              INTEGER         NOT NULL,
    monthly_transit             INTEGER         NOT NULL,
    monthly_streaming           INTEGER         NOT NULL,
    monthly_online_retail       INTEGER         NOT NULL,
    monthly_utilities           INTEGER         NOT NULL,

    -- Group 3: Preferences
    has_business_spend          BOOLEAN         NOT NULL,
    willing_to_pay_fee          BOOLEAN         NOT NULL,
    max_annual_fee              INTEGER         NOT NULL DEFAULT 0,
    prefers_cash_back           BOOLEAN         NOT NULL,
    airline_preference          VARCHAR(20),
    hotel_preference            VARCHAR(20),
    needs_intro_apr             BOOLEAN         NOT NULL
);

CREATE INDEX idx_survey_requests_created_at ON survey_requests (created_at DESC);
CREATE INDEX idx_survey_requests_session    ON survey_requests (session_id);


-- ── Recommendation output ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS survey_results (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id                  UUID        NOT NULL REFERENCES survey_requests(id) ON DELETE CASCADE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),

    cards_evaluated             INTEGER,

    -- Recommendation 1 (best match)
    rec1_card_id                UUID,
    rec1_issuer                 VARCHAR(60),
    rec1_card_name              VARCHAR(120),
    rec1_annual_fee             NUMERIC(8,2),
    rec1_reward_type            VARCHAR(20),
    rec1_reward_network         VARCHAR(30),
    rec1_eanv                   NUMERIC(10,2),
    rec1_rewards_total          NUMERIC(10,2),
    rec1_signup_bonus           NUMERIC(10,2),
    rec1_cat_groceries          NUMERIC(10,2),
    rec1_cat_dining             NUMERIC(10,2),
    rec1_cat_gas                NUMERIC(10,2),
    rec1_cat_travel             NUMERIC(10,2),
    rec1_cat_transit            NUMERIC(10,2),
    rec1_cat_streaming          NUMERIC(10,2),
    rec1_cat_online_retail      NUMERIC(10,2),
    rec1_cat_utilities          NUMERIC(10,2),
    rec1_why_this_card          TEXT,
    rec1_has_lounge_access      BOOLEAN,
    rec1_has_global_entry       BOOLEAN,
    rec1_intro_apr_months       SMALLINT,
    rec1_ongoing_apr_min        NUMERIC(5,2),
    rec1_ongoing_apr_max        NUMERIC(5,2),
    rec1_affiliate_link         TEXT,

    -- Recommendation 2 (second pick)
    rec2_card_id                UUID,
    rec2_issuer                 VARCHAR(60),
    rec2_card_name              VARCHAR(120),
    rec2_annual_fee             NUMERIC(8,2),
    rec2_reward_type            VARCHAR(20),
    rec2_reward_network         VARCHAR(30),
    rec2_eanv                   NUMERIC(10,2),
    rec2_rewards_total          NUMERIC(10,2),
    rec2_signup_bonus           NUMERIC(10,2),
    rec2_cat_groceries          NUMERIC(10,2),
    rec2_cat_dining             NUMERIC(10,2),
    rec2_cat_gas                NUMERIC(10,2),
    rec2_cat_travel             NUMERIC(10,2),
    rec2_cat_transit            NUMERIC(10,2),
    rec2_cat_streaming          NUMERIC(10,2),
    rec2_cat_online_retail      NUMERIC(10,2),
    rec2_cat_utilities          NUMERIC(10,2),
    rec2_why_this_card          TEXT,
    rec2_has_lounge_access      BOOLEAN,
    rec2_has_global_entry       BOOLEAN,
    rec2_intro_apr_months       SMALLINT,
    rec2_ongoing_apr_min        NUMERIC(5,2),
    rec2_ongoing_apr_max        NUMERIC(5,2),
    rec2_affiliate_link         TEXT
);

CREATE INDEX idx_survey_results_request_id ON survey_results (request_id);
CREATE INDEX idx_survey_results_created_at ON survey_results (created_at DESC);

COMMIT;
