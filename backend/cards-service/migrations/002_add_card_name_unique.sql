-- Migration 002: Add unique constraint on (issuer, card_name)
-- Required for upsert logic in fetch_cards.py

BEGIN;

ALTER TABLE cards
    ADD CONSTRAINT uq_cards_issuer_name UNIQUE (issuer, card_name);

COMMIT;
