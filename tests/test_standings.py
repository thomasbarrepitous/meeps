"""Tests for standings functionality in Leaguepedia parser."""

import pytest
from unittest.mock import Mock
from typing import List

import meeps as lp
from meeps.parsers.standings_parser import Standing

# Import helper functions from conftest
from .conftest import TestConstants, assert_valid_dataclass_instance, assert_mock_called_with_table


class TestStandingsImports:
    """Test that standings functions are properly importable."""
    
    @pytest.mark.unit
    def test_standings_functions_importable(self):
        """Test that all standings functions are available in the main module."""
        expected_functions = [
            'get_standings',
            'get_tournament_standings', 
            'get_team_standings',
            'get_standings_by_overview_page'
        ]
        
        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"


class TestStandingDataclass:
    """Test Standing dataclass functionality and computed properties."""
    
    @pytest.mark.unit
    def test_standing_initialization(self):
        """Test Standing dataclass can be initialized with all fields."""
        standing = Standing(
            team=TestConstants.TEAM_T1,
            overview_page=TestConstants.LCK_2024_SUMMER,
            place=1,
            win_series=16,
            loss_series=2,
            tie_series=0,
            win_games=34,
            loss_games=8,
            points=16
        )
        
        assert_valid_dataclass_instance(standing, Standing, ['team', 'place', 'win_series'])
        assert standing.team == TestConstants.TEAM_T1
        assert standing.place == 1
        assert standing.win_series == 16
        assert standing.loss_series == 2
    
    @pytest.mark.unit
    def test_standing_series_win_rate_calculation(self):
        """Test series win rate is calculated correctly."""
        standing = Standing(
            team=TestConstants.TEAM_T1,
            win_series=10,
            loss_series=5,
            tie_series=1
        )
        
        # Win rate should be 10/(10+5) = 66.67% (ties don't count)
        expected_win_rate = 66.67
        assert standing.series_win_rate is not None
        assert abs(standing.series_win_rate - expected_win_rate) < 0.1
    
    @pytest.mark.unit
    def test_standing_game_win_rate_calculation(self):
        """Test game win rate is calculated correctly."""
        standing = Standing(
            team=TestConstants.TEAM_T1,
            win_games=25,
            loss_games=15
        )
        
        # Win rate should be 25/(25+15) = 62.5%
        expected_win_rate = 62.5
        assert standing.game_win_rate is not None
        assert abs(standing.game_win_rate - expected_win_rate) < 0.1
    
    @pytest.mark.unit
    def test_standing_total_series_calculation(self):
        """Test total series played includes ties."""
        standing = Standing(
            win_series=10,
            loss_series=5,
            tie_series=2
        )
        
        assert standing.total_series_played == 17  # 10 + 5 + 2
    
    @pytest.mark.unit
    def test_standing_total_games_calculation(self):
        """Test total games played calculation."""
        standing = Standing(
            win_games=25,
            loss_games=15
        )
        
        assert standing.total_games_played == 40  # 25 + 15
    
    @pytest.mark.unit
    def test_standing_properties_with_none_values(self):
        """Test that computed properties handle None values gracefully."""
        standing = Standing(team=TestConstants.TEAM_T1)
        
        assert standing.series_win_rate is None
        assert standing.game_win_rate is None
        assert standing.total_series_played is None
        assert standing.total_games_played is None
    
    @pytest.mark.unit
    def test_standing_properties_with_zero_totals(self):
        """Test computed properties when totals are zero."""
        standing = Standing(
            win_series=0,
            loss_series=0,
            win_games=0,
            loss_games=0
        )
        
        assert standing.series_win_rate is None  # Division by zero should return None
        assert standing.game_win_rate is None    # Division by zero should return None
        assert standing.total_series_played == 0
        assert standing.total_games_played == 0


class TestStandingsAPI:
    """Test standings API functions with mocked data."""
    
    @pytest.mark.integration
    def test_get_standings_basic_call(self, mock_leaguepedia_query, standings_mock_data):
        """Test basic get_standings call returns properly parsed Standing objects."""
        mock_leaguepedia_query.return_value = standings_mock_data
        
        standings = lp.get_standings()
        
        assert len(standings) == 2
        assert all(isinstance(s, Standing) for s in standings)
        assert standings[0].team == TestConstants.TEAM_T1
        assert standings[1].team == TestConstants.TEAM_GENG
        assert_mock_called_with_table(mock_leaguepedia_query, "Standings")
    
    @pytest.mark.integration
    def test_get_standings_with_overview_page_filter(self, mock_leaguepedia_query, standings_mock_data):
        """Test get_standings with overview page filter."""
        mock_leaguepedia_query.return_value = standings_mock_data
        
        standings = lp.get_standings(overview_page=TestConstants.LCK_2024_SUMMER)
        
        assert len(standings) == 2
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes overview page filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert TestConstants.LCK_2024_SUMMER in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_standings_with_team_filter(self, mock_leaguepedia_query, standings_mock_data):
        """Test get_standings with team filter."""
        # Return only T1 data
        filtered_data = [standings_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        standings = lp.get_standings(team=TestConstants.TEAM_T1)
        
        assert len(standings) == 1
        assert standings[0].team == TestConstants.TEAM_T1
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes team filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert TestConstants.TEAM_T1 in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_tournament_standings(self, mock_leaguepedia_query, standings_mock_data):
        """Test get_tournament_standings convenience function."""
        mock_leaguepedia_query.return_value = standings_mock_data
        
        standings = lp.get_tournament_standings(TestConstants.LCK_2024_SUMMER)
        
        assert len(standings) == 2
        assert all(s.overview_page == TestConstants.LCK_2024_SUMMER for s in standings)
        assert_mock_called_with_table(mock_leaguepedia_query, "Standings")
    
    @pytest.mark.integration
    def test_get_team_standings(self, mock_leaguepedia_query, standings_mock_data):
        """Test get_team_standings convenience function."""
        filtered_data = [standings_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        standings = lp.get_team_standings(TestConstants.TEAM_T1)
        
        assert len(standings) == 1
        assert standings[0].team == TestConstants.TEAM_T1
        assert_mock_called_with_table(mock_leaguepedia_query, "Standings")
    
    @pytest.mark.integration
    def test_get_standings_by_overview_page(self, mock_leaguepedia_query, standings_mock_data):
        """Test get_standings_by_overview_page convenience function."""
        mock_leaguepedia_query.return_value = standings_mock_data
        
        standings = lp.get_standings_by_overview_page(TestConstants.LCK_2024_SUMMER)
        
        assert len(standings) == 2
        assert_mock_called_with_table(mock_leaguepedia_query, "Standings")


class TestStandingsErrorHandling:
    """Test error handling in standings functionality."""
    
    @pytest.mark.integration
    def test_get_standings_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to fetch standings"):
            lp.get_standings()
    
    @pytest.mark.integration
    def test_get_standings_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []
        
        standings = lp.get_standings()
        
        assert standings == []
        assert isinstance(standings, list)
    
    @pytest.mark.unit
    def test_standing_parsing_with_invalid_data(self):
        """Test Standing object creation with invalid/missing data."""
        # Test with empty data
        standing = Standing()
        assert standing.team is None
        assert standing.place is None
        
        # Test that computed properties handle missing data
        assert standing.series_win_rate is None
        assert standing.game_win_rate is None


class TestStandingsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_standing_with_all_wins_no_losses(self):
        """Test win rate calculation when there are no losses."""
        standing = Standing(
            win_series=10,
            loss_series=0,
            win_games=20,
            loss_games=0
        )
        
        assert standing.series_win_rate == 100.0
        assert standing.game_win_rate == 100.0
    
    @pytest.mark.unit
    def test_standing_with_all_losses_no_wins(self):
        """Test win rate calculation when there are no wins."""
        standing = Standing(
            win_series=0,
            loss_series=10,
            win_games=0,
            loss_games=20
        )
        
        assert standing.series_win_rate == 0.0
        assert standing.game_win_rate == 0.0
    
    @pytest.mark.unit
    def test_standing_with_special_characters_in_team_name(self):
        """Test Standing with special characters in team name."""
        special_team_name = "Team Liquid'"
        standing = Standing(team=special_team_name)
        
        assert standing.team == special_team_name
    
    @pytest.mark.integration
    def test_standings_sql_injection_protection(self, mock_leaguepedia_query, standings_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = standings_mock_data
        
        malicious_input = "'; DROP TABLE Standings; --"
        
        # Should not raise an exception and should escape the input
        standings = lp.get_standings(team=malicious_input)
        
        # Verify the input was escaped (single quotes doubled)
        call_kwargs = mock_leaguepedia_query.call_args[1] 
        assert "''" in call_kwargs['where']  # Escaped single quotes


if __name__ == "__main__":
    pytest.main([__file__])