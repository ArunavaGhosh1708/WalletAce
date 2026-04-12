"""
Phase 2 — EANV Calculator tests

All expected values hand-verified against the formula:
    reward = annual_spend × effective_rate × (cpp_cents / 100)
    EANV   = rewards_total + SB - AF
"""

import pytest

from app.engine.eanv import calculate, calculate_all


class TestEANVFormula:
    # ── Test 1: Chase Sapphire Preferred + Optimizer profile ──────────────────
    # Spend: groceries $600/mo, dining $300/mo, travel $500/mo
    # CSP:   cat_grocery=3.0, cat_dining=3.0, cat_travel=2.0, cpp=1.5, AF=95
    #
    # groceries : 600×12=7200  × 3.0 × (1.5/100) = 7200 × 0.045 = $324.00
    # dining    : 300×12=3600  × 3.0 × (1.5/100) = 3600 × 0.045 = $162.00
    # travel    : 500×12=6000  × 2.0 × (1.5/100) = 6000 × 0.030 = $180.00
    # rewards   : 324 + 162 + 180 = $666.00
    # Year 1    : 666 + 1125 - 95  = $1696.00
    # Year 2    : 666 + 0    - 95  = $571.00

    def test_csp_year1_eanv(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=1)
        assert result.eanv == pytest.approx(1696.00, abs=0.01)

    def test_csp_year2_eanv(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=2)
        assert result.eanv == pytest.approx(571.00, abs=0.01)

    def test_csp_rewards_total(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=1)
        assert result.rewards_total == pytest.approx(666.00, abs=0.01)

    def test_csp_category_breakdown(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=1)
        bd = result.breakdown
        assert bd.groceries == pytest.approx(324.00, abs=0.01)
        assert bd.dining == pytest.approx(162.00, abs=0.01)
        assert bd.travel == pytest.approx(180.00, abs=0.01)
        # Zero-spend categories earn 0
        assert bd.gas == pytest.approx(0.0, abs=0.01)
        assert bd.transit == pytest.approx(0.0, abs=0.01)

    # ── Test 2: Amex Blue Cash Preferred + Grocery-heavy profile ─────────────
    # Spend: groceries $1000/mo, streaming $50/mo, gas $200/mo
    # BCP:   cat_grocery=0.06, cat_streaming=0.06, cat_gas=0.03, cpp=100, AF=95
    #
    # groceries : 1000×12=12000 × 0.06 × (100/100) = 12000 × 0.06 = $720.00
    # streaming :   50×12=600   × 0.06 × (100/100) =   600 × 0.06 = $36.00
    # gas       :  200×12=2400  × 0.03 × (100/100) =  2400 × 0.03 = $72.00
    # rewards   : 720 + 36 + 72 = $828.00
    # Year 1    : 828 + 250 - 95 = $983.00
    # Year 2    : 828 + 0   - 95 = $733.00

    def test_bcp_year1_eanv(self, card_bcp, survey_grocery_heavy):
        result = calculate(card_bcp, survey_grocery_heavy, year=1)
        assert result.eanv == pytest.approx(983.00, abs=0.01)

    def test_bcp_year2_eanv(self, card_bcp, survey_grocery_heavy):
        result = calculate(card_bcp, survey_grocery_heavy, year=2)
        assert result.eanv == pytest.approx(733.00, abs=0.01)

    def test_bcp_category_breakdown(self, card_bcp, survey_grocery_heavy):
        result = calculate(card_bcp, survey_grocery_heavy, year=1)
        bd = result.breakdown
        assert bd.groceries == pytest.approx(720.00, abs=0.01)
        assert bd.streaming == pytest.approx(36.00, abs=0.01)
        assert bd.gas == pytest.approx(72.00, abs=0.01)

    # ── Test 3: Citi Double Cash + Simple profile ─────────────────────────────
    # Spend: groceries $500/mo, dining $200/mo
    # DC:    base=0.02, all cat_rates=0.02, cpp=100, AF=0
    #
    # groceries : 500×12=6000  × 0.02 × (100/100) = $120.00
    # dining    : 200×12=2400  × 0.02 × (100/100) = $48.00
    # rewards   : 120 + 48 = $168.00
    # Year 1    : 168 + 200 - 0 = $368.00
    # Year 2    : 168 + 0   - 0 = $168.00

    def test_double_cash_year1_eanv(self, card_double_cash, survey_simple):
        result = calculate(card_double_cash, survey_simple, year=1)
        assert result.eanv == pytest.approx(368.00, abs=0.01)

    def test_double_cash_year2_eanv(self, card_double_cash, survey_simple):
        result = calculate(card_double_cash, survey_simple, year=2)
        assert result.eanv == pytest.approx(168.00, abs=0.01)

    def test_double_cash_zero_annual_fee(self, card_double_cash, survey_simple):
        result = calculate(card_double_cash, survey_simple)
        assert result.annual_fee == 0.0


class TestBaseRateFallback:
    def test_zero_category_rate_falls_back_to_base(self, card_csp, survey_optimizer):
        """
        CSP has cat_gas_rate=1.0 (same as base), cat_online_retail_rate=1.0.
        If we set cat_gas_rate to 0.0, spend should fall back to base_rate=1.0.
        """
        card_csp.cat_gas_rate = 0.0
        # gas spend = 0 in survey_optimizer so result is 0 regardless
        # Use a survey with gas spend to verify fallback
        from tests.conftest import _base_survey
        survey = _base_survey(monthly_gas=200)
        result = calculate(card_csp, survey)
        # base_rate=1.0, cpp=1.5 → 200×12 × 1.0 × 1.5/100 = 2400 × 0.015 = $36.00
        assert result.breakdown.gas == pytest.approx(36.00, abs=0.01)


class TestSignUpBonus:
    def test_year1_includes_sub(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=1)
        assert result.signup_bonus_applied == pytest.approx(1125.00, abs=0.01)

    def test_year2_excludes_sub(self, card_csp, survey_optimizer):
        result = calculate(card_csp, survey_optimizer, year=2)
        assert result.signup_bonus_applied == pytest.approx(0.0, abs=0.01)

    def test_no_sub_card_unaffected_by_year(self, card_secured):
        from tests.conftest import _base_survey
        survey = _base_survey(monthly_dining=200)
        r1 = calculate(card_secured, survey, year=1)
        r2 = calculate(card_secured, survey, year=2)
        assert r1.signup_bonus_applied == 0.0
        assert r2.signup_bonus_applied == 0.0
        assert r1.eanv == r2.eanv


class TestNegativeEANV:
    def test_high_fee_card_with_zero_spend_has_negative_eanv(self, card_csr):
        """CSR costs $550/yr. With zero spend and no SUB in Year 2, EANV is negative."""
        from tests.conftest import _base_survey
        survey = _base_survey()  # all zero spend
        result = calculate(card_csr, survey, year=2)
        assert result.eanv < 0


class TestCalculateAll:
    def test_results_sorted_by_eanv_descending(
        self, card_csp, card_double_cash, survey_optimizer
    ):
        results = calculate_all([card_csp, card_double_cash], survey_optimizer, year=1)
        eanvs = [r.eanv for r in results]
        assert eanvs == sorted(eanvs, reverse=True)

    def test_empty_cards_returns_empty(self, survey_optimizer):
        assert calculate_all([], survey_optimizer) == []
