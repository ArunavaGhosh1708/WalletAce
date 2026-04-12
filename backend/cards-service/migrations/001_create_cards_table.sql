-- Migration 001: Create cards table
-- WalletAce card catalogue — 31 columns

BEGIN;

-- Reward type enum
CREATE TYPE reward_type_enum AS ENUM ('cash_back', 'points', 'miles');

-- Credit tier enum
CREATE TYPE credit_tier_enum AS ENUM ('Poor', 'Fair', 'Good', 'Excellent');

CREATE TABLE IF NOT EXISTS cards (
    -- Identity
    card_id                 UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    issuer                  VARCHAR(60)     NOT NULL,
    card_name               VARCHAR(120)    NOT NULL,

    -- Eligibility
    credit_tier_min         credit_tier_enum NOT NULL,
    income_minimum          INTEGER,                        -- NULL = no minimum

    -- Fees & APR
    annual_fee              NUMERIC(8,2)    NOT NULL DEFAULT 0,
    intro_apr_months        SMALLINT        NOT NULL DEFAULT 0,  -- 0 = no intro APR
    ongoing_apr_min         NUMERIC(5,2)    NOT NULL,
    ongoing_apr_max         NUMERIC(5,2)    NOT NULL,

    -- Reward structure
    reward_type             reward_type_enum NOT NULL,
    reward_network          VARCHAR(30),                    -- Chase UR, Amex MR, etc.
    cpp_cents               NUMERIC(6,3)    NOT NULL,       -- Cents per point/mile (100 for cash back)
    base_rate               NUMERIC(5,3)    NOT NULL,       -- Earn rate on non-category spend

    -- Category reward multipliers
    cat_grocery_rate        NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_dining_rate         NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_gas_rate            NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_travel_rate         NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_transit_rate        NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_streaming_rate      NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_online_retail_rate  NUMERIC(5,3)    NOT NULL DEFAULT 0,
    cat_utilities_rate      NUMERIC(5,3)    NOT NULL DEFAULT 0,

    -- Sign-up bonus
    signup_bonus_value      NUMERIC(8,2)    NOT NULL DEFAULT 0,
    signup_bonus_spend_req  NUMERIC(8,2)    NOT NULL DEFAULT 0,
    signup_bonus_months     SMALLINT        NOT NULL DEFAULT 0,

    -- Perks
    has_lounge_access       BOOLEAN         NOT NULL DEFAULT false,
    has_global_entry        BOOLEAN         NOT NULL DEFAULT false,

    -- Affinity (co-branded cards)
    airline_affinity        VARCHAR(40),                    -- NULL = general card
    hotel_affinity          VARCHAR(40),                    -- NULL = general card

    -- Issuer rules
    issuer_rule_524         BOOLEAN         NOT NULL DEFAULT false,

    -- Monetisation
    affiliate_link          TEXT            NOT NULL,

    -- Sync metadata
    last_updated            TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- Indexes for Phase 1 eligibility filters (hot path)
CREATE INDEX idx_cards_credit_tier    ON cards (credit_tier_min);
CREATE INDEX idx_cards_annual_fee     ON cards (annual_fee);
CREATE INDEX idx_cards_intro_apr      ON cards (intro_apr_months);
CREATE INDEX idx_cards_issuer_524     ON cards (issuer_rule_524) WHERE issuer_rule_524 = true;

-- Indexes for Phase 3 ranking filters
CREATE INDEX idx_cards_reward_type    ON cards (reward_type);
CREATE INDEX idx_cards_airline        ON cards (airline_affinity) WHERE airline_affinity IS NOT NULL;
CREATE INDEX idx_cards_hotel          ON cards (hotel_affinity)   WHERE hotel_affinity   IS NOT NULL;

-- Index for sync queries
CREATE INDEX idx_cards_last_updated   ON cards (last_updated);

COMMIT;
