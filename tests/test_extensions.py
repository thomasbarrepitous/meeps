"""Tests for the extended Leaguepedia parser functionality."""

import pytest
from unittest.mock import Mock, patch

# Import the new parsers
import meeps as mp
from meeps.parsers.standings_parser import Standing
from meeps.parsers.champions_parser import Champion
from meeps.parsers.items_parser import Item
from meeps.parsers.roster_changes_parser import RosterChange


class TestStandings:
    """Test standings functionality."""
    
    def test_get_standings_import(self):
        """Test that standings functions are importable."""
        assert hasattr(mp, 'get_standings')
        assert hasattr(mp, 'get_tournament_standings')
        assert hasattr(mp, 'get_team_standings')
        assert hasattr(mp, 'get_standings_by_overview_page')
    
    def test_standing_dataclass(self):
        """Test Standing dataclass and properties."""
        standing = Standing(
            team="T1",
            win_series=10,
            loss_series=5,
            tie_series=1,
            win_games=25,
            loss_games=15
        )
        assert standing.team == "T1"
        assert standing.win_series == 10
        assert standing.loss_series == 5
        assert standing.total_series_played == 16
        assert abs(standing.series_win_rate - 66.67) < 0.1  # 10/15 * 100 (ties don't count in win rate)
        assert standing.total_games_played == 40
        assert abs(standing.game_win_rate - 62.5) < 0.1  # 25/40 * 100


class TestChampions:
    """Test champions functionality."""
    
    def test_get_champions_import(self):
        """Test that champions functions are importable."""
        assert hasattr(mp, 'get_champions')
        assert hasattr(mp, 'get_champion_by_name')
        assert hasattr(mp, 'get_champions_by_attributes')
        assert hasattr(mp, 'get_champions_by_resource')
        assert hasattr(mp, 'get_melee_champions')
        assert hasattr(mp, 'get_ranged_champions')
    
    def test_champion_dataclass(self):
        """Test Champion dataclass and properties."""
        champion = Champion(
            name="Jinx",
            attack_range=525.0,
            attributes="Marksman"
        )
        assert champion.name == "Jinx"
        assert champion.is_ranged is True
        assert champion.is_melee is False


class TestItems:
    """Test items functionality."""
    
    def test_get_items_import(self):
        """Test that items functions are importable."""
        assert hasattr(mp, 'get_items')
        assert hasattr(mp, 'get_item_by_name')
        assert hasattr(mp, 'get_items_by_tier')
        assert hasattr(mp, 'get_ad_items')
        assert hasattr(mp, 'get_ap_items')
        assert hasattr(mp, 'get_tank_items')
        assert hasattr(mp, 'get_health_items')
        assert hasattr(mp, 'search_items_by_stat')
    
    def test_item_dataclass(self):
        """Test Item dataclass and properties."""
        item = Item(
            name="Infinity Edge",
            ad=70,
            armor=0,
            total_cost=3400
        )
        assert item.name == "Infinity Edge"
        assert item.provides_ad is True
        assert item.provides_armor is False


class TestRosterChanges:
    """Test roster changes functionality."""
    
    def test_get_roster_changes_import(self):
        """Test that roster changes functions are importable."""
        assert hasattr(mp, 'get_roster_changes')
        assert hasattr(mp, 'get_team_roster_changes')
        assert hasattr(mp, 'get_player_roster_changes')
        assert hasattr(mp, 'get_recent_roster_changes')
        assert hasattr(mp, 'get_roster_additions')
        assert hasattr(mp, 'get_roster_removals')
        assert hasattr(mp, 'get_retirements')
    
    def test_roster_change_dataclass(self):
        """Test RosterChange dataclass and properties."""
        change = RosterChange(
            team="T1",
            player="Faker",
            direction="Join",
            role="Mid"
        )
        assert change.team == "T1"
        assert change.player == "Faker"
        assert change.is_addition is True
        assert change.is_removal is False


class TestIntegration:
    """Integration tests for the extended functionality."""
    
    @patch('meeps.site.leaguepedia.leaguepedia.query')
    def test_champions_query_mock(self, mock_query):
        """Test champions query with mocked data."""
        mock_query.return_value = [
            {
                'Name': 'Jinx',
                'Attributes': 'Marksman',
                'AttackRange': '525',
                'AttackDamage': '59',
                'Health': '610'
            }
        ]
        
        champions = mp.get_champions_by_attributes("Marksman")
        
        assert len(champions) == 1
        assert champions[0].name == "Jinx"
        assert "Marksman" in champions[0].attributes
        assert champions[0].is_ranged is True
        mock_query.assert_called_once()
    
    @patch('meeps.site.leaguepedia.leaguepedia.query')
    def test_standings_query_mock(self, mock_query):
        """Test standings query with mocked data."""
        mock_query.return_value = [
            {
                'Team': 'T1',
                'OverviewPage': 'LCK/2024 Season/Summer Season',
                'Place': '1',
                'WinSeries': '16',
                'LossSeries': '2'
            }
        ]
        
        standings = mp.get_tournament_standings("LCK/2024 Season/Summer Season")
        
        assert len(standings) == 1
        assert standings[0].team == "T1"
        assert standings[0].place == 1
        assert standings[0].win_series == 16
        mock_query.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
