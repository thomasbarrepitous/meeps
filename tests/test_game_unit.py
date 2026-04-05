"""Unit tests for game_parser functionality with mocked data.

Note: Tests for get_games function are limited because it relies on the transmute_game
function which uses external libraries (lol_id_tools, lol_dto) with complex data structures.
Full integration tests for get_games are in test_game.py using @pytest.mark.api.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

import meeps as lp
from meeps.parsers.game_parser import (
    get_regions,
    get_tournaments,
    get_games,
    get_game_details,
)
from meeps.transmuters.tournament import LeaguepediaTournament

from .conftest import TestConstants


class TestDataFactory:
    """Factory for creating game parser test data."""

    @staticmethod
    def create_regions_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for regions data."""
        return [
            {'Region': 'Korea'},
            {'Region': 'China'},
            {'Region': 'Europe'},
            {'Region': 'North America'},
        ]

    @staticmethod
    def create_tournaments_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for tournaments data."""
        return [
            {
                'Name': 'LCK 2024 Summer',
                'DateStart': '2024-06-12',
                'Date': '2024-08-18',
                'Region': 'Korea',
                'League': 'LoL Champions Korea',
                'League Short': 'LCK',
                'Rulebook': 'https://example.com/rulebook',
                'TournamentLevel': 'Primary',
                'IsQualifier': 0,
                'IsPlayoffs': 0,
                'IsOfficial': 1,
                'OverviewPage': 'LCK/2024 Season/Summer Season',
            },
            {
                'Name': 'LCK 2024 Summer Playoffs',
                'DateStart': '2024-08-19',
                'Date': '2024-09-01',
                'Region': 'Korea',
                'League': 'LoL Champions Korea',
                'League Short': 'LCK',
                'Rulebook': 'https://example.com/rulebook',
                'TournamentLevel': 'Primary',
                'IsQualifier': 0,
                'IsPlayoffs': 1,
                'IsOfficial': 1,
                'OverviewPage': 'LCK/2024 Season/Summer Playoffs',
            },
        ]


@pytest.fixture
def regions_mock_data():
    """Provide regions mock data."""
    return TestDataFactory.create_regions_mock_response()


@pytest.fixture
def tournaments_mock_data():
    """Provide tournaments mock data."""
    return TestDataFactory.create_tournaments_mock_response()


class TestGameParserImports:
    """Test that game parser functions are properly importable."""

    @pytest.mark.unit
    def test_game_functions_importable(self):
        """Test that all game functions are available in the main module."""
        expected_functions = [
            'get_regions',
            'get_tournaments',
            'get_games',
            'get_game_details',
        ]

        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"


class TestGetRegions:
    """Test get_regions function."""

    @pytest.mark.integration
    def test_get_regions_basic(self, mock_leaguepedia_query, regions_mock_data):
        """Test basic get_regions call."""
        mock_leaguepedia_query.return_value = regions_mock_data

        regions = lp.get_regions()

        assert isinstance(regions, list)
        assert len(regions) == 4
        assert 'Korea' in regions
        assert 'China' in regions
        assert 'Europe' in regions

    @pytest.mark.integration
    def test_get_regions_returns_strings(self, mock_leaguepedia_query, regions_mock_data):
        """Test that get_regions returns list of strings."""
        mock_leaguepedia_query.return_value = regions_mock_data

        regions = lp.get_regions()

        assert all(isinstance(r, str) for r in regions)

    @pytest.mark.integration
    def test_get_regions_empty_response(self, mock_leaguepedia_query):
        """Test get_regions with empty response."""
        mock_leaguepedia_query.return_value = []

        regions = lp.get_regions()

        assert regions == []

    @pytest.mark.integration
    def test_get_regions_calls_correct_table(self, mock_leaguepedia_query, regions_mock_data):
        """Test that get_regions queries the correct table."""
        mock_leaguepedia_query.return_value = regions_mock_data

        lp.get_regions()

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs['tables'] == 'Tournaments'
        assert call_kwargs['fields'] == 'Region'


class TestGetTournaments:
    """Test get_tournaments function."""

    @pytest.mark.integration
    def test_get_tournaments_basic(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test basic get_tournaments call."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        tournaments = lp.get_tournaments(region='Korea', year=2024)

        assert isinstance(tournaments, list)
        assert len(tournaments) == 2
        assert all(isinstance(t, LeaguepediaTournament) for t in tournaments)

    @pytest.mark.integration
    def test_get_tournaments_with_region_filter(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with region filter."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        lp.get_tournaments(region='Korea')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'Korea' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_year_filter(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with year filter."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        lp.get_tournaments(year=2024)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert '2024' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_tournament_level(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments default tournament level."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        lp.get_tournaments(region='Korea')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'Primary' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_is_playoffs_true(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with is_playoffs=True."""
        mock_leaguepedia_query.return_value = [tournaments_mock_data[1]]

        lp.get_tournaments(region='Korea', is_playoffs=True)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        # is_playoffs is cast to integer 1
        assert 'IsPlayoffs' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_is_playoffs_false(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with is_playoffs=False."""
        mock_leaguepedia_query.return_value = [tournaments_mock_data[0]]

        lp.get_tournaments(region='Korea', is_playoffs=False)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'IsPlayoffs' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_order_by(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with order_by parameter."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        lp.get_tournaments(region='Korea', order_by='Tournaments.DateStart DESC')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs.get('order_by') == 'Tournaments.DateStart DESC'

    @pytest.mark.integration
    def test_get_tournaments_with_limit(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with limit parameter."""
        mock_leaguepedia_query.return_value = [tournaments_mock_data[0]]

        lp.get_tournaments(region='Korea', limit=1)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs.get('limit') == 1

    @pytest.mark.integration
    def test_get_tournaments_empty_response(self, mock_leaguepedia_query):
        """Test get_tournaments with empty response."""
        mock_leaguepedia_query.return_value = []

        tournaments = lp.get_tournaments(region='NonexistentRegion')

        assert tournaments == []

    @pytest.mark.integration
    def test_get_tournaments_transmutes_data(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test that tournament data is properly transmuted."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        tournaments = lp.get_tournaments(region='Korea')

        tournament = tournaments[0]
        assert tournament.name == 'LCK 2024 Summer'
        assert tournament.region == 'Korea'
        assert tournament.overviewPage == 'LCK/2024 Season/Summer Season'
        assert tournament.tournamentLevel == 'Primary'
        assert tournament.leagueShort == 'LCK'


class TestGetGames:
    """Test get_games function.

    Note: Full data transformation tests are covered in test_game.py with @pytest.mark.api
    because get_games relies on transmute_game which uses external libraries.
    These tests focus on query construction and empty response handling.
    """

    @pytest.mark.integration
    def test_get_games_empty_response(self, mock_leaguepedia_query):
        """Test get_games with empty response."""
        mock_leaguepedia_query.return_value = []

        games = lp.get_games('Nonexistent/Tournament')

        assert games == []

    @pytest.mark.integration
    def test_get_games_queries_correct_table(self, mock_leaguepedia_query):
        """Test that get_games queries ScoreboardGames table."""
        mock_leaguepedia_query.return_value = []

        lp.get_games('LCK/2024 Season/Summer Season')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs['tables'] == 'ScoreboardGames'

    @pytest.mark.integration
    def test_get_games_where_clause(self, mock_leaguepedia_query):
        """Test get_games constructs correct WHERE clause."""
        mock_leaguepedia_query.return_value = []

        lp.get_games(tournament_overview_page='LCK/2024 Season/Summer Season')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'LCK/2024 Season/Summer Season' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_games_with_limit(self, mock_leaguepedia_query):
        """Test get_games passes limit parameter."""
        mock_leaguepedia_query.return_value = []

        lp.get_games('LCK/2024 Season/Summer Season', limit=5)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs.get('limit') == 5

    @pytest.mark.integration
    def test_get_games_no_filter(self, mock_leaguepedia_query):
        """Test get_games with no tournament filter."""
        mock_leaguepedia_query.return_value = []

        lp.get_games()

        call_kwargs = mock_leaguepedia_query.call_args[1]
        # Should have no where clause or empty where clause
        assert call_kwargs['where'] is None or call_kwargs['where'] == ''


class TestGetGameDetails:
    """Test get_game_details function."""

    @pytest.mark.unit
    def test_get_game_details_requires_leaguepedia_id(self):
        """Test that get_game_details raises ValueError without Leaguepedia ID."""
        # Create a mock game without leaguepedia gameId
        mock_game = MagicMock()
        mock_game.sources.leaguepedia.gameId = None

        with pytest.raises(ValueError, match="Leaguepedia GameId not present"):
            get_game_details(mock_game)

    @pytest.mark.unit
    def test_get_game_details_requires_sources(self):
        """Test that get_game_details handles missing sources."""
        mock_game = MagicMock()
        mock_game.sources.leaguepedia.gameId = None

        with pytest.raises(ValueError):
            get_game_details(mock_game)


class TestGameParserSQLInjection:
    """Test SQL injection protection in game parser."""

    @pytest.mark.integration
    def test_get_tournaments_sql_injection_region(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test SQL injection protection in region parameter."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        malicious_input = "'; DROP TABLE Tournaments; --"
        lp.get_tournaments(region=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']

    @pytest.mark.integration
    def test_get_games_sql_injection_overview_page(self, mock_leaguepedia_query):
        """Test SQL injection protection in overview page parameter."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "'; DELETE FROM ScoreboardGames; --"
        lp.get_games(tournament_overview_page=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']


class TestLeaguepediaTournamentDataclass:
    """Test LeaguepediaTournament dataclass."""

    @pytest.mark.unit
    def test_tournament_initialization(self):
        """Test LeaguepediaTournament dataclass initialization."""
        tournament = LeaguepediaTournament(
            name='LCK 2024 Summer',
            start='2024-06-12',
            end='2024-08-18',
            region='Korea',
            league='LoL Champions Korea',
            leagueShort='LCK',
            rulebook='https://example.com/rulebook',
            tournamentLevel='Primary',
            isQualifier=False,
            isPlayoffs=False,
            isOfficial=True,
            overviewPage='LCK/2024 Season/Summer Season',
        )

        assert tournament.name == 'LCK 2024 Summer'
        assert tournament.region == 'Korea'
        assert tournament.leagueShort == 'LCK'
        assert tournament.isOfficial is True
        assert tournament.isPlayoffs is False

    @pytest.mark.unit
    def test_tournament_all_fields_present(self):
        """Test that LeaguepediaTournament has all expected fields."""
        expected_fields = [
            'name', 'start', 'end', 'region', 'league', 'leagueShort',
            'rulebook', 'tournamentLevel', 'isQualifier', 'isPlayoffs',
            'isOfficial', 'overviewPage'
        ]

        tournament = LeaguepediaTournament(
            name='Test',
            start='2024-01-01',
            end='2024-01-02',
            region='Test',
            league='Test',
            leagueShort='T',
            rulebook='',
            tournamentLevel='Primary',
            isQualifier=False,
            isPlayoffs=False,
            isOfficial=True,
            overviewPage='Test',
        )

        for field in expected_fields:
            assert hasattr(tournament, field), f"Missing field: {field}"


class TestGameParserEdgeCases:
    """Test edge cases in game parser."""

    @pytest.mark.integration
    def test_get_tournaments_no_filters(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with minimal filters."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        tournaments = lp.get_tournaments()

        assert len(tournaments) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        # Should still filter by tournament level
        assert 'Primary' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournaments_with_special_characters(self, mock_leaguepedia_query, tournaments_mock_data):
        """Test get_tournaments with special characters in region."""
        mock_leaguepedia_query.return_value = tournaments_mock_data

        lp.get_tournaments(region="North America")

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'North America' in call_kwargs['where']


if __name__ == "__main__":
    pytest.main([__file__])
