"""Shared test configuration and fixtures for Leaguepedia parser tests."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests with mocked APIs")
    config.addinivalue_line("markers", "slow: Tests that may take longer to run")
    config.addinivalue_line("markers", "api: Tests that interact with external APIs")


# Test Data Factories
class TestDataFactory:
    """Factory for creating consistent test data across test modules."""
    
    @staticmethod
    def create_standings_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for standings data."""
        return [
            {
                'Team': 'T1',
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Place': '1',
                'WinSeries': '16',
                'LossSeries': '2',
                'TieSeries': '0',
                'WinGames': '34',
                'LossGames': '8',
                'Points': '16',
                'PointsTiebreaker': '0.0',
                'Streak': '3',
                'StreakDirection': 'W'
            },
            {
                'Team': 'GenG',
                'OverviewPage': 'LCK/2024 Season/Summer Season', 
                'Place': '2',
                'WinSeries': '14',
                'LossSeries': '4',
                'TieSeries': '0',
                'WinGames': '30',
                'LossGames': '12',
                'Points': '14',
                'PointsTiebreaker': '0.0',
                'Streak': '1',
                'StreakDirection': 'L'
            }
        ]
    
    @staticmethod
    def create_champions_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for champions data."""
        return [
            {
                'Name': 'Jinx',
                'Title': 'The Loose Cannon',
                'Attributes': 'Marksman',
                'AttackRange': '525',
                'AttackDamage': '59',
                'Health': '610',
                'BE': '6300',
                'RP': '975',
                'Resource': 'Mana',
                'Movespeed': '325'
            },
            {
                'Name': 'Yasuo',
                'Title': 'The Unforgiven',
                'Attributes': 'Fighter,Assassin',
                'AttackRange': '175',
                'AttackDamage': '60',
                'Health': '590',
                'BE': '6300',
                'RP': '975',
                'Resource': 'Flow',
                'Movespeed': '345'
            }
        ]
    
    @staticmethod
    def create_items_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for items data."""
        return [
            {
                'Name': 'Infinity Edge',
                'Tier': 'Legendary',
                'AD': '70',
                'Crit': '20',
                'TotalCost': '3400',
                'Armor': '0',
                'AP': '0',
                'Health': '0',
                'Mana': '0'
            },
            {
                'Name': "Rabadon's Deathcap",
                'Tier': 'Legendary', 
                'AD': '0',
                'AP': '120',
                'TotalCost': '3600',
                'Armor': '0',
                'Crit': '0',
                'Health': '0',
                'Mana': '0'
            },
            {
                'Name': 'Thornmail',
                'Tier': 'Legendary',
                'AD': '0',
                'AP': '0',
                'Armor': '80',
                'Health': '350',
                'TotalCost': '2700',
                'Crit': '0',
                'Mana': '0'
            }
        ]
    
    @staticmethod
    def create_roster_changes_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for roster changes data."""
        return [
            {
                'Date_Sort': '2013-01-01T00:00:00Z',
                'Player': 'Faker',
                'Direction': 'Join',
                'Team': 'T1',
                'RolesIngame': 'Mid',
                'RolesStaff': '',
                'Roles': 'Mid',
                'RoleDisplay': 'Mid Laner',
                'Role': 'Mid',
                'RoleModifier': '',
                'Status': 'Active',
                'CurrentTeamPriority': '1',
                'PlayerUnlinked': False,
                'AlreadyJoined': '',
                'Tournaments': 'LCK/2013 Season/Winter',
                'Source': '',
                'IsGCD': False,
                'Preload': '',
                'PreloadSortNumber': '0',
                'Tags': '',
                'NewsId': 'RC001',
                'RosterChangeId': 'RC001',
                'N_LineInNews': '1'
            },
            {
                'Date_Sort': '2023-11-15T00:00:00Z',
                'Player': 'Caps',
                'Direction': 'Leave',
                'Team': 'G2 Esports',
                'RolesIngame': 'Mid',
                'RolesStaff': '',
                'Roles': 'Mid',
                'RoleDisplay': 'Mid Laner',
                'Role': 'Mid',
                'RoleModifier': '',
                'Status': 'Inactive',
                'CurrentTeamPriority': '0',
                'PlayerUnlinked': False,
                'AlreadyJoined': '',
                'Tournaments': 'LEC/2024 Season/Spring Season',
                'Source': '',
                'IsGCD': False,
                'Preload': '',
                'PreloadSortNumber': '0',
                'Tags': '',
                'NewsId': 'RC002',
                'RosterChangeId': 'RC002',
                'N_LineInNews': '1'
            }
        ]
    
    @staticmethod
    def create_contracts_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for contracts data."""
        return [
            {
                'Player': 'Faker',
                'Team': 'T1',
                'ContractEnd': '2025-12-31T23:59:59Z',
                'ContractEndText': 'December 31, 2025',
                'IsRemoval': '0',
                'NewsId': 'CONTRACT001'
            },
            {
                'Player': 'Caps',
                'Team': 'G2 Esports',
                'ContractEnd': '2024-11-30T23:59:59Z',
                'ContractEndText': 'November 30, 2024',
                'IsRemoval': '0',
                'NewsId': 'CONTRACT002'
            },
            {
                'Player': 'Jankos',
                'Team': 'G2 Esports',
                'ContractEnd': '2023-12-31T23:59:59Z',
                'ContractEndText': 'December 31, 2023',
                'IsRemoval': '1',
                'NewsId': 'CONTRACT003'
            },
            {
                'Player': 'Canyon',
                'Team': 'DAMWON KIA',
                'ContractEnd': '2026-06-15T23:59:59Z',
                'ContractEndText': 'June 15, 2026',
                'IsRemoval': '0',
                'NewsId': 'CONTRACT004'
            }
        ]
    
    @staticmethod
    def create_scoreboard_players_mock_response() -> List[Dict[str, Any]]:
        """Create mock API response for scoreboard players data."""
        return [
            {
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Link': 'Faker',
                'Champion': 'Azir',
                'Kills': '8',
                'Deaths': '1',
                'Assists': '12',
                'SummonerSpells': 'Flash,Teleport',
                'Gold': '18500',
                'CS': '285',
                'DamageToChampions': '32000',
                'VisionScore': '45',
                'Items': 'Nashor\'s Tooth;Rabadon\'s Deathcap;Zhonya\'s Hourglass;Void Staff;Morellonomicon;Sorcerer\'s Shoes',
                'Trinket': 'Farsight Alteration',
                'KeystoneMastery': 'Lethal Tempo',
                'KeystoneRune': 'Lethal Tempo',
                'PrimaryTree': 'Precision',
                'SecondaryTree': 'Inspiration',
                'Runes': 'Lethal Tempo, Presence of Mind, Legend: Alacrity, Cut Down, Magical Footwear, Biscuit Delivery',
                'TeamKills': '22',
                'TeamGold': '85000',
                'Team': 'T1',
                'TeamVs': 'GenG',
                'Time': '2024-08-15T10:30:00Z',
                'PlayerWin': 'Yes',
                'DateTime_UTC': '2024-08-15T10:30:00Z',
                'DST': 'No',
                'Tournament': 'LCK/2024 Season/Summer Season',
                'Role': 'Mid',
                'Role_Number': '3',
                'IngameRole': 'Middle',
                'Side': '1',
                'UniqueLine': 'T1_Mid',
                'UniqueLineVs': 'GenG_Mid',
                'UniqueRole': 'T1_Mid_1',
                'UniqueRoleVs': 'GenG_Mid_1',
                'GameId': 'GAME001',
                'MatchId': 'MATCH001',
                'GameTeamId': 'T1_GAME001',
                'GameRoleId': 'T1_Mid_GAME001',
                'GameRoleIdVs': 'GenG_Mid_GAME001',
                'StatsPage': 'T1_vs_GenG_Game1'
            },
            {
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Link': 'Chovy',
                'Champion': 'Orianna',
                'Kills': '4',
                'Deaths': '3',
                'Assists': '8',
                'SummonerSpells': 'Flash,Teleport',
                'Gold': '16200',
                'CS': '295',
                'DamageToChampions': '28500',
                'VisionScore': '38',
                'Items': 'Liandry\'s Anguish;Rabadon\'s Deathcap;Zhonya\'s Hourglass;Void Staff;Seraph\'s Embrace;Sorcerer\'s Shoes',
                'Trinket': 'Farsight Alteration',
                'KeystoneMastery': 'Phase Rush',
                'KeystoneRune': 'Phase Rush',
                'PrimaryTree': 'Sorcery',
                'SecondaryTree': 'Precision',
                'Runes': 'Phase Rush, Manaflow Band, Transcendence, Gathering Storm, Presence of Mind, Last Stand',
                'TeamKills': '15',
                'TeamGold': '72000',
                'Team': 'GenG',
                'TeamVs': 'T1',
                'Time': '2024-08-15T10:30:00Z',
                'PlayerWin': 'No',
                'DateTime_UTC': '2024-08-15T10:30:00Z',
                'DST': 'No',
                'Tournament': 'LCK/2024 Season/Summer Season',
                'Role': 'Mid',
                'Role_Number': '3',
                'IngameRole': 'Middle',
                'Side': '2',
                'UniqueLine': 'GenG_Mid',
                'UniqueLineVs': 'T1_Mid',
                'UniqueRole': 'GenG_Mid_1',
                'UniqueRoleVs': 'T1_Mid_1',
                'GameId': 'GAME001',
                'MatchId': 'MATCH001',
                'GameTeamId': 'GenG_GAME001',
                'GameRoleId': 'GenG_Mid_GAME001',
                'GameRoleIdVs': 'T1_Mid_GAME001',
                'StatsPage': 'T1_vs_GenG_Game1'
            },
            {
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Link': 'Gumayusi',
                'Champion': 'Jinx',
                'Kills': '12',
                'Deaths': '2',
                'Assists': '8',
                'SummonerSpells': 'Flash,Heal',
                'Gold': '22000',
                'CS': '320',
                'DamageToChampions': '45000',
                'VisionScore': '25',
                'Items': 'Kraken Slayer;Infinity Edge;Lord Dominik\'s Regards;Phantom Dancer;Bloodthirster;Berserker\'s Greaves',
                'Trinket': 'Farsight Alteration',
                'KeystoneMastery': 'Lethal Tempo',
                'KeystoneRune': 'Lethal Tempo',
                'PrimaryTree': 'Precision',
                'SecondaryTree': 'Domination',
                'Runes': 'Lethal Tempo, Overheal, Legend: Bloodline, Cut Down, Taste of Blood, Treasure Hunter',
                'TeamKills': '22',
                'TeamGold': '85000',
                'Team': 'T1',
                'TeamVs': 'GenG',
                'Time': '2024-08-15T10:30:00Z',
                'PlayerWin': 'Yes',
                'DateTime_UTC': '2024-08-15T10:30:00Z',
                'DST': 'No',
                'Tournament': 'LCK/2024 Season/Summer Season',
                'Role': 'Bot',
                'Role_Number': '1',
                'IngameRole': 'Bottom',
                'Side': '1',
                'UniqueLine': 'T1_Bot',
                'UniqueLineVs': 'GenG_Bot',
                'UniqueRole': 'T1_Bot_1',
                'UniqueRoleVs': 'GenG_Bot_1',
                'GameId': 'GAME001',
                'MatchId': 'MATCH001',
                'GameTeamId': 'T1_GAME001',
                'GameRoleId': 'T1_Bot_GAME001',
                'GameRoleIdVs': 'GenG_Bot_GAME001',
                'StatsPage': 'T1_vs_GenG_Game1'
            }
        ]


# Shared Fixtures
@pytest.fixture
def test_data_factory():
    """Provide test data factory for all tests."""
    return TestDataFactory


@pytest.fixture
def mock_leaguepedia_query():
    """Mock the leaguepedia query method."""
    with patch('meeps.site.leaguepedia.leaguepedia.query') as mock:
        yield mock


@pytest.fixture
def standings_mock_data(test_data_factory):
    """Provide standings mock data."""
    return test_data_factory.create_standings_mock_response()


@pytest.fixture
def champions_mock_data(test_data_factory):
    """Provide champions mock data."""
    return test_data_factory.create_champions_mock_response()


@pytest.fixture
def items_mock_data(test_data_factory):
    """Provide items mock data."""
    return test_data_factory.create_items_mock_response()


@pytest.fixture
def roster_changes_mock_data(test_data_factory):
    """Provide roster changes mock data."""
    return test_data_factory.create_roster_changes_mock_response()


@pytest.fixture
def contracts_mock_data(test_data_factory):
    """Provide contracts mock data."""
    return test_data_factory.create_contracts_mock_response()


@pytest.fixture
def scoreboard_players_mock_data(test_data_factory):
    """Provide scoreboard players mock data."""
    return test_data_factory.create_scoreboard_players_mock_response()


# Constants for tests
class TestConstants:
    """Constants used across multiple test modules."""
    
    # Tournament identifiers
    LCK_2024_SUMMER = "LCK/2024 Season/Summer Season"
    LEC_2024_SPRING = "LEC/2024 Season/Spring Season"
    
    # Team names
    TEAM_T1 = "T1"
    TEAM_GENG = "GenG"
    TEAM_G2 = "G2 Esports"
    
    # Player names
    PLAYER_FAKER = "Faker"
    PLAYER_CAPS = "Caps"
    
    # Item names
    ITEM_INFINITY_EDGE = "Infinity Edge"
    ITEM_RABADONS = "Rabadon's Deathcap"
    ITEM_THORNMAIL = "Thornmail"
    
    # Champion names
    CHAMPION_JINX = "Jinx"
    CHAMPION_YASUO = "Yasuo"


@pytest.fixture
def test_constants():
    """Provide test constants."""
    return TestConstants


# Helper functions for assertions
def assert_valid_dataclass_instance(instance, expected_type, required_fields: List[str]):
    """Assert that an instance is a valid dataclass of expected type with required fields."""
    assert isinstance(instance, expected_type)
    for field in required_fields:
        assert hasattr(instance, field), f"Missing required field: {field}"


def assert_mock_called_with_table(mock_query, expected_table: str):
    """Assert that mock was called with the expected table parameter."""
    mock_query.assert_called_once()
    call_args = mock_query.call_args
    assert call_args[1]['tables'] == expected_table


# Export helpers for use in tests
__all__ = [
    'TestDataFactory',
    'TestConstants', 
    'assert_valid_dataclass_instance',
    'assert_mock_called_with_table'
]