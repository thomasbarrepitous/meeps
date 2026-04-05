"""Tests for teams parser functionality."""

import pytest
from unittest.mock import patch

import meeps as lp
from meeps.parsers.teams_parser import (
    Team,
    get_teams,
    get_team_by_name,
    get_team_by_short,
    get_teams_by_region,
    get_active_teams,
    get_disbanded_teams,
    search_teams,
    _parse_bool,
)

from .conftest import (
    TestConstants,
    assert_valid_dataclass_instance,
    assert_mock_called_with_table,
)


class TestTeamDataclass:
    """Test Team dataclass functionality and computed properties."""

    @pytest.mark.unit
    def test_team_initialization(self):
        """Test Team dataclass can be initialized with all fields."""
        team = Team(
            name="T1",
            short="T1",
            region="Korea",
            link="T1",
            overview_page="T1",
            image="T1logo.png",
            is_disbanded=False,
            renamed_to=None,
            location="Seoul",
        )

        assert_valid_dataclass_instance(team, Team, ["name", "short", "region"])
        assert team.name == "T1"
        assert team.short == "T1"
        assert team.region == "Korea"

    @pytest.mark.unit
    def test_team_is_active_when_not_disbanded(self):
        """Test is_active returns True for non-disbanded teams."""
        team = Team(name="T1", is_disbanded=False, renamed_to=None)
        assert team.is_active is True

    @pytest.mark.unit
    def test_team_is_active_when_disbanded(self):
        """Test is_active returns False for disbanded teams."""
        team = Team(name="Old Team", is_disbanded=True)
        assert team.is_active is False

    @pytest.mark.unit
    def test_team_is_active_when_renamed(self):
        """Test is_active returns False for renamed teams."""
        team = Team(name="Old Name", is_disbanded=False, renamed_to="New Name")
        assert team.is_active is False

    @pytest.mark.unit
    def test_team_display_name_with_full_name(self):
        """Test display_name returns full name when available."""
        team = Team(name="T1 Esports", short="T1")
        assert team.display_name == "T1 Esports"

    @pytest.mark.unit
    def test_team_display_name_fallback_to_short(self):
        """Test display_name falls back to short name."""
        team = Team(name=None, short="T1")
        assert team.display_name == "T1"

    @pytest.mark.unit
    def test_team_trigram_alias(self):
        """Test trigram is an alias for short."""
        team = Team(short="GEN")
        assert team.trigram == "GEN"

    @pytest.mark.unit
    def test_team_has_rebranded_true(self):
        """Test has_rebranded returns True when renamed_to is set."""
        team = Team(name="Old Name", renamed_to="New Name")
        assert team.has_rebranded is True

    @pytest.mark.unit
    def test_team_has_rebranded_false(self):
        """Test has_rebranded returns False when not renamed."""
        team = Team(name="T1", renamed_to=None)
        assert team.has_rebranded is False

    @pytest.mark.unit
    def test_team_has_rebranded_empty_string(self):
        """Test has_rebranded returns False for empty string."""
        team = Team(name="T1", renamed_to="")
        assert team.has_rebranded is False

    @pytest.mark.unit
    def test_team_default_values(self):
        """Test Team with default None values."""
        team = Team()
        assert team.name is None
        assert team.short is None
        assert team.is_disbanded is None
        assert team.is_active is True  # Default behavior


class TestParseBool:
    """Test the _parse_bool helper function."""

    @pytest.mark.unit
    def test_parse_bool_yes(self):
        """Test parsing 'Yes' as True."""
        assert _parse_bool("Yes") is True
        assert _parse_bool("yes") is True

    @pytest.mark.unit
    def test_parse_bool_true(self):
        """Test parsing 'true' and '1' as True."""
        assert _parse_bool("true") is True
        assert _parse_bool("1") is True

    @pytest.mark.unit
    def test_parse_bool_false_values(self):
        """Test parsing other values as False/None."""
        assert _parse_bool("No") is False
        assert _parse_bool("0") is False
        assert _parse_bool("") is None
        assert _parse_bool(None) is None

    @pytest.mark.unit
    def test_parse_bool_already_bool(self):
        """Test that actual booleans pass through."""
        assert _parse_bool(True) is True
        assert _parse_bool(False) is False


class TestTeamsAPI:
    """Test teams API functions with mocked data."""

    @pytest.mark.integration
    def test_get_teams_basic_call(self, mock_leaguepedia_query, teams_mock_data):
        """Test basic get_teams call returns properly parsed Team objects."""
        mock_leaguepedia_query.return_value = teams_mock_data

        teams = get_teams()

        assert len(teams) == 3
        assert all(isinstance(t, Team) for t in teams)
        assert teams[0].name == "T1"
        assert_mock_called_with_table(mock_leaguepedia_query, "Teams")

    @pytest.mark.integration
    def test_get_teams_with_region_filter(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_teams with region filter."""
        mock_leaguepedia_query.return_value = [teams_mock_data[0], teams_mock_data[1]]

        teams = get_teams(region="Korea")

        assert len(teams) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Korea" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_teams_exclude_disbanded(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_teams excluding disbanded teams."""
        mock_leaguepedia_query.return_value = teams_mock_data[:2]

        teams = get_teams(include_disbanded=False)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "IsDisbanded" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_teams_exclude_renamed(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_teams excluding renamed teams."""
        mock_leaguepedia_query.return_value = teams_mock_data[:2]

        teams = get_teams(include_renamed=False)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "RenamedTo" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_teams_with_limit(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_teams with limit parameter."""
        mock_leaguepedia_query.return_value = teams_mock_data

        teams = get_teams(limit=2)

        assert len(teams) == 2

    @pytest.mark.integration
    def test_get_team_by_name(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_team_by_name returns single team."""
        mock_leaguepedia_query.return_value = [teams_mock_data[0]]

        team = get_team_by_name("T1")

        assert team is not None
        assert team.name == "T1"

    @pytest.mark.integration
    def test_get_team_by_name_not_found(self, mock_leaguepedia_query):
        """Test get_team_by_name returns None when not found."""
        mock_leaguepedia_query.return_value = []

        team = get_team_by_name("NonexistentTeam")

        assert team is None

    @pytest.mark.integration
    def test_get_team_by_short(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_team_by_short returns single team."""
        mock_leaguepedia_query.return_value = [teams_mock_data[1]]

        team = get_team_by_short("GEN")

        assert team is not None
        assert team.short == "GEN"

    @pytest.mark.integration
    def test_get_teams_by_region(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_teams_by_region convenience function."""
        mock_leaguepedia_query.return_value = [teams_mock_data[0], teams_mock_data[1]]

        teams = get_teams_by_region("Korea")

        assert len(teams) == 2

    @pytest.mark.integration
    def test_get_active_teams(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_active_teams excludes disbanded and renamed."""
        mock_leaguepedia_query.return_value = teams_mock_data[:2]

        teams = get_active_teams()

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "IsDisbanded" in call_kwargs["where"]
        assert "RenamedTo" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_disbanded_teams(self, mock_leaguepedia_query, teams_mock_data):
        """Test get_disbanded_teams returns only disbanded teams."""
        disbanded_team = teams_mock_data[2]
        mock_leaguepedia_query.return_value = [disbanded_team]

        teams = get_disbanded_teams()

        assert len(teams) == 1
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "IsDisbanded='Yes'" in call_kwargs["where"]

    @pytest.mark.integration
    def test_search_teams(self, mock_leaguepedia_query, teams_mock_data):
        """Test search_teams with LIKE matching."""
        mock_leaguepedia_query.return_value = [teams_mock_data[0]]

        teams = search_teams("T1")

        assert len(teams) == 1
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "LIKE" in call_kwargs["where"]

    @pytest.mark.integration
    def test_search_teams_with_region(self, mock_leaguepedia_query, teams_mock_data):
        """Test search_teams with region filter."""
        mock_leaguepedia_query.return_value = [teams_mock_data[0]]

        teams = search_teams("T1", region="Korea")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "LIKE" in call_kwargs["where"]
        assert "Korea" in call_kwargs["where"]


class TestTeamsErrorHandling:
    """Test error handling in teams functionality."""

    @pytest.mark.integration
    def test_get_teams_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch teams"):
            get_teams()

    @pytest.mark.integration
    def test_get_team_by_name_api_error(self, mock_leaguepedia_query):
        """Test get_team_by_name error handling."""
        mock_leaguepedia_query.side_effect = Exception("API error")

        with pytest.raises(RuntimeError, match="Failed to fetch team by name"):
            get_team_by_name("T1")

    @pytest.mark.integration
    def test_get_teams_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []

        teams = get_teams()

        assert teams == []
        assert isinstance(teams, list)


class TestTeamsSQLInjection:
    """Test SQL injection protection."""

    @pytest.mark.integration
    def test_teams_sql_injection_protection(self, mock_leaguepedia_query, teams_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "'; DROP TABLE Teams; --"
        get_teams(region=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]

    @pytest.mark.integration
    def test_search_teams_sql_injection_protection(self, mock_leaguepedia_query):
        """Test search_teams escapes SQL injection."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "T1'; DROP TABLE Teams; --"
        search_teams(malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]


class TestTeamsImports:
    """Test that teams functions are properly importable."""

    @pytest.mark.unit
    def test_teams_functions_importable(self):
        """Test that all teams functions are available in the main module."""
        expected_functions = [
            "get_teams",
            "get_team_by_name",
            "get_team_by_short",
            "get_teams_by_region",
            "get_active_teams",
            "get_disbanded_teams",
            "search_teams",
        ]

        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_team_dataclass_importable(self):
        """Test that Team dataclass is importable from main module."""
        assert hasattr(lp, "Team")


if __name__ == "__main__":
    pytest.main([__file__])
