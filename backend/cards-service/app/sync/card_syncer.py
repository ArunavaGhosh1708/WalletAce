"""
card_syncer.py — Weekly DeepSeek card catalogue sync.

Fetches real US credit card data in 4 batches from DeepSeek and upserts
into the cards table. New cards are inserted; existing cards have all
columns updated to reflect the latest data.

Called automatically by the APScheduler weekly job (Sunday 02:00 UTC)
and also exposed via POST /admin/sync for manual triggers.
"""

import json
import logging
from datetime import datetime, timezone

import asyncpg
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


# ── Real application URLs ─────────────────────────────────────────────────────
# Keyed by card_name exactly as returned by DeepSeek.
# These override whatever placeholder URL DeepSeek generates.

AFFILIATE_LINKS: dict[str, str] = {
    # ── Premium travel ────────────────────────────────────────────────────────
    "Chase Sapphire Reserve":                            "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
    "American Express Platinum Card":                    "https://www.americanexpress.com/us/credit-cards/card/platinum/",
    "Amex Platinum":                                     "https://www.americanexpress.com/us/credit-cards/card/platinum/",
    "Capital One Venture X Rewards Credit Card":         "https://creditcards.capitalone.com/venture-x-credit-card/",
    "Capital One Venture X":                             "https://creditcards.capitalone.com/venture-x-credit-card/",
    "U.S. Bank Altitude Reserve Visa Infinite Card":     "https://www.usbank.com/credit-cards/altitude-reserve-visa-infinite-credit-card.html",
    "US Bank Altitude Reserve":                          "https://www.usbank.com/credit-cards/altitude-reserve-visa-infinite-credit-card.html",

    # ── Mid-tier travel ───────────────────────────────────────────────────────
    "Chase Sapphire Preferred Card":                     "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
    "Chase Sapphire Preferred":                          "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
    "American Express Gold Card":                        "https://www.americanexpress.com/us/credit-cards/card/gold-card/",
    "Amex Gold":                                         "https://www.americanexpress.com/us/credit-cards/card/gold-card/",
    "Capital One Venture Rewards Credit Card":           "https://creditcards.capitalone.com/venture-credit-card/",
    "Capital One Venture":                               "https://creditcards.capitalone.com/venture-credit-card/",
    # Citi Premier was renamed Citi Strata Premier — use the current product page
    "Citi Premier Card":                                 "https://www.citi.com/credit-cards/citi-strata-premier-credit-card",
    "Citi Premier":                                      "https://www.citi.com/credit-cards/citi-strata-premier-credit-card",
    "Citi Strata Premier Card":                          "https://www.citi.com/credit-cards/citi-strata-premier-credit-card",

    # ── Airline co-branded — Delta ────────────────────────────────────────────
    "Delta SkyMiles Gold American Express Card":         "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-gold-american-express-card/",
    "Delta SkyMiles Gold Amex":                          "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-gold-american-express-card/",
    "Delta SkyMiles Platinum American Express Card":     "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-platinum-american-express-card/",
    "Delta SkyMiles Platinum Amex":                      "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-platinum-american-express-card/",
    "Delta SkyMiles Reserve American Express Card":      "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-reserve-american-express-card/",
    "Delta SkyMiles Reserve Amex":                       "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-reserve-american-express-card/",

    # ── Airline co-branded — United ───────────────────────────────────────────
    "United Explorer Card":                              "https://creditcards.chase.com/travel-credit-cards/united/explorer",
    "United Club Infinite Card":                         "https://creditcards.chase.com/travel-credit-cards/united/club-infinite",

    # ── Airline co-branded — American Airlines ────────────────────────────────
    # Barclays AAdvantage Aviator Red — direct Barclays apply page
    "AAdvantage Aviator Red World Elite Mastercard":     "https://www.barclays.us/credit-cards/aadvantage-aviator-red-world-elite-mastercard/",
    "AA Aviator Red World Elite Mastercard":             "https://www.barclays.us/credit-cards/aadvantage-aviator-red-world-elite-mastercard/",

    # ── Airline co-branded — Southwest ───────────────────────────────────────
    "Southwest Rapid Rewards Priority Credit Card":      "https://creditcards.chase.com/travel-credit-cards/southwest/priority",
    "Southwest Rapid Rewards Plus Credit Card":          "https://creditcards.chase.com/travel-credit-cards/southwest/plus",
    "Southwest Rapid Rewards Premier Credit Card":       "https://creditcards.chase.com/travel-credit-cards/southwest/premier",

    # ── Airline co-branded — Alaska Airlines ──────────────────────────────────
    "Alaska Airlines Visa Signature Card":               "https://www.bankofamerica.com/credit-cards/products/alaska-airlines-visa-credit-card/",
    "Alaska Airlines Visa Credit Card":                  "https://www.bankofamerica.com/credit-cards/products/alaska-airlines-visa-credit-card/",

    # ── Airline co-branded — JetBlue ──────────────────────────────────────────
    "JetBlue Plus Card":                                 "https://www.barclays.us/credit-cards/jetblue-plus-card/",
    "JetBlue Card":                                      "https://www.barclays.us/credit-cards/jetblue-card/",

    # ── Hotel co-branded — Marriott ───────────────────────────────────────────
    "Marriott Bonvoy Boundless Credit Card":             "https://creditcards.chase.com/travel-credit-cards/marriott-bonvoy/boundless",
    "Marriott Bonvoy Brilliant American Express Card":   "https://www.americanexpress.com/us/credit-cards/card/marriott-bonvoy-brilliant/",
    "Marriott Bonvoy Brilliant Amex":                    "https://www.americanexpress.com/us/credit-cards/card/marriott-bonvoy-brilliant/",
    "Marriott Bonvoy Bold Credit Card":                  "https://creditcards.chase.com/travel-credit-cards/marriott-bonvoy/bold",
    "Marriott Bonvoy Bevy American Express Card":        "https://www.americanexpress.com/us/credit-cards/card/marriott-bonvoy-bevy/",

    # ── Hotel co-branded — Hyatt ──────────────────────────────────────────────
    "World of Hyatt Credit Card":                        "https://creditcards.chase.com/travel-credit-cards/hyatt",

    # ── Hotel co-branded — Hilton ─────────────────────────────────────────────
    "Hilton Honors American Express Surpass Card":       "https://www.americanexpress.com/us/credit-cards/card/hilton-honors-american-express-surpass-card/",
    "Hilton Honors Amex Surpass Card":                   "https://www.americanexpress.com/us/credit-cards/card/hilton-honors-american-express-surpass-card/",
    "Hilton Honors American Express Card":               "https://www.americanexpress.com/us/credit-cards/card/hilton-honors/",
    "Hilton Honors American Express Aspire Card":        "https://www.americanexpress.com/us/credit-cards/card/hilton-honors-aspire/",

    # ── Hotel co-branded — IHG ────────────────────────────────────────────────
    "IHG One Rewards Premier Credit Card":               "https://creditcards.chase.com/travel-credit-cards/ihg/premier",
    "IHG One Rewards Traveler Credit Card":              "https://creditcards.chase.com/travel-credit-cards/ihg/traveler",

    # ── Cash back ─────────────────────────────────────────────────────────────
    "Chase Freedom Unlimited":                           "https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited",
    "Chase Freedom Flex":                                "https://creditcards.chase.com/cash-back-credit-cards/freedom/flex",
    "Blue Cash Preferred Card from American Express":    "https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/",
    "Amex Blue Cash Preferred":                          "https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/",
    "Blue Cash Everyday Card from American Express":     "https://www.americanexpress.com/us/credit-cards/card/blue-cash-everyday/",
    "Amex Blue Cash Everyday Card":                      "https://www.americanexpress.com/us/credit-cards/card/blue-cash-everyday/",
    # Citi Double Cash is now the Citi Double Cash+ — same URL resolves correctly
    "Citi Double Cash Card":                             "https://www.citi.com/credit-cards/citi-double-cash-credit-card",
    "Wells Fargo Active Cash Card":                      "https://www.wellsfargo.com/credit-cards/active-cash/",
    "Capital One SavorOne Cash Rewards Credit Card":     "https://creditcards.capitalone.com/savor-one-credit-card/",
    "Capital One Quicksilver Cash Rewards Credit Card":  "https://creditcards.capitalone.com/quicksilver-credit-card/",
    "Discover it Cash Back":                             "https://www.discover.com/credit-cards/cash-back/it-card.html",
    "Bank of America Unlimited Cash Rewards Credit Card": "https://www.bankofamerica.com/credit-cards/products/unlimited-cash-back-credit-card/",
    "Bank of America Customized Cash Rewards Credit Card": "https://www.bankofamerica.com/credit-cards/products/cash-back-credit-card/",
    "U.S. Bank Cash+ Visa Signature Card":               "https://www.usbank.com/credit-cards/cash-plus-visa-signature-credit-card.html",
    "US Bank Cash+ Visa Signature Card":                 "https://www.usbank.com/credit-cards/cash-plus-visa-signature-credit-card.html",
    # Fidelity card is issued by Elan Financial / US Bank — use Fidelity's own page
    "Fidelity Rewards Visa Signature Card":              "https://www.fidelity.com/spend-save/visa-signature-card",
    "Apple Card":                                        "https://www.apple.com/apple-card/",
    # Bilt card apply page
    "Bilt Mastercard":                                   "https://www.biltrewards.com/card",

    # ── Balance transfer / low APR ────────────────────────────────────────────
    # Citi Simplicity — use the current product slug
    "Citi Simplicity Card":                              "https://www.citi.com/credit-cards/citi-simplicity-credit-card",
    "Wells Fargo Reflect Card":                          "https://www.wellsfargo.com/credit-cards/reflect/",

    # ── Fair / limited credit ─────────────────────────────────────────────────
    "Capital One Platinum Credit Card":                  "https://creditcards.capitalone.com/platinum-credit-card/",
    # Petal 2 is now WebBank-issued under the "Petal" brand
    "Petal 2 Visa Credit Card":                          "https://www.petalcard.com/",
    "Petal 2 Cash Back, No Fees Visa Credit Card":       "https://www.petalcard.com/",
    "Mission Lane Visa Credit Card":                     "https://missionlane.com/credit-cards/",

    # ── Student ───────────────────────────────────────────────────────────────
    "Discover it Student Cash Back":                     "https://www.discover.com/credit-cards/student/it-card.html",
    "Discover it Student Chrome":                        "https://www.discover.com/credit-cards/student/chrome-card.html",

    # ── Secured / credit-building ─────────────────────────────────────────────
    "Discover it Secured Credit Card":                   "https://www.discover.com/credit-cards/secured/",
    "Capital One Platinum Secured Credit Card":          "https://creditcards.capitalone.com/platinum-secured-credit-card/",
    # OpenSky — no application redirect needed, direct homepage
    "OpenSky Secured Visa Credit Card":                  "https://www.openskycc.com/apply",
    # Self — credit-builder card
    "Self Secured Visa Credit Card":                     "https://www.self.inc/credit-card",
}


def _apply_real_links(cards: list[dict]) -> list[dict]:
    """Replace placeholder affiliate_link with the real application URL."""
    for card in cards:
        real = AFFILIATE_LINKS.get(card.get("card_name", ""))
        if real:
            card["affiliate_link"] = real
    return cards


def _dedup_by_name(cards: list[dict]) -> list[dict]:
    """
    Remove duplicate card_name entries that may arise if DeepSeek drifts and
    repeats a card across batches. Last occurrence wins (latest batch = freshest data).
    Logs any duplicates so they can be spotted in sync logs.
    """
    seen: dict[str, dict] = {}
    for card in cards:
        name = card.get("card_name", "")
        if name in seen:
            logger.warning("Duplicate card_name across batches — keeping last: %r", name)
        seen[name] = card
    return list(seen.values())


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a credit card data expert. Generate accurate data for real, currently active \
US consumer credit cards. All rates, fees, and bonuses must reflect current real-world values \
as of 2024-2025. Do not invent cards — only include cards that actually exist and are \
currently available to new applicants.\
"""

# Shared field-level rules injected into every batch prompt.
# Kept here so a single edit propagates to all batches.
CARD_SCHEMA = """\
For EACH card return this exact JSON object shape — no extra fields, no missing fields:
{
  "issuer": "string (e.g. Chase, Amex, Capital One)",
  "card_name": "string (full official card name)",
  "credit_tier_min": "Excellent | Good | Fair | Poor",
  "income_minimum": null or integer (USD, only set if issuer publicly states a minimum),
  "annual_fee": float (0.00 if none),
  "intro_apr_months": integer (0 if none),
  "ongoing_apr_min": float (e.g. 20.99),
  "ongoing_apr_max": float (e.g. 29.99),
  "reward_type": "cash_back | points | miles",
  "reward_network": null or string (e.g. "Chase UR", "Amex MR", "Delta SkyMiles", "Citi TY"),
  "cpp_cents": float (EXACTLY 100.0 for cash_back; for points/miles use realistic redemption value in cents, e.g. 150.0 for Chase UR, 100.0 for airline miles at face value),
  "base_rate": float (UNIT RULE — cash_back: decimal fraction, 1.5% = 0.015; points/miles: earn multiplier, 1x = 1.0, 3x = 3.0),
  "cat_grocery_rate": float (same unit as base_rate — use 0.0 if no category bonus),
  "cat_dining_rate": float,
  "cat_gas_rate": float,
  "cat_travel_rate": float,
  "cat_transit_rate": float,
  "cat_streaming_rate": float,
  "cat_online_retail_rate": float,
  "cat_utilities_rate": float,
  "signup_bonus_value": float (USD dollar value of the bonus — 0.0 if none),
  "signup_bonus_spend_req": float (required spend in USD — 0.0 if no bonus),
  "signup_bonus_months": integer (months to meet spend requirement — 0 if no bonus),
  "has_lounge_access": true | false,
  "has_global_entry": true | false,
  "airline_affinity": null or one of: "delta" | "united" | "aa" | "southwest" | "alaska" | "jetblue" | "hawaiian" | "frontier" | "spirit",
  "hotel_affinity": null or one of: "marriott" | "hilton" | "hyatt" | "ihg",
  "issuer_rule_524": true | false (true ONLY for Chase-issued cards; false for all others),
  "affiliate_link": "https://example.com/apply/<slug>"
}

CRITICAL RULES:
- cash_back base_rate and category rates are DECIMAL fractions (3% = 0.03, NOT 3.0).
- points/miles base_rate and category rates are EARN MULTIPLIERS (3x points = 3.0, NOT 0.03).
- cpp_cents is ALWAYS 100.0 for cash_back cards.
- signup_bonus_value is always in USD dollars (not points).
- Return ONLY a JSON object with a "cards" key containing the array. No markdown, no commentary.\
"""

# ── Card lists per batch (single source of truth for names) ──────────────────
# Defined here so each batch prompt can explicitly exclude all prior batches,
# preventing the model from drifting and repeating already-covered cards.

_BATCH_1_CARDS = [
    "Chase Sapphire Reserve", "American Express Platinum Card",
    "Capital One Venture X Rewards Credit Card", "U.S. Bank Altitude Reserve Visa Infinite Card",
    "Chase Sapphire Preferred Card", "American Express Gold Card",
    "Capital One Venture Rewards Credit Card", "Citi Premier Card",
    "Delta SkyMiles Gold American Express Card", "Delta SkyMiles Platinum American Express Card",
    "United Explorer Card", "AAdvantage Aviator Red World Elite Mastercard",
]

_BATCH_2_CARDS = [
    "Southwest Rapid Rewards Priority Credit Card", "Southwest Rapid Rewards Plus Credit Card",
    "Marriott Bonvoy Boundless Credit Card", "Marriott Bonvoy Brilliant American Express Card",
    "World of Hyatt Credit Card", "Hilton Honors American Express Surpass Card",
    "IHG One Rewards Premier Credit Card",
    "Chase Freedom Unlimited", "Chase Freedom Flex",
    "Blue Cash Preferred Card from American Express",
    "Citi Double Cash Card", "Wells Fargo Active Cash Card",
]

_BATCH_3_CARDS = [
    "Capital One SavorOne Cash Rewards Credit Card",
    "Capital One Quicksilver Cash Rewards Credit Card",
    "Discover it Cash Back",
    "Bank of America Unlimited Cash Rewards Credit Card",
    "Blue Cash Everyday Card from American Express",
    "U.S. Bank Cash+ Visa Signature Card",
    "Citi Simplicity Card", "Wells Fargo Reflect Card", "Apple Card",
    "Hilton Honors American Express Card",
    "IHG One Rewards Traveler Credit Card", "Bilt Mastercard",
]

_BATCH_4_CARDS = [
    "Capital One Platinum Credit Card", "Discover it Student Cash Back",
    "Discover it Secured Credit Card", "Capital One Platinum Secured Credit Card",
    "OpenSky Secured Visa Credit Card", "Self Secured Visa Credit Card",
    "Petal 2 Visa Credit Card", "Mission Lane Visa Credit Card",
    "Delta SkyMiles Reserve American Express Card", "United Club Infinite Card",
    "Bank of America Customized Cash Rewards Credit Card",
    "Fidelity Rewards Visa Signature Card",
]

_BATCH_5_CARDS = [
    "Alaska Airlines Visa Signature Card",
    "JetBlue Plus Card",
]


def _exclusion_block(already_done: list[list[str]]) -> str:
    """Build a 'do NOT include' list from all prior batches for injection into the next prompt."""
    flat = [name for batch in already_done for name in batch]
    lines = "\n".join(f"  - {n}" for n in flat)
    return (
        f"\nDo NOT include any of the following cards — they are already covered in prior batches:\n"
        f"{lines}\n"
    )


def _make_prompt(card_list: list[str], already_done: list[list[str]]) -> str:
    names = ", ".join(card_list)
    exclusion = _exclusion_block(already_done) if already_done else ""
    return (
        f"Generate data for exactly {len(card_list)} real, currently active US credit cards:\n"
        f"{names}.\n"
        f"{exclusion}\n"
        + CARD_SCHEMA
    )


# Build prompts with cross-batch exclusion lists baked in
BATCHES: list[tuple[list[str], str]] = [
    (_BATCH_1_CARDS, _make_prompt(_BATCH_1_CARDS, [])),
    (_BATCH_2_CARDS, _make_prompt(_BATCH_2_CARDS, [_BATCH_1_CARDS])),
    (_BATCH_3_CARDS, _make_prompt(_BATCH_3_CARDS, [_BATCH_1_CARDS, _BATCH_2_CARDS])),
    (_BATCH_4_CARDS, _make_prompt(_BATCH_4_CARDS, [_BATCH_1_CARDS, _BATCH_2_CARDS, _BATCH_3_CARDS])),
    (_BATCH_5_CARDS, _make_prompt(_BATCH_5_CARDS, [_BATCH_1_CARDS, _BATCH_2_CARDS, _BATCH_3_CARDS, _BATCH_4_CARDS])),
]


# ── DeepSeek fetch ────────────────────────────────────────────────────────────

def _call_deepseek(client: OpenAI, prompt: str, batch_num: int, expected: int) -> list[dict]:
    logger.info("Calling DeepSeek — batch %d (%d cards expected)", batch_num, expected)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=8192,
    )
    raw = response.choices[0].message.content or ""
    data = json.loads(raw)
    if isinstance(data, list):
        cards = data
    else:
        cards = next((v for v in data.values() if isinstance(v, list)), None)
        if cards is None:
            raise ValueError(f"Unexpected response shape: {list(data.keys())}")
    if len(cards) != expected:
        logger.warning("Batch %d: expected %d cards, got %d", batch_num, expected, len(cards))
    return cards


def _fetch_from_deepseek() -> list[dict]:
    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url="https://api.deepseek.com",
    )
    all_cards: list[dict] = []
    for i, (card_list, prompt) in enumerate(BATCHES, 1):
        batch = _call_deepseek(client, prompt, i, len(card_list))
        logger.info("Batch %d — %d cards received", i, len(batch))
        all_cards.extend(batch)

    # Deduplicate by card_name before applying links — last batch wins on conflict
    all_cards = _dedup_by_name(all_cards)
    return _apply_real_links(all_cards)


# ── DB upsert ─────────────────────────────────────────────────────────────────

_INSERT_SQL = """
INSERT INTO cards (
    issuer, card_name, credit_tier_min, income_minimum,
    annual_fee, intro_apr_months, ongoing_apr_min, ongoing_apr_max,
    reward_type, reward_network, cpp_cents, base_rate,
    cat_grocery_rate, cat_dining_rate, cat_gas_rate, cat_travel_rate,
    cat_transit_rate, cat_streaming_rate, cat_online_retail_rate, cat_utilities_rate,
    signup_bonus_value, signup_bonus_spend_req, signup_bonus_months,
    has_lounge_access, has_global_entry,
    airline_affinity, hotel_affinity,
    issuer_rule_524, affiliate_link
) VALUES (
    $1, $2, $3, $4,
    $5, $6, $7, $8,
    $9, $10, $11, $12,
    $13, $14, $15, $16,
    $17, $18, $19, $20,
    $21, $22, $23,
    $24, $25,
    $26, $27,
    $28, $29
)
ON CONFLICT (issuer, card_name) DO UPDATE
    SET affiliate_link = EXCLUDED.affiliate_link
    WHERE cards.affiliate_link LIKE 'https://example.com%'
"""


def _card_params(card: dict) -> tuple:
    return (
        card["issuer"], card["card_name"], card["credit_tier_min"],
        card.get("income_minimum"), float(card["annual_fee"]),
        int(card["intro_apr_months"]), float(card["ongoing_apr_min"]),
        float(card["ongoing_apr_max"]), card["reward_type"],
        card.get("reward_network"), float(card["cpp_cents"]),
        float(card["base_rate"]), float(card["cat_grocery_rate"]),
        float(card["cat_dining_rate"]), float(card["cat_gas_rate"]),
        float(card["cat_travel_rate"]), float(card["cat_transit_rate"]),
        float(card["cat_streaming_rate"]), float(card["cat_online_retail_rate"]),
        float(card["cat_utilities_rate"]), float(card["signup_bonus_value"]),
        float(card["signup_bonus_spend_req"]), int(card["signup_bonus_months"]),
        bool(card["has_lounge_access"]), bool(card["has_global_entry"]),
        card.get("airline_affinity"), card.get("hotel_affinity"),
        bool(card["issuer_rule_524"]), card["affiliate_link"],
    )


async def _upsert_cards(cards: list[dict]) -> tuple[int, int]:
    ok = 0
    skipped = 0
    # Acquire connection AFTER the DeepSeek fetch so it's always fresh.
    # Neon serverless closes idle connections, so sharing one across the
    # multi-minute fetch would result in a dead connection by the time we write.
    dsn = settings.database_url.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn=dsn)
    try:
        for card in cards:
            try:
                await conn.execute(_INSERT_SQL, *_card_params(card))
                ok += 1
            except Exception:
                logger.exception("Failed to upsert card: %s", card.get("card_name"))
                skipped += 1
    finally:
        await conn.close()
    return ok, skipped


# ── Public entry point ────────────────────────────────────────────────────────

async def run_sync() -> dict:
    """
    Fetch all card batches from DeepSeek and upsert into the DB.
    Returns a summary dict: {upserted, skipped, ran_at}.
    """
    if not settings.deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY not set — skipping card sync")
        return {"upserted": 0, "skipped": 0, "error": "DEEPSEEK_API_KEY not configured"}

    logger.info("Card sync started")
    cards = _fetch_from_deepseek()
    logger.info("DeepSeek returned %d cards total", len(cards))

    ok, skipped = await _upsert_cards(cards)
    ran_at = datetime.now(timezone.utc).isoformat()
    logger.info("Card sync complete — %d upserted, %d skipped", ok, skipped)

    return {"upserted": ok, "skipped": skipped, "ran_at": ran_at}
