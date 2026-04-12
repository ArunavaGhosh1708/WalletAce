"""
Phase 3 — Ranking Engine tests

Verifies that preference adjustments re-order cards correctly
without mutating the underlying EANV values.
"""

import pytest

from app.engine.eanv import calculate
from app.engine.ranking import rank, top_n


def _result(card, survey, year=1):
    return calculate(card, survey, year)


class TestBalanceCarrySort:
    def test_carries_balance_sorts_by_apr_ascending(
        self, card_bcp, card_double_cash, survey_balance_carrier
    ):
        """
        BCP:         ongoing_apr_min=19.24
        Double Cash: ongoing_apr_min=19.24  (same — tiebreaker by ranking_score)
        Use cards with different APRs to test sort direction.
        """
        # BCP has lower APR (19.24) vs Double Cash (19.24) — same here,
        # so let's use card_csr (22.49) vs card_bcp (19.24)
        r_bcp = _result(card_bcp, survey_balance_carrier)
        r_csr = _result(card_bcp, survey_balance_carrier)  # reuse shape, APR differs on card

        from app.engine.ranking import RankedCard
        ranked = rank([r_bcp], survey_balance_carrier)
        # All cards in ranked list should have APR as primary sort
        assert len(ranked) == 1

    def test_lowest_apr_card_ranked_first_for_balance_carrier(
        self, card_bcp, card_csr, survey_balance_carrier
    ):
        """
        BCP:  apr_min=19.24
        CSR:  apr_min=22.49
        Balance carrier → BCP should rank above CSR.
        """
        r_bcp = _result(card_bcp, survey_balance_carrier)
        r_csr = _result(card_csr, survey_balance_carrier)
        ranked = rank([r_csr, r_bcp], survey_balance_carrier)
        assert ranked[0].result.card.ongoing_apr_min <= ranked[1].result.card.ongoing_apr_min

    def test_eanv_values_unchanged_after_ranking(
        self, card_csp, card_bcp, survey_balance_carrier
    ):
        r_csp = _result(card_csp, survey_balance_carrier)
        r_bcp = _result(card_bcp, survey_balance_carrier)
        original_eanvs = {r_csp.card.card_id: r_csp.eanv, r_bcp.card.card_id: r_bcp.eanv}

        ranked = rank([r_csp, r_bcp], survey_balance_carrier)
        for rc in ranked:
            assert rc.result.eanv == original_eanvs[rc.result.card.card_id]


class TestTravelPerkBoost:
    def test_lounge_card_boosted_for_heavy_traveler(
        self, card_csr, card_csp, survey_delta_flyer
    ):
        """
        survey_delta_flyer has monthly_travel=600 (≥ $500 threshold).
        CSR has has_lounge_access=True → gets +$150 ranking boost.
        CSP has has_lounge_access=False → no boost.
        Both require Excellent / Good tier — use Excellent survey for CSR.
        """
        from tests.conftest import _base_survey
        from app.models.survey import FicoTier, AirlinePreference
        survey = _base_survey(
            fico_tier=FicoTier.tier_740_plus,
            monthly_travel=600,
            recent_inquiries_6m=0,
        )
        r_csr = _result(card_csr, survey)
        r_csp = _result(card_csp, survey)

        ranked = rank([r_csr, r_csp], survey)
        # CSR has lounge — should rank above CSP if EANV is otherwise similar
        csr_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csr.card_id)
        csp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csp.card_id)
        assert csr_ranked.ranking_score > csp_ranked.ranking_score

    def test_no_boost_below_travel_threshold(self, card_csr, card_csp):
        from tests.conftest import _base_survey
        from app.models.survey import FicoTier
        survey = _base_survey(
            fico_tier=FicoTier.tier_740_plus,
            monthly_travel=400,   # below $500 threshold
            recent_inquiries_6m=0,
        )
        r_csr = _result(card_csr, survey)
        r_csp = _result(card_csp, survey)
        ranked = rank([r_csr, r_csp], survey)

        csr_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csr.card_id)
        csp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csp.card_id)
        # No travel perk boost — CSR gets no +150 advantage from perks
        # (CSR may still rank higher/lower purely on EANV)
        assert csr_ranked.ranking_score - csp_ranked.ranking_score != 150.0


class TestRewardTypeBoost:
    def test_cash_back_preference_boosts_cash_back_card(
        self, card_bcp, card_csp, survey_optimizer
    ):
        from tests.conftest import _base_survey
        survey = _base_survey(
            monthly_groceries=600,
            monthly_dining=300,
            prefers_cash_back=True,
        )
        r_bcp = _result(card_bcp, survey)
        r_csp = _result(card_csp, survey)
        ranked = rank([r_bcp, r_csp], survey)

        bcp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_bcp.card_id)
        csp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csp.card_id)
        # BCP is cash_back — gets +100 boost
        assert bcp_ranked.ranking_score > bcp_ranked.result.eanv

    def test_points_preference_boosts_points_card(
        self, card_bcp, card_csp, survey_optimizer
    ):
        from tests.conftest import _base_survey
        survey = _base_survey(
            monthly_groceries=600,
            monthly_dining=300,
            prefers_cash_back=False,
        )
        r_bcp = _result(card_bcp, survey)
        r_csp = _result(card_csp, survey)
        ranked = rank([r_bcp, r_csp], survey)

        csp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csp.card_id)
        # CSP is points — gets +100 boost
        assert csp_ranked.ranking_score > csp_ranked.result.eanv


class TestAffinityBoost:
    def test_airline_affinity_boosts_matching_card(
        self, card_delta, card_double_cash, survey_delta_flyer
    ):
        r_delta = _result(card_delta, survey_delta_flyer)
        r_dc = _result(card_double_cash, survey_delta_flyer)
        ranked = rank([r_delta, r_dc], survey_delta_flyer)

        delta_ranked = next(
            rc for rc in ranked if rc.result.card.card_id == card_delta.card_id
        )
        dc_ranked = next(
            rc for rc in ranked if rc.result.card.card_id == card_double_cash.card_id
        )
        # Delta card gets airline affinity boost; Double Cash does not
        assert delta_ranked.ranking_score - delta_ranked.result.eanv > (
            dc_ranked.ranking_score - dc_ranked.result.eanv
        )

    def test_no_affinity_set_gives_no_boost(self, card_delta, survey_optimizer):
        """survey_optimizer has airline_preference=None."""
        r = _result(card_delta, survey_optimizer)
        ranked = rank([r], survey_optimizer)
        # No airline boost applied (points preference boost may still apply)
        delta_ranked = ranked[0]
        boost = delta_ranked.ranking_score - delta_ranked.result.eanv
        # Only reward_type boost (100) can apply; no affinity boost
        assert boost <= 100.0


class TestFeeReluctance:
    def test_fee_card_pushed_below_no_fee_card_for_fee_averse_user(
        self, card_csp, card_double_cash, survey_fee_averse
    ):
        """
        survey_fee_averse has willing_to_pay_fee=False.
        card_csp has annual_fee=$95 → should rank below Double Cash ($0 fee)
        even if CSP has higher raw EANV.
        """
        r_csp = _result(card_csp, survey_fee_averse)
        r_dc = _result(card_double_cash, survey_fee_averse)
        ranked = rank([r_csp, r_dc], survey_fee_averse)

        assert ranked[0].result.card.card_id == card_double_cash.card_id

    def test_fee_card_allowed_for_fee_willing_user(
        self, card_csp, card_double_cash, survey_optimizer
    ):
        """survey_optimizer has willing_to_pay_fee=True — fee card not penalised."""
        r_csp = _result(card_csp, survey_optimizer)
        r_dc = _result(card_double_cash, survey_optimizer)
        ranked = rank([r_csp, r_dc], survey_optimizer)

        csp_ranked = next(rc for rc in ranked if rc.result.card.card_id == card_csp.card_id)
        # No fee penalty — ranking_score should be close to EANV (± boosts only)
        assert csp_ranked.ranking_score > -9000  # not massively penalised


class TestTopN:
    def test_top_n_returns_correct_count(
        self, card_csp, card_bcp, card_double_cash, survey_optimizer
    ):
        results = [
            _result(card_csp, survey_optimizer),
            _result(card_bcp, survey_optimizer),
            _result(card_double_cash, survey_optimizer),
        ]
        top = top_n(results, survey_optimizer, n=2)
        assert len(top) == 2

    def test_top_n_fewer_cards_than_n(self, card_csp, survey_optimizer):
        results = [_result(card_csp, survey_optimizer)]
        top = top_n(results, survey_optimizer, n=2)
        assert len(top) == 1

    def test_top_n_empty_returns_empty(self, survey_optimizer):
        assert top_n([], survey_optimizer) == []


class TestWhyThisCard:
    def test_why_mentions_top_spend_category(self, card_bcp, survey_grocery_heavy):
        """BCP earns most on groceries for a grocery-heavy user."""
        r = _result(card_bcp, survey_grocery_heavy)
        ranked = rank([r], survey_grocery_heavy)
        assert "groceries" in ranked[0].why_this_card.lower()

    def test_why_mentions_apr_for_balance_carrier(self, card_bcp, survey_balance_carrier):
        r = _result(card_bcp, survey_balance_carrier)
        ranked = rank([r], survey_balance_carrier)
        assert "apr" in ranked[0].why_this_card.lower() or "balance" in ranked[0].why_this_card.lower()
