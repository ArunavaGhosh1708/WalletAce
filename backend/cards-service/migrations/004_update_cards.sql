-- Migration 004: Correct annual fees and affiliate links per 2024-2025 data
-- Run in Neon SQL Editor before triggering POST /admin/sync to add new cards.

BEGIN;

-- ── Annual fee corrections (2024-2025 issuer increases) ───────────────────────
UPDATE cards SET annual_fee = 795.00, last_updated = now()
  WHERE card_name = 'Chase Sapphire Reserve';

UPDATE cards SET annual_fee = 895.00, last_updated = now()
  WHERE card_name = 'American Express Platinum Card';

UPDATE cards SET annual_fee = 325.00, last_updated = now()
  WHERE card_name = 'American Express Gold Card';

UPDATE cards SET annual_fee = 350.00, last_updated = now()
  WHERE card_name = 'Delta SkyMiles Platinum American Express Card';

UPDATE cards SET annual_fee = 650.00, last_updated = now()
  WHERE card_name = 'Delta SkyMiles Reserve American Express Card';

-- ── Fix affiliate links that still hold placeholder values ────────────────────
UPDATE cards SET
    affiliate_link = 'https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve',
    last_updated   = now()
  WHERE card_name = 'Chase Sapphire Reserve'
    AND affiliate_link LIKE 'https://example.com%';

UPDATE cards SET
    affiliate_link = 'https://www.americanexpress.com/us/credit-cards/card/platinum/',
    last_updated   = now()
  WHERE card_name = 'American Express Platinum Card'
    AND affiliate_link LIKE 'https://example.com%';

UPDATE cards SET
    affiliate_link = 'https://www.americanexpress.com/us/credit-cards/card/gold-card/',
    last_updated   = now()
  WHERE card_name = 'American Express Gold Card'
    AND affiliate_link LIKE 'https://example.com%';

UPDATE cards SET
    affiliate_link = 'https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-platinum-american-express-card/',
    last_updated   = now()
  WHERE card_name = 'Delta SkyMiles Platinum American Express Card'
    AND affiliate_link LIKE 'https://example.com%';

UPDATE cards SET
    affiliate_link = 'https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-reserve-american-express-card/',
    last_updated   = now()
  WHERE card_name = 'Delta SkyMiles Reserve American Express Card'
    AND affiliate_link LIKE 'https://example.com%';

-- ── Remove known duplicate rows (keep the row with the lower card_id / earlier insert) ──
-- Only runs if duplicates exist; safe to run even if they don't.
DELETE FROM cards a
  USING cards b
  WHERE a.issuer    = b.issuer
    AND a.card_name = b.card_name
    AND a.card_id   > b.card_id;

COMMIT;
