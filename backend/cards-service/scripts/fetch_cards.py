"""
fetch_cards.py — Populate the database with real US credit cards via DeepSeek.

DeepSeek generates a comprehensive, accurate dataset of active US credit cards
covering all credit tiers, reward types, issuers, and spending categories.
This replaces the 20-card seed file with a realistic 50+ card catalogue.

Usage:
    cd backend/cards-service
    python scripts/fetch_cards.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://", "postgresql://"
)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

if not DEEPSEEK_API_KEY:
    print("ERROR: DEEPSEEK_API_KEY not set in .env")
    sys.exit(1)


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a credit card data expert. Generate accurate data for real, currently active \
US consumer credit cards. All rates, fees, and bonuses must reflect current real-world values \
as of 2024-2025. Do not invent cards — only include cards that actually exist and are \
currently available to new applicants.\
"""

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
  "cpp_cents": float (EXACTLY 100.0 for cash_back; for points/miles use realistic redemption value in cents, e.g. 150.0 for Chase UR),
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

# ── Card name lists per batch ─────────────────────────────────────────────────
# Explicit lists drive both the prompts and the cross-batch exclusion blocks,
# preventing the model from drifting and repeating already-covered cards.

_B1 = [
    "Chase Sapphire Reserve", "American Express Platinum Card",
    "Capital One Venture X Rewards Credit Card", "U.S. Bank Altitude Reserve Visa Infinite Card",
    "Chase Sapphire Preferred Card", "American Express Gold Card",
    "Capital One Venture Rewards Credit Card", "Citi Premier Card",
    "Delta SkyMiles Gold American Express Card", "Delta SkyMiles Platinum American Express Card",
    "United Explorer Card", "AAdvantage Aviator Red World Elite Mastercard",
]
_B2 = [
    "Southwest Rapid Rewards Priority Credit Card", "Southwest Rapid Rewards Plus Credit Card",
    "Marriott Bonvoy Boundless Credit Card", "Marriott Bonvoy Brilliant American Express Card",
    "World of Hyatt Credit Card", "Hilton Honors American Express Surpass Card",
    "IHG One Rewards Premier Credit Card",
    "Chase Freedom Unlimited", "Chase Freedom Flex",
    "Blue Cash Preferred Card from American Express",
    "Citi Double Cash Card", "Wells Fargo Active Cash Card",
]
_B3 = [
    "Capital One SavorOne Cash Rewards Credit Card",
    "Capital One Quicksilver Cash Rewards Credit Card",
    "Discover it Cash Back", "Bank of America Unlimited Cash Rewards Credit Card",
    "Blue Cash Everyday Card from American Express", "U.S. Bank Cash+ Visa Signature Card",
    "Citi Simplicity Card", "Wells Fargo Reflect Card", "Apple Card",
    "Hilton Honors American Express Card", "IHG One Rewards Traveler Credit Card", "Bilt Mastercard",
]
_B4 = [
    "Capital One Platinum Credit Card", "Discover it Student Cash Back",
    "Discover it Secured Credit Card", "Capital One Platinum Secured Credit Card",
    "OpenSky Secured Visa Credit Card", "Self Secured Visa Credit Card",
    "Petal 2 Visa Credit Card", "Mission Lane Visa Credit Card",
    "Delta SkyMiles Reserve American Express Card", "United Club Infinite Card",
    "Bank of America Customized Cash Rewards Credit Card", "Fidelity Rewards Visa Signature Card",
]
_B5 = [
    "Alaska Airlines Visa Signature Card",
    "JetBlue Plus Card",
]
_B6 = [
    "Discover it Student Chrome",
    "Citi Custom Cash Card",
    "Citi Diamond Preferred Card",
    "Wells Fargo Autograph Card",
    "Wells Fargo Autograph Journey Visa Card",
    "Bank of America Travel Rewards Credit Card",
    "Bank of America Premium Rewards Credit Card",
    "Capital One SavorOne Student Cash Rewards Credit Card",
    "Capital One Quicksilver Student Cash Rewards Credit Card",
    "Chase Freedom Student Credit Card",
    "Chase Freedom Rise Credit Card",
    "U.S. Bank Altitude Connect Visa Signature Card",
]
_B7 = [
    "Navy Federal cashRewards Credit Card",
    "Navy Federal GO REWARDS Credit Card",
    "Navy Federal Platinum Credit Card",
    "Navy Federal More Rewards American Express Card",
    "Navy Federal nRewards Secured Credit Card",
    "Alliant Cashback Visa Signature Card",
    "Alliant Visa Platinum Card",
    "SoFi Credit Card",
    "Robinhood Gold Card",
    "TD Cash Credit Card",
    "TD Double Up Credit Card",
]
_B8 = [
    "Chime Credit Builder Secured Visa Credit Card",
    "Upgrade Cash Rewards Visa",
    "Upgrade Triple Cash Rewards Visa",
    "PayPal Cashback Mastercard",
    "Venmo Credit Card",
    "Sam's Club Mastercard",
    "Grow Credit Mastercard",
    "Hilton Honors American Express Aspire Card",
    "Marriott Bonvoy Bevy American Express Card",
    "Marriott Bonvoy Bold Credit Card",
    "Southwest Rapid Rewards Premier Credit Card",
]


def _make_prompt(card_list: list[str], prior_batches: list[list[str]]) -> str:
    names = ", ".join(card_list)
    exclusion = ""
    if prior_batches:
        flat = [name for batch in prior_batches for name in batch]
        lines = "\n".join(f"  - {n}" for n in flat)
        exclusion = (
            f"\nDo NOT include any of the following cards — they are already covered:\n"
            f"{lines}\n"
        )
    return (
        f"Generate data for exactly {len(card_list)} real, currently active US credit cards:\n"
        f"{names}.\n"
        f"{exclusion}\n"
        + CARD_SCHEMA
    )


BATCH_1_PROMPT = _make_prompt(_B1, [])
BATCH_2_PROMPT = _make_prompt(_B2, [_B1])
BATCH_3_PROMPT = _make_prompt(_B3, [_B1, _B2])
BATCH_4_PROMPT = _make_prompt(_B4, [_B1, _B2, _B3])
BATCH_5_PROMPT = _make_prompt(_B5, [_B1, _B2, _B3, _B4])
BATCH_6_PROMPT = _make_prompt(_B6, [_B1, _B2, _B3, _B4, _B5])
BATCH_7_PROMPT = _make_prompt(_B7, [_B1, _B2, _B3, _B4, _B5, _B6])
BATCH_8_PROMPT = _make_prompt(_B8, [_B1, _B2, _B3, _B4, _B5, _B6, _B7])

BATCHES = [
    BATCH_1_PROMPT, BATCH_2_PROMPT, BATCH_3_PROMPT, BATCH_4_PROMPT,
    BATCH_5_PROMPT, BATCH_6_PROMPT, BATCH_7_PROMPT, BATCH_8_PROMPT,
]


# ── DeepSeek call ─────────────────────────────────────────────────────────────

def _call_deepseek(client: OpenAI, prompt: str, batch_num: int, expected: int) -> list[dict]:
    print(f"Calling DeepSeek — batch {batch_num} ({expected} cards expected)...")
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
        print(f"  ⚠ Batch {batch_num}: expected {expected} cards, got {len(cards)}")
    return cards


AFFILIATE_LINKS: dict[str, str] = {
    "Chase Sapphire Reserve":                   "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
    "The Platinum Card from American Express":   "https://www.americanexpress.com/us/credit-cards/card/platinum/",
    "Amex Platinum":                             "https://www.americanexpress.com/us/credit-cards/card/platinum/",
    "Capital One Venture X":                     "https://creditcards.capitalone.com/venture-x-credit-card/",
    "US Bank Altitude Reserve":                  "https://www.usbank.com/credit-cards/altitude-reserve-visa-infinite-credit-card.html",
    "Chase Sapphire Preferred":                  "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
    "Amex Gold":                                 "https://www.americanexpress.com/us/credit-cards/card/gold-card/",
    "Capital One Venture":                       "https://creditcards.capitalone.com/venture-credit-card/",
    "Citi Premier":                              "https://www.citi.com/credit-cards/citi-strata-premier-credit-card",
    "Delta SkyMiles Gold Amex":                  "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-gold-american-express-card/",
    "Delta SkyMiles Platinum Amex":              "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-platinum-american-express-card/",
    "Delta SkyMiles Reserve Amex":               "https://www.americanexpress.com/us/credit-cards/card/delta-skymiles-reserve-american-express-card/",
    "United Explorer Card":                      "https://creditcards.chase.com/travel-credit-cards/united/explorer",
    "United Club Infinite Card":                 "https://creditcards.chase.com/travel-credit-cards/united/club-infinite",
    "AA Aviator Red World Elite Mastercard":     "https://www.barclays.us/credit-cards/aadvantage-aviator-red-world-elite-mastercard/",
    "Southwest Rapid Rewards Priority Credit Card": "https://creditcards.chase.com/travel-credit-cards/southwest/priority",
    "Southwest Rapid Rewards Plus Credit Card":  "https://creditcards.chase.com/travel-credit-cards/southwest/plus",
    "Marriott Bonvoy Boundless Credit Card":     "https://creditcards.chase.com/travel-credit-cards/marriott-bonvoy/boundless",
    "Marriott Bonvoy Brilliant Amex":            "https://www.americanexpress.com/us/credit-cards/card/marriott-bonvoy-brilliant/",
    "World of Hyatt Credit Card":                "https://creditcards.chase.com/travel-credit-cards/hyatt",
    "Hilton Honors Amex Surpass Card":           "https://www.americanexpress.com/us/credit-cards/card/hilton-honors-american-express-surpass-card/",
    "Hilton Honors American Express Card":       "https://www.americanexpress.com/us/credit-cards/card/hilton-honors/",
    "IHG One Rewards Premier Credit Card":       "https://creditcards.chase.com/travel-credit-cards/ihg/premier",
    "IHG One Rewards Traveler Credit Card":      "https://creditcards.chase.com/travel-credit-cards/ihg/traveler",
    "Chase Freedom Unlimited":                   "https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited",
    "Chase Freedom Flex":                        "https://creditcards.chase.com/cash-back-credit-cards/freedom/flex",
    "Amex Blue Cash Preferred":                  "https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/",
    "Amex Blue Cash Everyday Card":              "https://www.americanexpress.com/us/credit-cards/card/blue-cash-everyday/",
    "Citi Double Cash Card":                     "https://www.citi.com/credit-cards/citi-double-cash-credit-card",
    "Wells Fargo Active Cash Card":              "https://www.wellsfargo.com/credit-cards/active-cash/",
    "Capital One SavorOne Cash Rewards Credit Card": "https://creditcards.capitalone.com/savor-one-credit-card/",
    "Capital One Quicksilver Cash Rewards Credit Card": "https://creditcards.capitalone.com/quicksilver-credit-card/",
    "Discover it Cash Back":                     "https://www.discover.com/credit-cards/cash-back/it-card.html",
    "Bank of America Unlimited Cash Rewards Credit Card": "https://www.bankofamerica.com/credit-cards/products/unlimited-cash-back-credit-card/",
    "Bank of America Customized Cash Rewards Credit Card": "https://www.bankofamerica.com/credit-cards/products/cash-back-credit-card/",
    "US Bank Cash+ Visa Signature Card":         "https://www.usbank.com/credit-cards/cash-plus-visa-signature-credit-card.html",
    "Fidelity Rewards Visa Signature Card":      "https://www.fidelity.com/cash-management/visa-signature-card",
    "Apple Card":                                "https://www.apple.com/apple-card/",
    "Bilt Mastercard":                           "https://www.biltrewards.com/card",
    "Citi Simplicity Card":                              "https://www.citi.com/credit-cards/citi-simplicity-credit-card",
    "Citi Diamond Preferred Card":                       "https://www.citi.com/credit-cards/citi-diamond-preferred-credit-card",
    "Citi Custom Cash Card":                             "https://www.citi.com/credit-cards/citi-custom-cash-credit-card",
    "Wells Fargo Reflect Card":                          "https://www.wellsfargo.com/credit-cards/reflect/",
    "Wells Fargo Autograph Card":                        "https://www.wellsfargo.com/credit-cards/autograph/",
    "Wells Fargo Autograph Journey Visa Card":           "https://www.wellsfargo.com/credit-cards/autograph-journey/",
    "Bank of America Travel Rewards Credit Card":        "https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card/",
    "Bank of America Premium Rewards Credit Card":       "https://www.bankofamerica.com/credit-cards/products/premium-rewards-credit-card/",
    "U.S. Bank Altitude Connect Visa Signature Card":    "https://www.usbank.com/credit-cards/altitude-connect-visa-signature-credit-card.html",
    "Capital One Platinum Credit Card":                  "https://creditcards.capitalone.com/platinum-credit-card/",
    "Capital One SavorOne Student Cash Rewards Credit Card":    "https://creditcards.capitalone.com/savor-one-student-credit-card/",
    "Capital One Quicksilver Student Cash Rewards Credit Card": "https://creditcards.capitalone.com/quicksilver-student-credit-card/",
    "Chase Freedom Student Credit Card":                 "https://creditcards.chase.com/cash-back-credit-cards/freedom/student",
    "Chase Freedom Rise Credit Card":                    "https://creditcards.chase.com/cash-back-credit-cards/freedom/rise",
    "Southwest Rapid Rewards Premier Credit Card":       "https://creditcards.chase.com/travel-credit-cards/southwest/premier",
    "Marriott Bonvoy Bold Credit Card":                  "https://creditcards.chase.com/travel-credit-cards/marriott-bonvoy/bold",
    "Marriott Bonvoy Bevy American Express Card":        "https://www.americanexpress.com/us/credit-cards/card/marriott-bonvoy-bevy/",
    "Hilton Honors American Express Aspire Card":        "https://www.americanexpress.com/us/credit-cards/card/hilton-honors-aspire/",
    "Petal 2 Visa Credit Card":                          "https://www.petalcard.com/",
    "Mission Lane Visa Credit Card":                     "https://missionlane.com/credit-cards/",
    "Discover it Student Cash Back":                     "https://www.discover.com/credit-cards/student/it-card.html",
    "Discover it Student Chrome":                        "https://www.discover.com/credit-cards/student/chrome-card.html",
    "Discover it Secured Credit Card":                   "https://www.discover.com/credit-cards/secured/",
    "Capital One Platinum Secured Credit Card":          "https://creditcards.capitalone.com/platinum-secured-credit-card/",
    "OpenSky Secured Visa Credit Card":                  "https://www.openskycc.com/apply",
    "Self Secured Visa Credit Card":                     "https://www.self.inc/credit-card",
    "Navy Federal cashRewards Credit Card":              "https://www.navyfederal.org/loans-cards/credit-cards/cashrewards/",
    "Navy Federal GO REWARDS Credit Card":               "https://www.navyfederal.org/loans-cards/credit-cards/go-rewards/",
    "Navy Federal Platinum Credit Card":                 "https://www.navyfederal.org/loans-cards/credit-cards/platinum/",
    "Navy Federal More Rewards American Express Card":   "https://www.navyfederal.org/loans-cards/credit-cards/more-rewards/",
    "Navy Federal nRewards Secured Credit Card":         "https://www.navyfederal.org/loans-cards/credit-cards/nrewards-secured/",
    "Alliant Cashback Visa Signature Card":              "https://www.alliantcreditunion.org/bank/visa-signature-credit-card",
    "Alliant Visa Platinum Card":                        "https://www.alliantcreditunion.org/bank/visa-platinum-card",
    "TD Cash Credit Card":                               "https://www.td.com/us/en/personal-banking/credit-cards/td-cash-credit-card",
    "TD Double Up Credit Card":                          "https://www.td.com/us/en/personal-banking/credit-cards/td-double-up-credit-card",
    "SoFi Credit Card":                                  "https://www.sofi.com/credit-card/",
    "Robinhood Gold Card":                               "https://robinhood.com/creditcard/",
    "Chime Credit Builder Secured Visa Credit Card":     "https://www.chime.com/credit-builder-visa-credit-card/",
    "Upgrade Cash Rewards Visa":                         "https://www.upgrade.com/cash-rewards-visa/",
    "Upgrade Triple Cash Rewards Visa":                  "https://www.upgrade.com/triple-cash-rewards-visa/",
    "PayPal Cashback Mastercard":                        "https://www.paypal.com/us/webapps/mpp/cashback-credit-card",
    "Venmo Credit Card":                                 "https://venmo.com/creditcard/",
    "Sam's Club Mastercard":                             "https://www.samsclub.com/content/credit-center",
    "Grow Credit Mastercard":                            "https://www.growcredit.com/card",
}


def _dedup_by_name(cards: list[dict]) -> list[dict]:
    """Remove duplicates by card_name — last occurrence wins. Warns on any collision."""
    seen: dict[str, dict] = {}
    for card in cards:
        name = card.get("card_name", "")
        if name in seen:
            print(f"  ⚠ Duplicate across batches — keeping last: {name!r}")
        seen[name] = card
    return list(seen.values())


def fetch_cards_from_deepseek() -> list[dict]:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    # Pair each batch list with its prompt so we know the expected card count
    batch_pairs = list(zip([_B1, _B2, _B3, _B4, _B5, _B6, _B7, _B8], BATCHES))
    all_cards: list[dict] = []
    for i, (card_list, prompt) in enumerate(batch_pairs, 1):
        batch = _call_deepseek(client, prompt, i, len(card_list))
        print(f"  → {len(batch)} cards received")
        all_cards.extend(batch)

    # Deduplicate by card_name before applying links — last batch wins on collision
    all_cards = _dedup_by_name(all_cards)

    # Replace placeholder links with real application URLs
    for card in all_cards:
        real = AFFILIATE_LINKS.get(card.get("card_name", ""))
        if real:
            card["affiliate_link"] = real
    return all_cards


# ── DB insert ─────────────────────────────────────────────────────────────────

INSERT_SQL = """
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
ON CONFLICT (issuer, card_name) DO UPDATE SET
    credit_tier_min        = EXCLUDED.credit_tier_min,
    income_minimum         = EXCLUDED.income_minimum,
    annual_fee             = EXCLUDED.annual_fee,
    intro_apr_months       = EXCLUDED.intro_apr_months,
    ongoing_apr_min        = EXCLUDED.ongoing_apr_min,
    ongoing_apr_max        = EXCLUDED.ongoing_apr_max,
    reward_type            = EXCLUDED.reward_type,
    reward_network         = EXCLUDED.reward_network,
    cpp_cents              = EXCLUDED.cpp_cents,
    base_rate              = EXCLUDED.base_rate,
    cat_grocery_rate       = EXCLUDED.cat_grocery_rate,
    cat_dining_rate        = EXCLUDED.cat_dining_rate,
    cat_gas_rate           = EXCLUDED.cat_gas_rate,
    cat_travel_rate        = EXCLUDED.cat_travel_rate,
    cat_transit_rate       = EXCLUDED.cat_transit_rate,
    cat_streaming_rate     = EXCLUDED.cat_streaming_rate,
    cat_online_retail_rate = EXCLUDED.cat_online_retail_rate,
    cat_utilities_rate     = EXCLUDED.cat_utilities_rate,
    signup_bonus_value     = EXCLUDED.signup_bonus_value,
    signup_bonus_spend_req = EXCLUDED.signup_bonus_spend_req,
    signup_bonus_months    = EXCLUDED.signup_bonus_months,
    has_lounge_access      = EXCLUDED.has_lounge_access,
    has_global_entry       = EXCLUDED.has_global_entry,
    airline_affinity       = EXCLUDED.airline_affinity,
    hotel_affinity         = EXCLUDED.hotel_affinity,
    issuer_rule_524        = EXCLUDED.issuer_rule_524,
    affiliate_link         = EXCLUDED.affiliate_link,
    last_updated           = now()
"""


async def insert_cards(cards: list[dict]) -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        ok = 0
        skipped = 0
        for card in cards:
            try:
                await conn.execute(
                    INSERT_SQL,
                    card["issuer"],
                    card["card_name"],
                    card["credit_tier_min"],
                    card.get("income_minimum"),
                    float(card["annual_fee"]),
                    int(card["intro_apr_months"]),
                    float(card["ongoing_apr_min"]),
                    float(card["ongoing_apr_max"]),
                    card["reward_type"],
                    card.get("reward_network"),
                    float(card["cpp_cents"]),
                    float(card["base_rate"]),
                    float(card["cat_grocery_rate"]),
                    float(card["cat_dining_rate"]),
                    float(card["cat_gas_rate"]),
                    float(card["cat_travel_rate"]),
                    float(card["cat_transit_rate"]),
                    float(card["cat_streaming_rate"]),
                    float(card["cat_online_retail_rate"]),
                    float(card["cat_utilities_rate"]),
                    float(card["signup_bonus_value"]),
                    float(card["signup_bonus_spend_req"]),
                    int(card["signup_bonus_months"]),
                    bool(card["has_lounge_access"]),
                    bool(card["has_global_entry"]),
                    card.get("airline_affinity"),
                    card.get("hotel_affinity"),
                    bool(card["issuer_rule_524"]),
                    card["affiliate_link"],
                )
                print(f"  ✓ {card['issuer']:20} {card['card_name']}")
                ok += 1
            except Exception as e:
                print(f"  ✗ {card.get('card_name', '?')} — {e}")
                skipped += 1

        print(f"\nDone: {ok} upserted, {skipped} skipped.")
    finally:
        await conn.close()


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    cards = fetch_cards_from_deepseek()
    print(f"DeepSeek returned {len(cards)} cards.\n")
    await insert_cards(cards)


if __name__ == "__main__":
    asyncio.run(main())
