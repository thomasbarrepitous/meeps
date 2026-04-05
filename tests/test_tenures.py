"""Tests for the Tenures parser module."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from meeps.parsers.tenures_parser import (
    Tenure,
    get_tenures,
    get_player_tenures,
    get_team_tenures,
    get_current_roster_tenures,
    get_longest_tenures,
    _parse_tenure_data,
)


class TestTenureDataclass:
    """Tests for the Tenure dataclass."""

    def test_default_initialization(self):
        """Test default values for Tenure."""
        tenure = Tenure()
        assert tenure.player is None
        assert tenure.team is None
        assert tenure.date_join is None
        assert tenure.date_leave is None
        assert tenure.duration is None
        assert tenure.is_current is None

    def test_full_initialization(self):
        """Test Tenure with all fields populated."""
        tenure = Tenure(
            player="Faker",
            team="T1",
            date_join=datetime(2013, 2, 1, tzinfo=timezone.utc),
            date_leave=None,
            duration=4000,
            is_current=True,
            next_team=None,
            next_is_retired=False,
            contract_end="2025-12-31",
        )
        assert tenure.player == "Faker"
        assert tenure.team == "T1"
        assert tenure.duration == 4000

    def test_is_active_current_no_leave(self):
        """Test is_active returns True for current tenure with no leave date."""
        tenure = Tenure(is_current=True, date_leave=None)
        assert tenure.is_active is True

    def test_is_active_current_with_leave(self):
        """Test is_active returns False for current tenure with leave date."""
        tenure = Tenure(
            is_current=True,
            date_leave=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        assert tenure.is_active is False

    def test_is_active_not_current(self):
        """Test is_active returns False for non-current tenure."""
        tenure = Tenure(is_current=False, date_leave=None)
        assert tenure.is_active is False

    def test_is_active_none_current(self):
        """Test is_active returns False when is_current is None."""
        tenure = Tenure(is_current=None, date_leave=None)
        assert tenure.is_active is False

    def test_duration_months_calculation(self):
        """Test duration_months calculation."""
        tenure = Tenure(duration=365)
        assert tenure.duration_months == pytest.approx(12.0, abs=0.5)

    def test_duration_months_none(self):
        """Test duration_months returns None when duration is None."""
        tenure = Tenure(duration=None)
        assert tenure.duration_months is None

    def test_duration_years_calculation(self):
        """Test duration_years calculation."""
        tenure = Tenure(duration=730)
        assert tenure.duration_years == pytest.approx(2.0, abs=0.1)

    def test_duration_years_none(self):
        """Test duration_years returns None when duration is None."""
        tenure = Tenure(duration=None)
        assert tenure.duration_years is None

    def test_ended_in_retirement_true(self):
        """Test ended_in_retirement returns True when next_is_retired is True."""
        tenure = Tenure(next_is_retired=True)
        assert tenure.ended_in_retirement is True

    def test_ended_in_retirement_false(self):
        """Test ended_in_retirement returns False when next_is_retired is False."""
        tenure = Tenure(next_is_retired=False)
        assert tenure.ended_in_retirement is False

    def test_ended_in_retirement_none(self):
        """Test ended_in_retirement returns False when next_is_retired is None."""
        tenure = Tenure(next_is_retired=None)
        assert tenure.ended_in_retirement is False


class TestParseTenureData:
    """Tests for the _parse_tenure_data function."""

    def test_parse_complete_data(self, tenures_mock_data):
        """Test parsing complete tenure data."""
        result = _parse_tenure_data(tenures_mock_data[0])
        assert result.player == "Faker"
        assert result.team == "T1"
        assert result.duration == 4000
        assert result.is_current is True

    def test_parse_empty_data(self):
        """Test parsing empty data."""
        result = _parse_tenure_data({})
        assert result.player is None
        assert result.team is None
        assert result.duration is None

    def test_parse_partial_data(self):
        """Test parsing partial data."""
        data = {"Player": "Faker", "Team": "T1"}
        result = _parse_tenure_data(data)
        assert result.player == "Faker"
        assert result.team == "T1"
        assert result.duration is None


class TestGetTenures:
    """Tests for the get_tenures function."""

    def test_get_tenures_no_filters(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting all tenures without filters."""
        mock_leaguepedia_query.return_value = tenures_mock_data
        result = get_tenures()
        assert len(result) == 2
        mock_leaguepedia_query.assert_called_once()

    def test_get_tenures_with_player(self, mock_leaguepedia_query, tenures_mock_data):
        """Test filtering by player."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_tenures(player="Faker")
        assert len(result) == 1
        assert result[0].player == "Faker"

    def test_get_tenures_with_team(self, mock_leaguepedia_query, tenures_mock_data):
        """Test filtering by team."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_tenures(team="T1")
        assert len(result) == 1
        assert result[0].team == "T1"

    def test_get_tenures_current_only(self, mock_leaguepedia_query, tenures_mock_data):
        """Test filtering by current tenures only."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_tenures(current_only=True)
        assert len(result) == 1
        assert result[0].is_current is True

    def test_get_tenures_with_limit(self, mock_leaguepedia_query, tenures_mock_data):
        """Test applying limit."""
        mock_leaguepedia_query.return_value = tenures_mock_data
        result = get_tenures(limit=1)
        assert len(result) == 1

    def test_get_tenures_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch tenures"):
            get_tenures()


class TestGetPlayerTenures:
    """Tests for the get_player_tenures function."""

    def test_get_player_tenures(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting tenures for a specific player."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_player_tenures("Faker")
        assert len(result) == 1
        assert result[0].player == "Faker"


class TestGetTeamTenures:
    """Tests for the get_team_tenures function."""

    def test_get_team_tenures(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting tenures for a specific team."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_team_tenures("T1")
        assert len(result) == 1
        assert result[0].team == "T1"

    def test_get_team_tenures_current_only(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting current tenures for a team."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_team_tenures("T1", current_only=True)
        assert len(result) == 1


class TestGetCurrentRosterTenures:
    """Tests for the get_current_roster_tenures function."""

    def test_get_current_roster_tenures(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting current roster tenures for a team."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_current_roster_tenures("T1")
        assert len(result) == 1
        assert result[0].team == "T1"


class TestGetLongestTenures:
    """Tests for the get_longest_tenures function."""

    def test_get_longest_tenures_no_filter(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting longest tenures without team filter."""
        mock_leaguepedia_query.return_value = tenures_mock_data
        result = get_longest_tenures()
        assert len(result) == 2
        call_args = mock_leaguepedia_query.call_args
        assert "Duration DESC" in call_args[1]["order_by"]

    def test_get_longest_tenures_with_team(self, mock_leaguepedia_query, tenures_mock_data):
        """Test getting longest tenures for a specific team."""
        mock_leaguepedia_query.return_value = [tenures_mock_data[0]]
        result = get_longest_tenures(team="T1")
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "T1" in call_args[1]["where"]

    def test_get_longest_tenures_with_limit(self, mock_leaguepedia_query, tenures_mock_data):
        """Test applying limit to longest tenures."""
        mock_leaguepedia_query.return_value = tenures_mock_data
        result = get_longest_tenures(limit=1)
        assert len(result) == 1

    def test_get_longest_tenures_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch longest tenures"):
            get_longest_tenures()
