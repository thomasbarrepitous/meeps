"""Tests for match schedule parser functionality."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

import meeps as mp
from meeps.parsers.match_schedule_parser import (
    MatchSchedule,
    get_match_schedule,
    get_upcoming_matches,
    get_recent_results,
    get_team_schedule,
    get_tournament_schedule,
    get_today_matches,
    get_head_to_head,
    _parse_int,
    _parse_bool,
    _parse_datetime,
)

from .conftest import (
    TestConstants,
    assert_valid_dataclass_instance,
    assert_mock_called_with_table,
)


class TestMatchScheduleDataclass:
    """Test MatchSchedule dataclass functionality and computed properties."""

    @pytest.mark.unit
    def test_match_schedule_initialization(self):
        """Test MatchSchedule dataclass can be initialized with all fields."""
        match = MatchSchedule(
            team1="T1",
            team2="GenG",
            datetime_utc=datetime(2024, 8, 15, 10, 0, tzinfo=timezone.utc),
            overview_page="LCK/2024 Season/Summer Season",
            best_of=3,
            winner="1",
            team1_score=2,
            team2_score=1,
        )

        assert_valid_dataclass_instance(
            match, MatchSchedule, ["team1", "team2", "datetime_utc"]
        )
        assert match.team1 == "T1"
        assert match.team2 == "GenG"
        assert match.best_of == 3

    @pytest.mark.unit
    def test_is_upcoming_future_match(self):
        """Test is_upcoming returns True for future matches."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=24)
        match = MatchSchedule(datetime_utc=future_time)
        assert match.is_upcoming is True

    @pytest.mark.unit
    def test_is_upcoming_past_match(self):
        """Test is_upcoming returns False for past matches."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=24)
        match = MatchSchedule(datetime_utc=past_time)
        assert match.is_upcoming is False

    @pytest.mark.unit
    def test_is_upcoming_no_datetime(self):
        """Test is_upcoming returns None when datetime is not set."""
        match = MatchSchedule()
        assert match.is_upcoming is None

    @pytest.mark.unit
    def test_is_completed_with_winner(self):
        """Test is_completed returns True when winner is set."""
        match = MatchSchedule(winner="1")
        assert match.is_completed is True

    @pytest.mark.unit
    def test_is_completed_no_winner(self):
        """Test is_completed returns False when no winner."""
        match = MatchSchedule(winner=None)
        assert match.is_completed is False

    @pytest.mark.unit
    def test_is_completed_empty_winner(self):
        """Test is_completed returns False for empty winner string."""
        match = MatchSchedule(winner="")
        assert match.is_completed is False

    @pytest.mark.unit
    def test_is_live_match_in_progress(self):
        """Test is_live returns True for potentially live matches."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        match = MatchSchedule(datetime_utc=past_time, winner=None)
        assert match.is_live is True

    @pytest.mark.unit
    def test_is_live_completed_match(self):
        """Test is_live returns False for completed matches."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        match = MatchSchedule(datetime_utc=past_time, winner="1")
        assert match.is_live is False

    @pytest.mark.unit
    def test_is_live_future_match(self):
        """Test is_live returns False for future matches."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        match = MatchSchedule(datetime_utc=future_time, winner=None)
        assert match.is_live is False

    @pytest.mark.unit
    def test_hours_until_match_future(self):
        """Test hours_until_match for future match."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=5)
        match = MatchSchedule(datetime_utc=future_time)
        assert match.hours_until_match is not None
        assert abs(match.hours_until_match - 5) < 0.1

    @pytest.mark.unit
    def test_hours_until_match_past(self):
        """Test hours_until_match returns negative for past match."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=3)
        match = MatchSchedule(datetime_utc=past_time)
        assert match.hours_until_match is not None
        assert abs(match.hours_until_match + 3) < 0.1

    @pytest.mark.unit
    def test_match_display(self):
        """Test match_display format."""
        match = MatchSchedule(team1="T1", team2="GenG")
        assert match.match_display == "T1 vs GenG"

    @pytest.mark.unit
    def test_match_display_tbd(self):
        """Test match_display with TBD teams."""
        match = MatchSchedule(team1=None, team2="GenG")
        assert match.match_display == "TBD vs GenG"

    @pytest.mark.unit
    def test_score_display(self):
        """Test score_display format."""
        match = MatchSchedule(team1_score=2, team2_score=1)
        assert match.score_display == "2-1"

    @pytest.mark.unit
    def test_score_display_no_scores(self):
        """Test score_display returns None without scores."""
        match = MatchSchedule()
        assert match.score_display is None


class TestParserHelpers:
    """Test parser helper functions."""

    @pytest.mark.unit
    def test_parse_int_valid(self):
        """Test _parse_int with valid values."""
        assert _parse_int("5") == 5
        assert _parse_int("123") == 123
        assert _parse_int("-5") == -5

    @pytest.mark.unit
    def test_parse_int_invalid(self):
        """Test _parse_int with invalid values."""
        assert _parse_int("") is None
        assert _parse_int(None) is None
        assert _parse_int("abc") is None

    @pytest.mark.unit
    def test_parse_bool_yes_values(self):
        """Test _parse_bool with yes/true values."""
        assert _parse_bool("Yes") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("true") is True
        assert _parse_bool("1") is True

    @pytest.mark.unit
    def test_parse_bool_no_values(self):
        """Test _parse_bool with no/false values."""
        assert _parse_bool("No") is False
        assert _parse_bool("") is None
        assert _parse_bool(None) is None

    @pytest.mark.unit
    def test_parse_datetime_iso(self):
        """Test _parse_datetime with ISO format."""
        result = _parse_datetime("2024-08-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 8
        assert result.tzinfo is not None

    @pytest.mark.unit
    def test_parse_datetime_invalid(self):
        """Test _parse_datetime with invalid values."""
        assert _parse_datetime(None) is None
        assert _parse_datetime("") is None
        assert _parse_datetime("invalid") is None


class TestMatchScheduleAPI:
    """Test match schedule API functions with mocked data."""

    @pytest.mark.integration
    def test_get_match_schedule_basic(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test basic get_match_schedule call."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        matches = get_match_schedule()

        assert len(matches) == 3
        assert all(isinstance(m, MatchSchedule) for m in matches)
        assert_mock_called_with_table(mock_leaguepedia_query, "MatchSchedule")

    @pytest.mark.integration
    def test_get_match_schedule_tournament_filter(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with tournament filter."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        get_match_schedule(tournament="LCK/2024 Season/Summer Season")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "OverviewPage" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_match_schedule_team_filter(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with team filter (OR condition)."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        get_match_schedule(team="T1")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Team1" in call_kwargs["where"]
        assert "Team2" in call_kwargs["where"]
        assert "OR" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_match_schedule_date_filter(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with date filters."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        get_match_schedule(start_date="2024-08-01", end_date="2024-08-31")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "DateTime_UTC >=" in call_kwargs["where"]
        assert "DateTime_UTC <=" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_match_schedule_completed_only(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with completed_only filter."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[0]]

        get_match_schedule(completed_only=True)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Winner IS NOT NULL" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_match_schedule_upcoming_only(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with upcoming_only filter."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[2]]

        get_match_schedule(upcoming_only=True)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Winner IS NULL" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_match_schedule_with_limit(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_match_schedule with limit parameter."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        matches = get_match_schedule(limit=2)

        assert len(matches) == 2

    @pytest.mark.integration
    def test_get_upcoming_matches(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_upcoming_matches convenience function."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[2]]

        matches = get_upcoming_matches(days_ahead=7)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "DateTime_UTC >=" in call_kwargs["where"]
        assert "Winner IS NULL" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_recent_results(self, mock_leaguepedia_query, match_schedule_mock_data):
        """Test get_recent_results convenience function."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[0]]

        matches = get_recent_results(days_back=7)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Winner IS NOT NULL" in call_kwargs["where"]
        assert "DESC" in call_kwargs["order_by"]

    @pytest.mark.integration
    def test_get_team_schedule(self, mock_leaguepedia_query, match_schedule_mock_data):
        """Test get_team_schedule convenience function."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data[:2]

        matches = get_team_schedule("T1")

        assert len(matches) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "T1" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_tournament_schedule(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_tournament_schedule function."""
        mock_leaguepedia_query.return_value = match_schedule_mock_data

        matches = get_tournament_schedule("LCK/2024 Season/Summer Season")

        assert len(matches) == 3
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "OverviewPage" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_tournament_schedule_with_round(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_tournament_schedule with round filter."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[0]]

        matches = get_tournament_schedule(
            "LCK/2024 Season/Summer Season", round_filter="Week 1"
        )

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Round" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_today_matches(self, mock_leaguepedia_query, match_schedule_mock_data):
        """Test get_today_matches function."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[1]]

        matches = get_today_matches()

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "DateTime_UTC >=" in call_kwargs["where"]
        assert "DateTime_UTC <=" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_head_to_head(self, mock_leaguepedia_query, match_schedule_mock_data):
        """Test get_head_to_head function."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[0]]

        matches = get_head_to_head("T1", "GenG")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        # Should have both team combinations
        assert "T1" in call_kwargs["where"]
        assert "GenG" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_head_to_head_with_tournament(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test get_head_to_head with tournament filter."""
        mock_leaguepedia_query.return_value = [match_schedule_mock_data[0]]

        matches = get_head_to_head(
            "T1", "GenG", tournament="LCK/2024 Season/Summer Season"
        )

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "OverviewPage" in call_kwargs["where"]


class TestMatchScheduleErrorHandling:
    """Test error handling in match schedule functionality."""

    @pytest.mark.integration
    def test_get_match_schedule_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch match schedule"):
            get_match_schedule()

    @pytest.mark.integration
    def test_get_tournament_schedule_api_error(self, mock_leaguepedia_query):
        """Test get_tournament_schedule error handling."""
        mock_leaguepedia_query.side_effect = Exception("API error")

        with pytest.raises(RuntimeError, match="Failed to fetch tournament schedule"):
            get_tournament_schedule("LCK/2024")

    @pytest.mark.integration
    def test_get_head_to_head_api_error(self, mock_leaguepedia_query):
        """Test get_head_to_head error handling."""
        mock_leaguepedia_query.side_effect = Exception("API error")

        with pytest.raises(RuntimeError, match="Failed to fetch head-to-head"):
            get_head_to_head("T1", "GenG")

    @pytest.mark.integration
    def test_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []

        matches = get_match_schedule()

        assert matches == []
        assert isinstance(matches, list)


class TestMatchScheduleSQLInjection:
    """Test SQL injection protection."""

    @pytest.mark.integration
    def test_tournament_sql_injection(
        self, mock_leaguepedia_query, match_schedule_mock_data
    ):
        """Test tournament parameter is escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "'; DROP TABLE MatchSchedule; --"
        get_match_schedule(tournament=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]

    @pytest.mark.integration
    def test_team_sql_injection(self, mock_leaguepedia_query, match_schedule_mock_data):
        """Test team parameter is escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "T1'; DROP TABLE MatchSchedule; --"
        get_match_schedule(team=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]

    @pytest.mark.integration
    def test_head_to_head_sql_injection(self, mock_leaguepedia_query):
        """Test head-to-head parameters are escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_team = "T1'; DROP TABLE MatchSchedule; --"
        get_head_to_head(malicious_team, "GenG")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]


class TestMatchScheduleImports:
    """Test that match schedule functions are properly importable."""

    @pytest.mark.unit
    def test_match_schedule_functions_importable(self):
        """Test that all match schedule functions are available in the main module."""
        expected_functions = [
            "get_match_schedule",
            "get_upcoming_matches",
            "get_recent_results",
            "get_team_schedule",
            "get_tournament_schedule",
            "get_today_matches",
            "get_head_to_head",
        ]

        for func_name in expected_functions:
            assert hasattr(mp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_match_schedule_dataclass_importable(self):
        """Test that MatchSchedule dataclass is importable from main module."""
        assert hasattr(mp, "MatchSchedule")


if __name__ == "__main__":
    pytest.main([__file__])
