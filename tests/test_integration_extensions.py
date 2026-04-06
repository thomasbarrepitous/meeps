"""Integration tests for extended Leaguepedia parser functionality."""

import pytest
from unittest.mock import Mock, patch
from typing import List, Any, Dict

import meeps as mp
from meeps.parsers.standings_parser import Standing
from meeps.parsers.champions_parser import Champion
from meeps.parsers.items_parser import Item
from meeps.parsers.roster_changes_parser import RosterChange

from .conftest import TestConstants, TestDataFactory


class TestCrossModuleIntegration:
    """Test integration between different parser modules."""
    
    @pytest.mark.integration
    def test_all_parsers_use_same_query_interface(self, mock_leaguepedia_query):
        """Test that all parsers use the same underlying query interface."""
        mock_leaguepedia_query.return_value = []
        
        # Call functions from each parser module
        mp.get_standings()
        mp.get_champions()
        mp.get_items()
        mp.get_roster_changes()
        
        # Verify all calls went through the same mock
        assert mock_leaguepedia_query.call_count == 4
        
        # Verify all calls have proper structure
        for call in mock_leaguepedia_query.call_args_list:
            assert 'tables' in call[1]
            assert 'fields' in call[1]
    
    @pytest.mark.integration
    def test_error_handling_consistency(self, mock_leaguepedia_query):
        """Test that all parsers handle errors consistently."""
        mock_leaguepedia_query.side_effect = Exception("Network error")
        
        # All should raise RuntimeError with descriptive message
        with pytest.raises(RuntimeError, match="Failed to fetch standings"):
            mp.get_standings()
        
        with pytest.raises(RuntimeError, match="Failed to fetch champions"):
            mp.get_champions()
        
        with pytest.raises(RuntimeError, match="Failed to fetch items"):
            mp.get_items()
        
        with pytest.raises(RuntimeError, match="Failed to fetch roster changes"):
            mp.get_roster_changes()


class TestComplexQueryScenarios:
    """Test complex query scenarios combining multiple parameters."""
    
    @pytest.mark.integration
    def test_standings_with_multiple_filters(self, mock_leaguepedia_query, test_data_factory):
        """Test standings query with multiple filters."""
        mock_data = test_data_factory.create_standings_mock_response()
        mock_leaguepedia_query.return_value = mock_data
        
        standings = mp.get_standings(
            overview_page=TestConstants.LCK_2024_SUMMER,
            team=TestConstants.TEAM_T1
        )
        
        assert len(standings) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        
        # Verify both filters are applied
        assert TestConstants.LCK_2024_SUMMER in call_kwargs['where']
        assert TestConstants.TEAM_T1 in call_kwargs['where']
        assert " AND " in call_kwargs['where']  # Multiple conditions
    
    @pytest.mark.integration
    def test_champions_with_resource_and_attributes(self, mock_leaguepedia_query, test_data_factory):
        """Test champions query with both resource and attributes filters."""
        mock_data = test_data_factory.create_champions_mock_response()
        mock_leaguepedia_query.return_value = mock_data
        
        champions = mp.get_champions(resource="Mana", attributes="Marksman")
        
        assert len(champions) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        
        # Verify both filters are applied
        assert "Resource='Mana'" in call_kwargs['where']
        assert "LIKE '%Marksman%'" in call_kwargs['where']
        assert " AND " in call_kwargs['where']
    
    @pytest.mark.integration
    def test_roster_changes_with_date_range_and_team(self, mock_leaguepedia_query, test_data_factory):
        """Test roster changes query with date range and team filter."""
        mock_data = test_data_factory.create_roster_changes_mock_response()
        mock_leaguepedia_query.return_value = mock_data
        
        changes = mp.get_roster_changes(
            team=TestConstants.TEAM_T1,
            start_date="2013-01-01",
            end_date="2013-12-31"
        )
        
        assert len(changes) == 2
        call_kwargs = mock_leaguepedia_query.call_args[1]
        
        # Verify all filters are applied
        assert f"Team='{TestConstants.TEAM_T1}'" in call_kwargs['where']
        assert "Date_Sort >= '2013-01-01'" in call_kwargs['where']
        assert "Date_Sort <= '2013-12-31'" in call_kwargs['where']


class TestDataConsistency:
    """Test data consistency across different modules."""
    
    @pytest.mark.integration
    def test_consistent_field_parsing(self, mock_leaguepedia_query, test_data_factory):
        """Test that similar data types are parsed consistently across modules."""
        # Test string fields
        standings_data = test_data_factory.create_standings_mock_response()
        mock_leaguepedia_query.return_value = standings_data
        standings = mp.get_standings()
        
        assert all(isinstance(s.team, str) for s in standings if s.team)
        assert all(isinstance(s.overview_page, str) for s in standings if s.overview_page)
        
        # Test integer fields
        champions_data = test_data_factory.create_champions_mock_response()
        mock_leaguepedia_query.return_value = champions_data
        champions = mp.get_champions()
        
        # Verify numeric fields are properly typed
        for champion in champions:
            if champion.be is not None:
                assert isinstance(champion.be, int)
            if champion.rp is not None:
                assert isinstance(champion.rp, int)
    
    @pytest.mark.integration
    def test_consistent_error_response_format(self, mock_leaguepedia_query):
        """Test that all modules return consistent error formats."""
        test_cases = [
            (mp.get_standings, "Failed to fetch standings"),
            (mp.get_champions, "Failed to fetch champions"),
            (mp.get_items, "Failed to fetch items"),
            (mp.get_roster_changes, "Failed to fetch roster changes")
        ]
        
        for func, expected_message in test_cases:
            mock_leaguepedia_query.side_effect = Exception("Test error")
            
            with pytest.raises(RuntimeError) as exc_info:
                func()
            
            assert expected_message in str(exc_info.value)
            mock_leaguepedia_query.reset_mock()


class TestPerformanceAndScaling:
    """Test performance-related aspects and scaling behavior."""
    
    @pytest.mark.integration
    def test_large_dataset_handling(self, mock_leaguepedia_query):
        """Test handling of large datasets."""
        # Create large mock dataset
        large_standings_data = []
        for i in range(100):
            large_standings_data.append({
                'Team': f'Team{i}',
                'OverviewPage': TestConstants.LCK_2024_SUMMER,
                'Place': str(i + 1),
                'WinSeries': str(20 - i),
                'LossSeries': str(i),
                'WinGames': str(40 - i),
                'LossGames': str(i * 2)
            })
        
        mock_leaguepedia_query.return_value = large_standings_data
        
        standings = mp.get_standings()
        
        assert len(standings) == 100
        assert all(isinstance(s, Standing) for s in standings)
        
        # Verify data integrity for first and last items
        assert standings[0].team == 'Team0'
        assert standings[99].team == 'Team99'
    
    @pytest.mark.integration
    def test_empty_dataset_handling(self, mock_leaguepedia_query):
        """Test handling of empty datasets across all modules."""
        mock_leaguepedia_query.return_value = []
        
        # All should return empty lists
        assert mp.get_standings() == []
        assert mp.get_champions() == []
        assert mp.get_items() == []
        assert mp.get_roster_changes() == []
    
    @pytest.mark.integration
    def test_partial_data_handling(self, mock_leaguepedia_query):
        """Test handling of partial/incomplete data."""
        # Test with minimal data
        minimal_standings = [{
            'Team': TestConstants.TEAM_T1,
            'Place': '1'
            # Missing other fields
        }]
        
        mock_leaguepedia_query.return_value = minimal_standings
        standings = mp.get_standings()
        
        assert len(standings) == 1
        assert standings[0].team == TestConstants.TEAM_T1
        assert standings[0].place == 1
        # Other fields should be None
        assert standings[0].win_series is None
        assert standings[0].loss_series is None


class TestAPIContractCompliance:
    """Test that all modules comply with expected API contracts."""
    
    @pytest.mark.integration
    def test_return_type_consistency(self, mock_leaguepedia_query, test_data_factory):
        """Test that all functions return expected types."""
        # Test list-returning functions
        list_functions = [
            (mp.get_standings, test_data_factory.create_standings_mock_response()),
            (mp.get_champions, test_data_factory.create_champions_mock_response()),
            (mp.get_items, test_data_factory.create_items_mock_response()),
            (mp.get_roster_changes, test_data_factory.create_roster_changes_mock_response())
        ]
        
        for func, mock_data in list_functions:
            mock_leaguepedia_query.return_value = mock_data
            result = func()
            
            assert isinstance(result, list)
            if result:  # If not empty
                assert len(result) > 0
            
            mock_leaguepedia_query.reset_mock()
        
        # Test single-item returning functions
        single_item_functions = [
            (mp.get_champion_by_name, test_data_factory.create_champions_mock_response()[:1]),
            (mp.get_item_by_name, test_data_factory.create_items_mock_response()[:1])
        ]
        
        for func, mock_data in single_item_functions:
            mock_leaguepedia_query.return_value = mock_data
            result = func("TestName")
            
            assert result is not None
            mock_leaguepedia_query.reset_mock()
    
    @pytest.mark.integration
    def test_parameter_validation(self, mock_leaguepedia_query, test_data_factory):
        """Test parameter validation across modules."""
        mock_leaguepedia_query.return_value = []
        
        # Test None parameters don't break queries
        mp.get_standings(overview_page=None, team=None)
        mp.get_champions(resource=None, attributes=None)
        mp.get_roster_changes(team=None, player=None, action=None)
        
        # All should complete without errors
        assert mock_leaguepedia_query.call_count == 3


class TestRealWorldScenarios:
    """Test scenarios that mimic real-world usage patterns."""
    
    @pytest.mark.integration
    def test_tournament_analysis_workflow(self, mock_leaguepedia_query, test_data_factory):
        """Test a complete tournament analysis workflow."""
        # Step 1: Get tournament standings
        standings_data = test_data_factory.create_standings_mock_response()
        mock_leaguepedia_query.return_value = standings_data
        
        standings = mp.get_tournament_standings(TestConstants.LCK_2024_SUMMER)
        top_team = standings[0].team  # T1
        
        # Step 2: Get roster changes for top team
        roster_data = test_data_factory.create_roster_changes_mock_response()
        mock_leaguepedia_query.return_value = [roster_data[0]]  # T1 data only
        
        roster_changes = mp.get_team_roster_changes(top_team)
        
        # Step 3: Verify workflow completion
        assert len(standings) == 2
        assert top_team == TestConstants.TEAM_T1
        assert len(roster_changes) == 1
        assert roster_changes[0].team == top_team
        
        # Verify correct number of API calls
        assert mock_leaguepedia_query.call_count == 2
    
    @pytest.mark.integration
    def test_champion_and_items_analysis(self, mock_leaguepedia_query, test_data_factory):
        """Test champion and items analysis workflow."""
        # Step 1: Get all marksman champions
        champions_data = test_data_factory.create_champions_mock_response()
        mock_leaguepedia_query.return_value = [champions_data[0]]  # Jinx only
        
        marksmen = mp.get_champions_by_attributes("Marksman")
        
        # Step 2: Get AD items for marksmen
        items_data = test_data_factory.create_items_mock_response()
        mock_leaguepedia_query.return_value = [items_data[0]]  # Infinity Edge only
        
        ad_items = mp.get_ad_items()
        
        # Step 3: Verify analysis results
        assert len(marksmen) == 1
        assert marksmen[0].name == TestConstants.CHAMPION_JINX
        assert marksmen[0].is_ranged is True
        
        assert len(ad_items) == 1
        assert ad_items[0].name == TestConstants.ITEM_INFINITY_EDGE
        assert ad_items[0].provides_ad is True
        
        # Verify API interaction
        assert mock_leaguepedia_query.call_count == 2


class TestConcurrentAccess:
    """Test behavior under concurrent access patterns."""
    
    @pytest.mark.integration
    def test_multiple_simultaneous_queries(self, mock_leaguepedia_query, test_data_factory):
        """Test multiple queries in rapid succession."""
        # Set up different mock responses for different calls
        mock_responses = [
            test_data_factory.create_standings_mock_response(),
            test_data_factory.create_champions_mock_response(),
            test_data_factory.create_items_mock_response(),
            test_data_factory.create_roster_changes_mock_response()
        ]
        
        mock_leaguepedia_query.side_effect = mock_responses
        
        # Execute multiple queries rapidly
        results = []
        results.append(mp.get_standings())
        results.append(mp.get_champions())
        results.append(mp.get_items())
        results.append(mp.get_roster_changes())
        
        # Verify all queries completed successfully
        assert len(results) == 4
        assert all(isinstance(result, list) for result in results)
        assert all(len(result) > 0 for result in results)
        
        # Verify all mock calls were made
        assert mock_leaguepedia_query.call_count == 4


class TestEdgeCasesIntegration:
    """Test edge cases that span multiple modules."""
    
    @pytest.mark.integration
    def test_special_characters_across_modules(self, mock_leaguepedia_query):
        """Test special character handling across all modules."""
        mock_leaguepedia_query.return_value = []
        
        special_chars_inputs = [
            "Team Liquid'",
            "Björgsen", 
            "G2 Esports",
            "100 Thieves",
            "T1"
        ]
        
        for special_input in special_chars_inputs:
            # Should not raise exceptions
            mp.get_standings(team=special_input)
            mp.get_roster_changes(team=special_input)
            
            # Verify SQL injection protection
            call_kwargs = mock_leaguepedia_query.call_args[1]
            if "'" in special_input:
                assert "''" in call_kwargs['where']  # Escaped quotes
            
            mock_leaguepedia_query.reset_mock()
    
    @pytest.mark.integration
    def test_unicode_handling(self, mock_leaguepedia_query):
        """Test Unicode character handling across modules."""
        mock_leaguepedia_query.return_value = []
        
        unicode_inputs = [
            "한국어팀",  # Korean
            "中文队伍",  # Chinese
            "Ñoñó",     # Spanish with tildes
            "Café"      # French with accents
        ]
        
        for unicode_input in unicode_inputs:
            # Should handle Unicode without errors
            mp.get_standings(team=unicode_input)
            mp.get_roster_changes(player=unicode_input)
            
            # Verify call was made
            assert mock_leaguepedia_query.called
            mock_leaguepedia_query.reset_mock()


if __name__ == "__main__":
    pytest.main([__file__])