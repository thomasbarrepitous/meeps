"""Tests for roster changes functionality in Leaguepedia parser."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List

import meeps as mp
from meeps.parsers.roster_changes_parser import RosterChange, RosterAction

from .conftest import TestConstants, assert_valid_dataclass_instance, assert_mock_called_with_table


class TestRosterChangesImports:
    """Test that roster changes functions are properly importable."""
    
    @pytest.mark.unit
    def test_roster_changes_functions_importable(self):
        """Test that all roster changes functions are available in the main module."""
        expected_functions = [
            'get_roster_changes',
            'get_team_roster_changes',
            'get_player_roster_changes',
            'get_recent_roster_changes',
            'get_roster_additions',
            'get_roster_removals',
            'get_retirements'
        ]
        
        for func_name in expected_functions:
            assert hasattr(mp, func_name), f"Function {func_name} is not importable"


class TestRosterActionEnum:
    """Test RosterAction enumeration."""
    
    @pytest.mark.unit
    def test_roster_action_enum_values(self):
        """Test that RosterAction enum has expected values."""
        expected_actions = {
            'ADD': 'Add',
            'REMOVE': 'Remove',
            'ROLE_CHANGE': 'Role Change',
            'SUBSTITUTE': 'Substitute',
            'LOAN': 'Loan',
            'TRANSFER': 'Transfer',
            'RETIREMENT': 'Retirement'
        }
        
        for attr_name, expected_value in expected_actions.items():
            assert hasattr(RosterAction, attr_name)
            assert getattr(RosterAction, attr_name).value == expected_value


class TestRosterChangeDataclass:
    """Test RosterChange dataclass functionality and computed properties."""
    
    @pytest.mark.unit
    def test_roster_change_initialization_complete(self):
        """Test RosterChange dataclass can be initialized with all fields."""
        change_date = datetime(2023, 11, 15)
        roster_change = RosterChange(
            date_sort=change_date,
            player=TestConstants.PLAYER_FAKER,
            direction="Join",
            team=TestConstants.TEAM_T1,
            role="Mid",
            roster_change_id="RC001",
            news_id="NEWS001",
            tournaments="LCK/2013 Season/Winter",
            status="Active"
        )
        
        assert_valid_dataclass_instance(roster_change, RosterChange, ['team', 'player', 'action'])
        assert roster_change.team == TestConstants.TEAM_T1
        assert roster_change.player == TestConstants.PLAYER_FAKER
        assert roster_change.action == "Join"  # Using backward compatibility property
        assert roster_change.date == change_date   # Using backward compatibility property
        assert roster_change.role == "Mid"
    
    @pytest.mark.unit
    def test_roster_change_direction_property(self):
        """Test direction property and backward compatibility action alias."""
        # Test join direction
        change_join = RosterChange(direction="Join")
        assert change_join.direction == "Join"
        assert change_join.action == "Join"  # Backward compatibility
        assert change_join.is_join is True
        assert change_join.is_leave is False
        
        # Test leave direction
        change_leave = RosterChange(direction="Leave")
        assert change_leave.direction == "Leave"
        assert change_leave.action == "Leave"  # Backward compatibility
        assert change_leave.is_join is False
        assert change_leave.is_leave is True
        
        # Test None direction
        change_none = RosterChange(direction=None)
        assert change_none.direction is None
        assert change_none.action is None
    
    @pytest.mark.unit
    def test_roster_change_is_addition_property(self):
        """Test is_addition property."""
        change_add = RosterChange(direction="Join")
        assert change_add.is_addition is True
        
        change_remove = RosterChange(direction="Leave")
        assert change_remove.is_addition is False
        
        change_none = RosterChange(direction=None)
        assert change_none.is_addition is False
    
    @pytest.mark.unit
    def test_roster_change_is_removal_property(self):
        """Test is_removal property."""
        change_remove = RosterChange(direction="Leave")
        assert change_remove.is_removal is True
        
        change_add = RosterChange(direction="Join")
        assert change_add.is_removal is False
        
        change_none = RosterChange(direction=None)
        assert change_none.is_removal is False
    
    @pytest.mark.unit
    def test_roster_change_boolean_field_handling(self):
        """Test boolean fields are properly handled."""
        roster_change = RosterChange(
            player_unlinked=True,
            is_gcd=False
        )
        
        assert roster_change.player_unlinked is True
        assert roster_change.is_gcd is False
        # Test backward compatibility property
        assert roster_change.is_retirement is None  # Not available in real API


class TestRosterChangesAPI:
    """Test roster changes API functions with mocked data."""
    
    @pytest.mark.integration
    def test_get_roster_changes_basic_call(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test basic get_roster_changes call returns properly parsed RosterChange objects."""
        mock_leaguepedia_query.return_value = roster_changes_mock_data
        
        changes = mp.get_roster_changes()
        
        assert len(changes) == 2
        assert all(isinstance(c, RosterChange) for c in changes)
        assert changes[0].team == TestConstants.TEAM_T1
        assert changes[0].player == TestConstants.PLAYER_FAKER
        assert changes[1].team == TestConstants.TEAM_G2
        assert changes[1].player == TestConstants.PLAYER_CAPS
        assert_mock_called_with_table(mock_leaguepedia_query, "RosterChanges")
    
    @pytest.mark.integration
    def test_get_roster_changes_with_team_filter(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_changes with team filter."""
        # Return only T1 changes
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        changes = mp.get_roster_changes(team=TestConstants.TEAM_T1)
        
        assert len(changes) == 1
        assert changes[0].team == TestConstants.TEAM_T1
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes team filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert f"Team='{TestConstants.TEAM_T1}'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_roster_changes_with_player_filter(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_changes with player filter."""
        # Return only Faker changes
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        changes = mp.get_roster_changes(player=TestConstants.PLAYER_FAKER)
        
        assert len(changes) == 1
        assert changes[0].player == TestConstants.PLAYER_FAKER
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes player filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert f"Player='{TestConstants.PLAYER_FAKER}'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_roster_changes_with_action_filter(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_changes with action filter."""
        # Return only Join actions
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        changes = mp.get_roster_changes(action="Join")
        
        assert len(changes) == 1
        assert changes[0].action == "Join"
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes action filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Direction='Join'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_roster_changes_with_date_range(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_changes with date range filters."""
        mock_leaguepedia_query.return_value = roster_changes_mock_data
        
        start_date = "2013-01-01"
        end_date = "2013-12-31"
        changes = mp.get_roster_changes(start_date=start_date, end_date=end_date)
        
        assert len(changes) == 2
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes date filters
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert f"Date_Sort >= '{start_date}'" in call_kwargs['where']
        assert f"Date_Sort <= '{end_date}'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_team_roster_changes(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_team_roster_changes convenience function."""
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        changes = mp.get_team_roster_changes(TestConstants.TEAM_T1)
        
        assert len(changes) == 1
        assert changes[0].team == TestConstants.TEAM_T1
        assert_mock_called_with_table(mock_leaguepedia_query, "RosterChanges")
    
    @pytest.mark.integration
    def test_get_player_roster_changes(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_player_roster_changes convenience function."""
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        changes = mp.get_player_roster_changes(TestConstants.PLAYER_FAKER)
        
        assert len(changes) == 1
        assert changes[0].player == TestConstants.PLAYER_FAKER
        assert_mock_called_with_table(mock_leaguepedia_query, "RosterChanges")
    
    @pytest.mark.integration
    @patch('meeps.parsers.roster_changes_parser.datetime')
    def test_get_recent_roster_changes(self, mock_datetime, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_recent_roster_changes with mocked datetime."""
        # Mock current time
        mock_now = datetime(2023, 12, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = timedelta  # Use real timedelta
        
        mock_leaguepedia_query.return_value = roster_changes_mock_data
        
        changes = mp.get_recent_roster_changes(days=30)
        
        assert len(changes) == 2
        mock_leaguepedia_query.assert_called_once()
        
        # Verify date range was calculated correctly (30 days back)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Date_Sort >= '2023-11-15'" in call_kwargs['where']  # 30 days before 2023-12-15
        assert "Date_Sort <= '2023-12-15'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_roster_additions(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_additions convenience function."""
        # Return only additions
        filtered_data = [roster_changes_mock_data[0]]
        mock_leaguepedia_query.return_value = filtered_data
        
        additions = mp.get_roster_additions()
        
        assert len(additions) == 1
        assert additions[0].action == "Join"
        mock_leaguepedia_query.assert_called_once()
        # Verify action filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Direction='Join'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_roster_removals(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_roster_removals convenience function."""
        # Return only removals
        filtered_data = [roster_changes_mock_data[1]]
        mock_leaguepedia_query.return_value = filtered_data
        
        removals = mp.get_roster_removals()
        
        assert len(removals) == 1
        assert removals[0].action == "Leave"
        mock_leaguepedia_query.assert_called_once()
        # Verify action filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Direction='Leave'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_retirements(self, mock_leaguepedia_query):
        """Test get_retirements function with retirement filter."""
        retirement_data = [{
            'Date_Sort': '2023-11-01T00:00:00Z',
            'Team': 'Former Team',
            'Player': 'RetiredPlayer',
            'Direction': 'Leave',
            'Role': 'Mid',
            'Status': 'Retired'
        }]
        mock_leaguepedia_query.return_value = retirement_data
        
        retirements = mp.get_retirements()
        
        assert len(retirements) == 1
        assert retirements[0].player == 'RetiredPlayer'
        mock_leaguepedia_query.assert_called_once()
        # Verify retirement filter is attempted (even if field doesn't exist)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "IsRetirement='Yes'" in call_kwargs['where']


class TestRosterChangesErrorHandling:
    """Test error handling in roster changes functionality."""
    
    @pytest.mark.integration
    def test_get_roster_changes_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to fetch roster changes"):
            mp.get_roster_changes()
    
    @pytest.mark.integration
    def test_get_retirements_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_retirements are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to fetch retirements"):
            mp.get_retirements()
    
    @pytest.mark.integration
    def test_get_roster_changes_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []
        
        changes = mp.get_roster_changes()
        
        assert changes == []
        assert isinstance(changes, list)


class TestRosterChangesEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_roster_change_with_special_characters_in_names(self):
        """Test RosterChange with special characters in team/player names."""
        special_team = "Team Liquid'"
        special_player = "Bjergsen"
        
        roster_change = RosterChange(team=special_team, player=special_player)
        
        assert roster_change.team == special_team
        assert roster_change.player == special_player
    
    @pytest.mark.unit
    def test_roster_change_with_none_date(self):
        """Test RosterChange with None date."""
        roster_change = RosterChange(date_sort=None)
        
        assert roster_change.date is None
    
    @pytest.mark.unit
    def test_roster_change_role_variations(self):
        """Test RosterChange with various role values."""
        roles = ["Top", "Jungle", "Mid", "Bot", "Support", "Coach", "Substitute"]
        
        for role in roles:
            roster_change = RosterChange(role=role)
            assert roster_change.role == role
    
    @pytest.mark.integration
    def test_roster_changes_sql_injection_protection(self, mock_leaguepedia_query, roster_changes_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = roster_changes_mock_data
        
        malicious_input = "'; DROP TABLE RosterChanges; --"
        
        # Should not raise an exception and should escape the input
        changes = mp.get_roster_changes(team=malicious_input)
        
        # Verify the input was escaped (single quotes doubled)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']  # Escaped single quotes
    
    @pytest.mark.unit
    def test_roster_change_additional_real_fields(self):
        """Test additional real API fields."""
        roster_change = RosterChange(
            status="Active",
            current_team_priority=1,
            already_joined="Yes"
        )
        
        assert roster_change.status == "Active"
        assert roster_change.current_team_priority == 1
        assert roster_change.already_joined == "Yes"
    
    @pytest.mark.integration
    @patch('meeps.parsers.roster_changes_parser.datetime')
    def test_get_recent_roster_changes_custom_days(self, mock_datetime, mock_leaguepedia_query, roster_changes_mock_data):
        """Test get_recent_roster_changes with custom day count."""
        mock_now = datetime(2023, 12, 15)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = timedelta
        
        mock_leaguepedia_query.return_value = roster_changes_mock_data
        
        changes = mp.get_recent_roster_changes(days=7)  # Last 7 days
        
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Date_Sort >= '2023-12-08'" in call_kwargs['where']  # 7 days before 2023-12-15
    
    @pytest.mark.unit
    def test_roster_change_additional_fields(self):
        """Test additional fields like news_id, roster_change_id."""
        roster_change = RosterChange(
            roster_change_id="RC001",
            news_id="NEWS001",
            source="Official announcement"
        )
        
        assert roster_change.roster_change_id == "RC001"
        assert roster_change.news_id == "NEWS001"
        assert roster_change.source == "Official announcement"


class TestRosterChangesDataParsing:
    """Test data parsing from API responses."""
    
    @pytest.mark.unit
    def test_roster_change_boolean_parsing(self):
        """Test that boolean fields are properly parsed."""
        # This would typically test the internal parsing function
        roster_change = RosterChange(
            player_unlinked=True,
            is_gcd=False
        )
        
        assert isinstance(roster_change.player_unlinked, bool)
        assert isinstance(roster_change.is_gcd, bool)
    
    @pytest.mark.unit
    def test_roster_change_date_parsing(self):
        """Test date field parsing."""
        test_date = datetime(2023, 11, 15)
        roster_change = RosterChange(date_sort=test_date)
        
        assert isinstance(roster_change.date, datetime)
        assert roster_change.date == test_date


if __name__ == "__main__":
    pytest.main([__file__])
