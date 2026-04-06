"""Unit tests for team_parser functionality with mocked data."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

import meeps as mp
from meeps.parsers.team_parser import (
    TeamAssets,
    TeamPlayer,
    get_active_players,
    get_team_logo,
    get_team_thumbnail,
    get_all_team_assets,
    get_long_team_name_from_trigram,
    _clean_player_name,
    _get_primary_valid_role,
    VALID_ROLES,
)

from .conftest import TestConstants


class TestDataFactory:
    """Factory for creating team parser test data."""

    @staticmethod
    def create_active_players_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for active players data."""
        return [
            {
                'Player': 'Zeus',
                'Team': 'T1',
                'DateJoin': '2022-01-01',
                'Roles': 'Top',
            },
            {
                'Player': 'Oner',
                'Team': 'T1',
                'DateJoin': '2021-01-01',
                'Roles': 'Jungle',
            },
            {
                'Player': 'Faker',
                'Team': 'T1',
                'DateJoin': '2013-01-01',
                'Roles': 'Mid;Part-Owner',
            },
            {
                'Player': 'Gumayusi',
                'Team': 'T1',
                'DateJoin': '2020-01-01',
                'Roles': 'Bot',
            },
            {
                'Player': 'Keria',
                'Team': 'T1',
                'DateJoin': '2021-01-01',
                'Roles': 'Support',
            },
        ]

    @staticmethod
    def create_player_with_real_name() -> List[Dict[str, Any]]:
        """Create mock with player real name in parentheses."""
        return [
            {
                'Player': 'Doran (Choi Hyeon-joon)',
                'Team': 'T1',
                'DateJoin': '2024-01-01',
                'Roles': 'Top',
            },
        ]


@pytest.fixture
def active_players_mock_data():
    """Provide active players mock data."""
    return TestDataFactory.create_active_players_mock_response()


@pytest.fixture
def player_with_real_name_mock():
    """Provide player with real name mock data."""
    return TestDataFactory.create_player_with_real_name()


class TestTeamParserImports:
    """Test that team parser functions are properly importable."""

    @pytest.mark.unit
    def test_team_functions_importable(self):
        """Test that all team functions are available in the main module."""
        expected_functions = [
            'get_active_players',
            'get_team_logo',
            'get_team_thumbnail',
            'get_all_team_assets',
            'get_long_team_name_from_trigram',
        ]

        for func_name in expected_functions:
            assert hasattr(mp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_team_dataclasses_importable(self):
        """Test that team dataclasses are importable."""
        assert hasattr(mp, 'TeamAssets')
        assert hasattr(mp, 'TeamPlayer')
        assert mp.TeamAssets is TeamAssets
        assert mp.TeamPlayer is TeamPlayer


class TestTeamPlayerDataclass:
    """Test TeamPlayer dataclass functionality."""

    @pytest.mark.unit
    def test_team_player_initialization(self):
        """Test TeamPlayer dataclass initialization."""
        player = TeamPlayer(name='Faker', role='Mid')

        assert player.name == 'Faker'
        assert player.role == 'Mid'

    @pytest.mark.unit
    def test_team_player_equality(self):
        """Test TeamPlayer equality comparison."""
        player1 = TeamPlayer(name='Faker', role='Mid')
        player2 = TeamPlayer(name='Faker', role='Mid')
        player3 = TeamPlayer(name='Chovy', role='Mid')

        assert player1 == player2
        assert player1 != player3


class TestTeamAssetsDataclass:
    """Test TeamAssets dataclass functionality."""

    @pytest.mark.unit
    def test_team_assets_initialization(self):
        """Test TeamAssets dataclass initialization."""
        assets = TeamAssets(
            thumbnail_url='https://example.com/thumb.png',
            logo_url='https://example.com/logo.png',
            long_name='T1'
        )

        assert assets.thumbnail_url == 'https://example.com/thumb.png'
        assert assets.logo_url == 'https://example.com/logo.png'
        assert assets.long_name == 'T1'


class TestCleanPlayerName:
    """Test _clean_player_name helper function."""

    @pytest.mark.unit
    def test_clean_player_name_with_real_name(self):
        """Test cleaning player name with real name in parentheses."""
        result = _clean_player_name('Doran (Choi Hyeon-joon)')
        assert result == 'Doran'

    @pytest.mark.unit
    def test_clean_player_name_without_parentheses(self):
        """Test cleaning player name without parentheses."""
        result = _clean_player_name('Faker')
        assert result == 'Faker'

    @pytest.mark.unit
    def test_clean_player_name_with_spaces(self):
        """Test cleaning player name with spaces but no parentheses."""
        result = _clean_player_name('Naak Nako')
        assert result == 'Naak Nako'

    @pytest.mark.unit
    def test_clean_player_name_empty(self):
        """Test cleaning empty player name."""
        result = _clean_player_name('')
        assert result == ''

    @pytest.mark.unit
    def test_clean_player_name_none(self):
        """Test cleaning None player name."""
        result = _clean_player_name(None)
        assert result == ''


class TestGetPrimaryValidRole:
    """Test _get_primary_valid_role helper function."""

    @pytest.mark.unit
    def test_get_primary_role_single(self):
        """Test getting primary role from single role."""
        result = _get_primary_valid_role('Mid')
        assert result == 'Mid'

    @pytest.mark.unit
    def test_get_primary_role_multiple(self):
        """Test getting primary role from multiple roles."""
        result = _get_primary_valid_role('Mid;Part-Owner')
        assert result == 'Mid'

    @pytest.mark.unit
    def test_get_primary_role_invalid_first(self):
        """Test skipping invalid role to get valid one."""
        result = _get_primary_valid_role('Coach;Top')
        assert result == 'Top'

    @pytest.mark.unit
    def test_get_primary_role_all_invalid(self):
        """Test returning None when no valid roles."""
        result = _get_primary_valid_role('Coach;Manager')
        assert result is None

    @pytest.mark.unit
    def test_get_primary_role_empty(self):
        """Test returning None for empty string."""
        result = _get_primary_valid_role('')
        assert result is None

    @pytest.mark.unit
    def test_get_primary_role_none(self):
        """Test returning None for None input."""
        result = _get_primary_valid_role(None)
        assert result is None

    @pytest.mark.unit
    def test_valid_roles_constant(self):
        """Test that VALID_ROLES contains expected roles."""
        expected_roles = {'Top', 'Jungle', 'Mid', 'Bot', 'Support'}
        assert expected_roles.issubset(VALID_ROLES)


class TestGetActivePlayers:
    """Test get_active_players function."""

    @pytest.mark.integration
    def test_get_active_players_basic(self, mock_leaguepedia_query, active_players_mock_data):
        """Test basic get_active_players call."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        players = mp.get_active_players('T1')

        assert isinstance(players, list)
        assert len(players) == 5
        assert all(isinstance(p, TeamPlayer) for p in players)

    @pytest.mark.integration
    def test_get_active_players_returns_team_players(
        self, mock_leaguepedia_query, active_players_mock_data
    ):
        """Test that get_active_players returns TeamPlayer objects."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        players = mp.get_active_players('T1')

        player_names = [p.name for p in players]
        assert 'Faker' in player_names
        assert 'Zeus' in player_names

    @pytest.mark.integration
    def test_get_active_players_extracts_role_correctly(
        self, mock_leaguepedia_query, active_players_mock_data
    ):
        """Test that get_active_players extracts roles correctly."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        players = mp.get_active_players('T1')

        # Find Faker and check role extraction (Mid;Part-Owner -> Mid)
        faker = next((p for p in players if p.name == 'Faker'), None)
        assert faker is not None
        assert faker.role == 'Mid'

    @pytest.mark.integration
    def test_get_active_players_cleans_player_names(
        self, mock_leaguepedia_query, player_with_real_name_mock
    ):
        """Test that get_active_players cleans player names."""
        mock_leaguepedia_query.return_value = player_with_real_name_mock

        players = mp.get_active_players('T1')

        assert len(players) == 1
        assert players[0].name == 'Doran'

    @pytest.mark.integration
    def test_get_active_players_empty_team(self, mock_leaguepedia_query):
        """Test get_active_players with empty result."""
        mock_leaguepedia_query.return_value = []

        players = mp.get_active_players('NonexistentTeam')

        assert players == []

    @pytest.mark.unit
    def test_get_active_players_empty_team_name(self):
        """Test get_active_players raises ValueError for empty team name."""
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            get_active_players('')

    @pytest.mark.unit
    def test_get_active_players_none_team_name(self):
        """Test get_active_players raises ValueError for None team name."""
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            get_active_players(None)

    @pytest.mark.integration
    def test_get_active_players_with_date(self, mock_leaguepedia_query, active_players_mock_data):
        """Test get_active_players with date filter."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        mp.get_active_players('T1', date='2022-06-01')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert '2022-06-01' in call_kwargs['where']


class TestGetActivePlayers_SQLInjection:
    """Test SQL injection protection in get_active_players."""

    @pytest.mark.integration
    def test_team_name_sql_injection(self, mock_leaguepedia_query, active_players_mock_data):
        """Test SQL injection protection in team name."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        malicious_input = "'; DROP TABLE Tenures; --"
        mp.get_active_players(malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']

    @pytest.mark.integration
    def test_date_sql_injection(self, mock_leaguepedia_query, active_players_mock_data):
        """Test SQL injection protection in date parameter."""
        mock_leaguepedia_query.return_value = active_players_mock_data

        malicious_date = "2024-01-01'; DROP TABLE Tenures; --"
        mp.get_active_players('T1', date=malicious_date)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']


class TestGetActivePlayersErrorHandling:
    """Test error handling in get_active_players."""

    @pytest.mark.integration
    def test_get_active_players_api_error(self, mock_leaguepedia_query):
        """Test that API errors are wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch active players"):
            mp.get_active_players('T1')


class TestGetActivePlayersEdgeCases:
    """Test edge cases in get_active_players."""

    @pytest.mark.integration
    def test_players_with_no_valid_roles(self, mock_leaguepedia_query):
        """Test handling players with no valid roles."""
        mock_data = [
            {
                'Player': 'Coach',
                'Team': 'T1',
                'DateJoin': '2024-01-01',
                'Roles': 'Head Coach',
            },
        ]
        mock_leaguepedia_query.return_value = mock_data

        players = mp.get_active_players('T1')

        # Should be empty since Head Coach is not a valid in-game role
        assert players == []

    @pytest.mark.integration
    def test_players_with_special_characters(self, mock_leaguepedia_query):
        """Test handling players with special characters in name."""
        mock_data = [
            {
                'Player': "Player's Name",
                'Team': 'T1',
                'DateJoin': '2024-01-01',
                'Roles': 'Mid',
            },
        ]
        mock_leaguepedia_query.return_value = mock_data

        players = mp.get_active_players('T1')

        assert len(players) == 1
        assert players[0].name == "Player's Name"


if __name__ == "__main__":
    pytest.main([__file__])
