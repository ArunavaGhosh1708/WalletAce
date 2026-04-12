"""
Phase 1 — Eligibility Filter tests

Each filter is tested independently, then combined.
"""

import pytest

from app.engine.eligibility import filter_eligible
from app.models.survey import FicoTier


class TestFicoFilter:
    def test_good_user_sees_good_card(self, card_csp, survey_optimizer):
        result = filter_eligible([card_csp], survey_optimizer)
        assert card_csp in result

    def test_good_user_blocked_from_excellent_card(self, card_csr, survey_optimizer):
        # survey_optimizer has fico_tier=670_739 (Good); CSR requires Excellent
        result = filter_eligible([card_csr], survey_optimizer)
        assert card_csr not in result

    def test_excellent_user_sees_all_tiers(
        self, card_csr, card_csp, card_secured, survey_524_triggered
    ):
        # survey_524_triggered has fico_tier=740_plus but 4 inquiries
        # CSR requires Excellent — should pass FICO (but fail 5/24)
        # CSP requires Good — passes
        # Secured requires Poor — passes
        # Use a survey with 0 inquiries to isolate FICO only
        from tests.conftest import _base_survey
        from app.models.survey import FicoTier

        survey = _base_survey(fico_tier=FicoTier.tier_740_plus, recent_inquiries_6m=0)
        result = filter_eligible([card_csr, card_csp, card_secured], survey)
        assert card_csr in result
        assert card_csp in result
        assert card_secured in result

    def test_poor_user_only_sees_poor_cards(
        self, card_secured, card_csp, survey_rebuilder
    ):
        result = filter_eligible([card_secured, card_csp], survey_rebuilder)
        assert card_secured in result
        assert card_csp not in result


class TestChase524Rule:
    def test_524_blocks_chase_card_at_3_plus_inquiries(
        self, card_csp, survey_524_triggered
    ):
        # card_csp has issuer_rule_524=True; survey has 4 recent inquiries
        result = filter_eligible([card_csp], survey_524_triggered)
        assert card_csp not in result

    def test_524_allows_non_chase_card_regardless_of_inquiries(
        self, card_bcp, survey_524_triggered
    ):
        # BCP is Amex, issuer_rule_524=False — not blocked by 5/24
        result = filter_eligible([card_bcp], survey_524_triggered)
        assert card_bcp in result

    def test_524_allows_chase_card_under_3_inquiries(self, card_csp, survey_optimizer):
        # survey_optimizer has recent_inquiries_6m=1 — passes 5/24
        result = filter_eligible([card_csp], survey_optimizer)
        assert card_csp in result

    def test_524_boundary_exactly_3_inquiries_is_blocked(self, card_csp):
        from tests.conftest import _base_survey
        survey = _base_survey(
            fico_tier=FicoTier.tier_740_plus, recent_inquiries_6m=3
        )
        result = filter_eligible([card_csp], survey)
        assert card_csp not in result


class TestIncomeFilter:
    def test_card_with_no_income_minimum_always_passes(
        self, card_csp, survey_optimizer
    ):
        # card_csp has income_minimum=None
        result = filter_eligible([card_csp], survey_optimizer)
        assert card_csp in result

    def test_card_blocked_when_income_below_minimum(self, card_csp):
        from tests.conftest import _base_survey
        card_csp.income_minimum = 100_000
        survey = _base_survey(annual_income=50_000)
        result = filter_eligible([card_csp], survey)
        assert card_csp not in result

    def test_card_passes_when_income_meets_minimum(self, card_csp):
        from tests.conftest import _base_survey
        card_csp.income_minimum = 50_000
        survey = _base_survey(annual_income=50_000)
        result = filter_eligible([card_csp], survey)
        assert card_csp in result


class TestIntroAPRFilter:
    def test_needs_intro_apr_blocks_card_with_zero_intro_months(
        self, card_csp, survey_balance_carrier
    ):
        # card_csp has intro_apr_months=0; survey_balance_carrier has needs_intro_apr=True
        result = filter_eligible([card_csp], survey_balance_carrier)
        assert card_csp not in result

    def test_needs_intro_apr_allows_card_with_intro_period(
        self, card_bcp, survey_balance_carrier
    ):
        # card_bcp has intro_apr_months=12
        result = filter_eligible([card_bcp], survey_balance_carrier)
        assert card_bcp in result

    def test_no_intro_apr_need_allows_all_cards(
        self, card_csp, card_bcp, survey_optimizer
    ):
        # survey_optimizer has needs_intro_apr=False — both cards pass
        result = filter_eligible([card_csp, card_bcp], survey_optimizer)
        assert card_csp in result
        assert card_bcp in result


class TestCombinedFilters:
    def test_empty_catalogue_returns_empty(self, survey_optimizer):
        assert filter_eligible([], survey_optimizer) == []

    def test_all_filters_applied_in_sequence(
        self, card_csr, card_csp, card_bcp, card_secured
    ):
        from tests.conftest import _base_survey
        # Good tier, 1 inquiry, no intro APR need, income 75k
        survey = _base_survey(
            fico_tier=FicoTier.tier_670_739,
            recent_inquiries_6m=1,
            needs_intro_apr=False,
            annual_income=75_000,
        )
        result = filter_eligible(
            [card_csr, card_csp, card_bcp, card_secured], survey
        )
        assert card_csr not in result   # Excellent required
        assert card_csp in result       # Good required, passes
        assert card_bcp in result       # Good required, passes
        assert card_secured in result   # Poor required, passes
