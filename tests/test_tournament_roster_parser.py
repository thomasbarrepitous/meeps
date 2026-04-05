"""Tests for tournament roster parser functionality."""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

import meeps as lp
from meeps.parsers.tournament_roster_parser import (
    TournamentRoster,
    get_tournament_rosters,
    _parse_tournament_roster_data,
)

from .conftest import TestConstants, assert_valid_dataclass_instance


class TestDataFactory:
    """Factory for creating tournament roster test data."""

    @staticmethod
    def create_tournament_roster_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for tournament roster data."""
        return [
            {
                'Team': 'T1',
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Region': 'Korea',
                'RosterLinks': 'Zeus;;Oner;;Faker;;Gumayusi;;Keria',
                'Roles': 'Top;;Jungle;;Mid;;Bot;;Support',
                'Flags': 'Korea;;Korea;;Korea;;Korea;;Korea',
                'Footnotes': '',
                'IsUsed': 'Yes',
                'Tournament': 'LCK 2024 Summer',
                'Short': 'LCK Summer',
                'IsComplete': 'Yes',
                'PageAndTeam': 'LCK/2024 Season/Summer Season_T1',
                'UniqueLine': 'T1_LCK_2024_Summer',
            },
            {
                'Team': 'GenG',
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Region': 'Korea',
                'RosterLinks': 'Kiin;;Canyon;;Chovy;;Peyz;;Lehends',
                'Roles': 'Top;;Jungle;;Mid;;Bot;;Support',
                'Flags': 'Korea;;Korea;;Korea;;Korea;;Korea',
                'Footnotes': 'Notes about roster',
                'IsUsed': 'Yes',
                'Tournament': 'LCK 2024 Summer',
                'Short': 'LCK Summer',
                'IsComplete': 'Yes',
                'PageAndTeam': 'LCK/2024 Season/Summer Season_GenG',
                'UniqueLine': 'GenG_LCK_2024_Summer',
            },
        ]

    @staticmethod
    def create_incomplete_roster_mock() -> List[Dict[str, Any]]:
        """Create mock for incomplete roster."""
        return [
            {
                'Team': 'NewTeam',
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Region': 'Korea',
                'RosterLinks': 'Player1;;Player2',
                'Roles': 'Top;;Jungle',
                'Flags': 'Korea;;Korea',
                'IsUsed': None,
                'IsComplete': 'No',
            }
        ]


@pytest.fixture
def tournament_roster_mock_data():
    """Provide tournament roster mock data."""
    return TestDataFactory.create_tournament_roster_mock_response()


@pytest.fixture
def incomplete_roster_mock_data():
    """Provide incomplete roster mock data."""
    return TestDataFactory.create_incomplete_roster_mock()


class TestTournamentRosterImports:
    """Test that tournament roster functions are properly importable."""

    @pytest.mark.unit
    def test_tournament_roster_functions_importable(self):
        """Test that all tournament roster functions are available in the main module."""
        assert hasattr(lp, 'get_tournament_rosters')

    @pytest.mark.unit
    def test_tournament_roster_dataclass_importable(self):
        """Test that TournamentRoster dataclass is importable."""
        assert hasattr(lp, 'TournamentRoster')
        assert lp.TournamentRoster is TournamentRoster


class TestTournamentRosterDataclass:
    """Test TournamentRoster dataclass functionality and computed properties."""

    @pytest.mark.unit
    def test_tournament_roster_initialization(self):
        """Test TournamentRoster dataclass can be initialized with all fields."""
        roster = TournamentRoster(
            team=TestConstants.TEAM_T1,
            overview_page=TestConstants.LCK_2024_SUMMER,
            region='Korea',
            roster_links='Zeus;;Oner;;Faker;;Gumayusi;;Keria',
            roles='Top;;Jungle;;Mid;;Bot;;Support',
            flags='Korea;;Korea;;Korea;;Korea;;Korea',
            is_used=True,
            is_complete=True,
        )

        assert_valid_dataclass_instance(
            roster, TournamentRoster, ['team', 'overview_page', 'region']
        )
        assert roster.team == TestConstants.TEAM_T1
        assert roster.overview_page == TestConstants.LCK_2024_SUMMER
        assert roster.region == 'Korea'

    @pytest.mark.unit
    def test_roster_links_list_property(self):
        """Test roster_links_list property correctly splits roster links."""
        roster = TournamentRoster(
            roster_links='Zeus;;Oner;;Faker;;Gumayusi;;Keria'
        )

        expected = ['Zeus', 'Oner', 'Faker', 'Gumayusi', 'Keria']
        assert roster.roster_links_list == expected
        assert len(roster.roster_links_list) == 5

    @pytest.mark.unit
    def test_roster_links_list_empty(self):
        """Test roster_links_list returns empty list when no links."""
        roster = TournamentRoster(roster_links=None)
        assert roster.roster_links_list == []

        roster2 = TournamentRoster(roster_links='')
        assert roster2.roster_links_list == []

    @pytest.mark.unit
    def test_roles_list_property(self):
        """Test roles_list property correctly splits roles."""
        roster = TournamentRoster(roles='Top;;Jungle;;Mid;;Bot;;Support')

        expected = ['Top', 'Jungle', 'Mid', 'Bot', 'Support']
        assert roster.roles_list == expected
        assert len(roster.roles_list) == 5

    @pytest.mark.unit
    def test_roles_list_empty(self):
        """Test roles_list returns empty list when no roles."""
        roster = TournamentRoster(roles=None)
        assert roster.roles_list == []

    @pytest.mark.unit
    def test_flags_list_property(self):
        """Test flags_list property correctly splits flags."""
        roster = TournamentRoster(flags='Korea;;Korea;;Korea;;China;;Korea')

        expected = ['Korea', 'Korea', 'Korea', 'China', 'Korea']
        assert roster.flags_list == expected

    @pytest.mark.unit
    def test_flags_list_empty(self):
        """Test flags_list returns empty list when no flags."""
        roster = TournamentRoster(flags=None)
        assert roster.flags_list == []

    @pytest.mark.unit
    def test_roster_with_whitespace_in_lists(self):
        """Test that list properties handle whitespace correctly."""
        roster = TournamentRoster(
            roster_links='  Zeus  ;;  Oner  ;;  Faker  ',
            roles='  Top  ;;  Jungle  ;;  Mid  ',
        )

        assert roster.roster_links_list == ['Zeus', 'Oner', 'Faker']
        assert roster.roles_list == ['Top', 'Jungle', 'Mid']

    @pytest.mark.unit
    def test_default_values(self):
        """Test TournamentRoster default values."""
        roster = TournamentRoster()

        assert roster.team is None
        assert roster.overview_page is None
        assert roster.region is None
        assert roster.roster_links is None
        assert roster.roles is None
        assert roster.flags is None
        assert roster.footnotes is None
        assert roster.is_used is None
        assert roster.tournament is None
        assert roster.short is None
        assert roster.is_complete is None
        assert roster.page_and_team is None
        assert roster.unique_line is None


class TestTournamentRosterParsing:
    """Test tournament roster parsing functionality."""

    @pytest.mark.unit
    def test_parse_tournament_roster_data_full(self, tournament_roster_mock_data):
        """Test parsing full tournament roster data."""
        roster = _parse_tournament_roster_data(tournament_roster_mock_data[0])

        assert roster.team == 'T1'
        assert roster.overview_page == 'LCK/2024 Season/Summer Season'
        assert roster.region == 'Korea'
        assert roster.roster_links == 'Zeus;;Oner;;Faker;;Gumayusi;;Keria'
        assert roster.roles == 'Top;;Jungle;;Mid;;Bot;;Support'
        assert roster.is_used is True
        assert roster.is_complete is True

    @pytest.mark.unit
    def test_parse_tournament_roster_data_boolean_fields(self):
        """Test boolean field parsing."""
        data = {'IsUsed': 'Yes', 'IsComplete': 'No'}
        roster = _parse_tournament_roster_data(data)

        assert roster.is_used is True
        assert roster.is_complete is False

    @pytest.mark.unit
    def test_parse_tournament_roster_data_none_boolean(self):
        """Test None boolean field parsing."""
        data = {'IsUsed': None, 'IsComplete': None}
        roster = _parse_tournament_roster_data(data)

        assert roster.is_used is None
        assert roster.is_complete is None

    @pytest.mark.unit
    def test_parse_tournament_roster_data_empty(self):
        """Test parsing empty data."""
        roster = _parse_tournament_roster_data({})

        assert roster.team is None
        assert roster.overview_page is None
        assert roster.is_used is None


class TestTournamentRosterAPI:
    """Test tournament roster API functions with mocked data."""

    @pytest.mark.integration
    def test_get_tournament_rosters_basic(self, mock_leaguepedia_query, tournament_roster_mock_data):
        """Test basic get_tournament_rosters call."""
        mock_leaguepedia_query.return_value = tournament_roster_mock_data

        rosters = lp.get_tournament_rosters(team='T1')

        assert len(rosters) == 2
        assert all(isinstance(r, TournamentRoster) for r in rosters)
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_tournament_rosters_with_tournament_filter(
        self, mock_leaguepedia_query, tournament_roster_mock_data
    ):
        """Test get_tournament_rosters with tournament filter."""
        mock_leaguepedia_query.return_value = [tournament_roster_mock_data[0]]

        rosters = lp.get_tournament_rosters(team='T1', tournament='LCK 2024 Summer')

        assert len(rosters) == 1
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'Tournament' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournament_rosters_with_region_filter(
        self, mock_leaguepedia_query, tournament_roster_mock_data
    ):
        """Test get_tournament_rosters with region filter."""
        mock_leaguepedia_query.return_value = tournament_roster_mock_data

        rosters = lp.get_tournament_rosters(team='T1', region='Korea')

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'Region' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournament_rosters_with_is_complete_filter(
        self, mock_leaguepedia_query, tournament_roster_mock_data
    ):
        """Test get_tournament_rosters with is_complete filter."""
        mock_leaguepedia_query.return_value = tournament_roster_mock_data

        rosters = lp.get_tournament_rosters(team='T1', is_complete=True)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert 'IsComplete' in call_kwargs['where']
        assert 'Yes' in call_kwargs['where']

    @pytest.mark.integration
    def test_get_tournament_rosters_empty_result(self, mock_leaguepedia_query):
        """Test get_tournament_rosters with empty result."""
        mock_leaguepedia_query.return_value = []

        rosters = lp.get_tournament_rosters(team='NonexistentTeam')

        assert rosters == []
        assert isinstance(rosters, list)


class TestTournamentRosterErrorHandling:
    """Test error handling in tournament roster functionality."""

    @pytest.mark.integration
    def test_get_tournament_rosters_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch tournament rosters"):
            lp.get_tournament_rosters(team='T1')

    @pytest.mark.integration
    def test_get_tournament_rosters_sql_injection_protection(
        self, mock_leaguepedia_query, tournament_roster_mock_data
    ):
        """Test SQL injection protection in team parameter."""
        mock_leaguepedia_query.return_value = tournament_roster_mock_data

        malicious_input = "'; DROP TABLE TournamentRosters; --"
        rosters = lp.get_tournament_rosters(team=malicious_input)

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']


class TestTournamentRosterEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_roster_with_single_player(self):
        """Test roster with only one player."""
        roster = TournamentRoster(
            roster_links='Solo',
            roles='Mid',
            flags='Korea',
        )

        assert roster.roster_links_list == ['Solo']
        assert roster.roles_list == ['Mid']
        assert roster.flags_list == ['Korea']

    @pytest.mark.unit
    def test_roster_with_special_characters_in_team(self):
        """Test roster with special characters in team name."""
        special_team = "Team's Name (Special)"
        roster = TournamentRoster(team=special_team)

        assert roster.team == special_team

    @pytest.mark.unit
    def test_roster_with_empty_delimiter_segments(self):
        """Test roster with empty segments between delimiters."""
        roster = TournamentRoster(roster_links='Zeus;;;;Faker')

        # Empty segments should be filtered out
        assert roster.roster_links_list == ['Zeus', 'Faker']

    @pytest.mark.integration
    def test_get_tournament_rosters_with_order_by(
        self, mock_leaguepedia_query, tournament_roster_mock_data
    ):
        """Test get_tournament_rosters with order_by parameter."""
        mock_leaguepedia_query.return_value = tournament_roster_mock_data

        rosters = lp.get_tournament_rosters(
            team='T1',
            order_by='TournamentRosters.Tournament DESC'
        )

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs.get('order_by') == 'TournamentRosters.Tournament DESC'


if __name__ == "__main__":
    pytest.main([__file__])
