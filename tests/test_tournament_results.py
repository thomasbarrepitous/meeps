"""Tests for the TournamentResults parser module."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from meeps.parsers.tournament_results_parser import (
    TournamentResult,
    get_tournament_results,
    get_team_tournament_history,
    get_tournament_placements,
    get_tournament_winners,
    get_prize_earnings,
    _parse_tournament_result_data,
)


class TestTournamentResultDataclass:
    """Tests for the TournamentResult dataclass."""

    def test_default_initialization(self):
        """Test default values for TournamentResult."""
        result = TournamentResult()
        assert result.event is None
        assert result.team is None
        assert result.place is None
        assert result.place_number is None
        assert result.prize is None
        assert result.prize_usd is None

    def test_full_initialization(self):
        """Test TournamentResult with all fields populated."""
        result = TournamentResult(
            event="Worlds 2023",
            team="T1",
            place="1st",
            place_number=1,
            overview_page="Worlds/2023",
            tier="Major",
            prize=500000,
            prize_usd=500000.0,
            prize_unit="USD",
        )
        assert result.event == "Worlds 2023"
        assert result.team == "T1"
        assert result.place_number == 1

    def test_is_winner_true(self):
        """Test is_winner returns True for first place."""
        result = TournamentResult(place_number=1)
        assert result.is_winner is True

    def test_is_winner_false(self):
        """Test is_winner returns False for non-first place."""
        result = TournamentResult(place_number=2)
        assert result.is_winner is False

    def test_is_winner_none(self):
        """Test is_winner returns False when place_number is None."""
        result = TournamentResult(place_number=None)
        assert result.is_winner is False

    def test_is_top_4_first(self):
        """Test is_top_4 for first place."""
        result = TournamentResult(place_number=1)
        assert result.is_top_4 is True

    def test_is_top_4_fourth(self):
        """Test is_top_4 for fourth place."""
        result = TournamentResult(place_number=4)
        assert result.is_top_4 is True

    def test_is_top_4_fifth(self):
        """Test is_top_4 for fifth place."""
        result = TournamentResult(place_number=5)
        assert result.is_top_4 is False

    def test_is_top_4_none(self):
        """Test is_top_4 when place_number is None."""
        result = TournamentResult(place_number=None)
        assert result.is_top_4 is False

    def test_has_prize_with_prize(self):
        """Test has_prize with prize value."""
        result = TournamentResult(prize=50000)
        assert result.has_prize is True

    def test_has_prize_with_prize_usd(self):
        """Test has_prize with prize_usd value."""
        result = TournamentResult(prize_usd=50000.0)
        assert result.has_prize is True

    def test_has_prize_no_prize(self):
        """Test has_prize with no prize data."""
        result = TournamentResult()
        assert result.has_prize is False

    def test_prize_display_usd(self):
        """Test prize_display with USD value."""
        result = TournamentResult(prize_usd=50000.0)
        assert result.prize_display == "$50,000 USD"

    def test_prize_display_local_currency(self):
        """Test prize_display with local currency."""
        result = TournamentResult(prize=1000000, prize_unit="KRW")
        assert result.prize_display == "1,000,000 KRW"

    def test_prize_display_no_unit(self):
        """Test prize_display with no unit."""
        result = TournamentResult(prize=50000)
        assert result.prize_display == "50,000"

    def test_prize_display_none(self):
        """Test prize_display with no prize data."""
        result = TournamentResult()
        assert result.prize_display is None


class TestParseTournamentResultData:
    """Tests for the _parse_tournament_result_data function."""

    def test_parse_complete_data(self, tournament_results_mock_data):
        """Test parsing complete tournament result data."""
        result = _parse_tournament_result_data(tournament_results_mock_data[0])
        assert result.event == "Worlds 2023"
        assert result.team == "T1"
        assert result.place_number == 1
        assert result.prize_usd == 500000.0

    def test_parse_empty_data(self):
        """Test parsing empty data."""
        result = _parse_tournament_result_data({})
        assert result.event is None
        assert result.team is None
        assert result.place_number is None

    def test_parse_partial_data(self):
        """Test parsing partial data."""
        data = {"Event": "LCK Finals", "Team": "GenG", "Place": "2nd"}
        result = _parse_tournament_result_data(data)
        assert result.event == "LCK Finals"
        assert result.team == "GenG"
        assert result.place == "2nd"
        assert result.place_number is None


class TestGetTournamentResults:
    """Tests for the get_tournament_results function."""

    def test_get_tournament_results_no_filters(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting all tournament results without filters."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_results()
        assert len(result) == 2
        mock_leaguepedia_query.assert_called_once()

    def test_get_tournament_results_with_team(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test filtering by team."""
        mock_leaguepedia_query.return_value = [tournament_results_mock_data[0]]
        result = get_tournament_results(team="T1")
        assert len(result) == 1
        assert result[0].team == "T1"

    def test_get_tournament_results_with_overview_page(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test filtering by overview page."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_results(overview_page="Worlds/2023")
        assert len(result) == 2

    def test_get_tournament_results_with_tier(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test filtering by tier."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_results(tier="Major")
        assert len(result) == 2

    def test_get_tournament_results_with_limit(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test applying limit."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_results(limit=1)
        assert len(result) == 1

    def test_get_tournament_results_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch tournament results"):
            get_tournament_results()


class TestGetTeamTournamentHistory:
    """Tests for the get_team_tournament_history function."""

    def test_get_team_tournament_history(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting tournament history for a specific team."""
        mock_leaguepedia_query.return_value = [tournament_results_mock_data[0]]
        result = get_team_tournament_history("T1")
        assert len(result) == 1
        assert result[0].team == "T1"

    def test_get_team_tournament_history_with_tier(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting tournament history with tier filter."""
        mock_leaguepedia_query.return_value = [tournament_results_mock_data[0]]
        result = get_team_tournament_history("T1", tier="Major")
        assert len(result) == 1


class TestGetTournamentPlacements:
    """Tests for the get_tournament_placements function."""

    def test_get_tournament_placements(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting all placements for a tournament."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_placements("Worlds/2023")
        assert len(result) == 2
        call_args = mock_leaguepedia_query.call_args
        assert "Place_Number ASC" in call_args[1]["order_by"]

    def test_get_tournament_placements_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch tournament placements"):
            get_tournament_placements("Worlds/2023")


class TestGetTournamentWinners:
    """Tests for the get_tournament_winners function."""

    def test_get_tournament_winners_no_filter(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting tournament winners without tier filter."""
        mock_leaguepedia_query.return_value = [tournament_results_mock_data[0]]
        result = get_tournament_winners()
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "Place_Number='1'" in call_args[1]["where"]

    def test_get_tournament_winners_with_tier(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test getting tournament winners with tier filter."""
        mock_leaguepedia_query.return_value = [tournament_results_mock_data[0]]
        result = get_tournament_winners(tier="Major")
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "Major" in call_args[1]["where"]

    def test_get_tournament_winners_with_limit(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test applying limit to tournament winners."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_tournament_winners(limit=1)
        assert len(result) == 1

    def test_get_tournament_winners_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch tournament winners"):
            get_tournament_winners()


class TestGetPrizeEarnings:
    """Tests for the get_prize_earnings function."""

    def test_get_prize_earnings(
        self, mock_leaguepedia_query, tournament_results_mock_data
    ):
        """Test calculating total prize earnings."""
        mock_leaguepedia_query.return_value = tournament_results_mock_data
        result = get_prize_earnings("T1")
        assert result == 700000.0  # 500000 + 200000

    def test_get_prize_earnings_no_prizes(self, mock_leaguepedia_query):
        """Test prize earnings with no prizes."""
        mock_leaguepedia_query.return_value = []
        result = get_prize_earnings("SomeTeam")
        assert result == 0.0

    def test_get_prize_earnings_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch prize earnings"):
            get_prize_earnings("T1")
