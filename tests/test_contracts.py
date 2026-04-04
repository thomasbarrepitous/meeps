"""Tests for the contracts parser module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from meeps.parsers.contracts_parser import (
    Contract,
    get_contracts,
    get_player_contracts,
    get_team_contracts,
    get_active_contracts,
    get_expiring_contracts,
    get_contract_removals,
    _parse_contract_data,
)
from .conftest import TestConstants, assert_valid_dataclass_instance


class TestContractDataclass:
    """Test the Contract dataclass and its properties."""

    @pytest.mark.unit
    def test_contract_dataclass_creation(self):
        """Test Contract dataclass can be created with all fields."""
        contract = Contract(
            player="Faker",
            team="T1",
            contract_end=datetime(2025, 12, 31),
            contract_end_text="December 31, 2025",
            is_removal=False,
            news_id="CONTRACT001"
        )
        
        assert contract.player == "Faker"
        assert contract.team == "T1"
        assert contract.contract_end == datetime(2025, 12, 31)
        assert contract.contract_end_text == "December 31, 2025"
        assert contract.is_removal is False
        assert contract.news_id == "CONTRACT001"

    @pytest.mark.unit
    def test_contract_dataclass_optional_fields(self):
        """Test Contract dataclass works with None values."""
        contract = Contract()
        
        assert contract.player is None
        assert contract.team is None
        assert contract.contract_end is None
        assert contract.contract_end_text is None
        assert contract.is_removal is None
        assert contract.news_id is None

    @pytest.mark.unit
    def test_is_active_property(self):
        """Test the is_active property logic."""
        # Future contract (should be active)
        future_contract = Contract(
            contract_end=datetime.now(timezone.utc) + timedelta(days=30),
            is_removal=False
        )
        assert future_contract.is_active is True

        # Past contract (should be inactive)
        past_contract = Contract(
            contract_end=datetime.now(timezone.utc) - timedelta(days=30),
            is_removal=False
        )
        assert past_contract.is_active is False

        # Removal contract (should be inactive)
        removal_contract = Contract(
            contract_end=datetime.now(timezone.utc) + timedelta(days=30),
            is_removal=True
        )
        assert removal_contract.is_active is False

        # No end date
        no_date_contract = Contract(is_removal=False)
        assert no_date_contract.is_active is None

    @pytest.mark.unit
    def test_is_expired_property(self):
        """Test the is_expired property logic."""
        # Future contract (not expired)
        future_contract = Contract(
            contract_end=datetime.now(timezone.utc) + timedelta(days=30)
        )
        assert future_contract.is_expired is False

        # Past contract (expired)
        past_contract = Contract(
            contract_end=datetime.now(timezone.utc) - timedelta(days=30)
        )
        assert past_contract.is_expired is True

        # No end date
        no_date_contract = Contract()
        assert no_date_contract.is_expired is None

    @pytest.mark.unit
    def test_days_until_expiry_property(self):
        """Test the days_until_expiry property logic."""
        # Future contract - allow for minor time differences
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        future_contract = Contract(contract_end=future_date)
        assert 29 <= future_contract.days_until_expiry <= 30

        # Past contract (negative days)
        past_date = datetime.now(timezone.utc) - timedelta(days=15)
        past_contract = Contract(contract_end=past_date)
        assert 29 <= future_contract.days_until_expiry <= 30  # Should be positive
        assert -16 <= past_contract.days_until_expiry <= -14   # Should be negative (allow for minor differences)

        # No end date
        no_date_contract = Contract()
        assert no_date_contract.days_until_expiry is None


class TestContractParser:
    """Test the contract parsing functions."""

    @pytest.mark.unit
    def test_parse_contract_data(self):
        """Test _parse_contract_data function."""
        raw_data = {
            'Player': 'Faker',
            'Team': 'T1',
            'ContractEnd': '2025-12-31T23:59:59Z',
            'ContractEndText': 'December 31, 2025',
            'IsRemoval': '0',
            'NewsId': 'CONTRACT001'
        }
        
        contract = _parse_contract_data(raw_data)
        
        assert isinstance(contract, Contract)
        assert contract.player == 'Faker'
        assert contract.team == 'T1'
        # Check date without timezone to avoid UTC/local time issues
        assert contract.contract_end.year == 2025
        assert contract.contract_end.month == 12
        assert contract.contract_end.day == 31
        assert contract.contract_end.hour == 23
        assert contract.contract_end.minute == 59
        assert contract.contract_end.second == 59
        assert contract.contract_end_text == 'December 31, 2025'
        assert contract.is_removal is False
        assert contract.news_id == 'CONTRACT001'

    @pytest.mark.unit
    def test_parse_contract_data_with_removal(self):
        """Test parsing contract removal data."""
        raw_data = {
            'Player': 'Jankos',
            'Team': 'G2 Esports',
            'ContractEnd': '2023-12-31T23:59:59Z',
            'ContractEndText': 'December 31, 2023',
            'IsRemoval': '1',
            'NewsId': 'CONTRACT003'
        }
        
        contract = _parse_contract_data(raw_data)
        
        assert contract.is_removal is True
        assert contract.player == 'Jankos'

    @pytest.mark.unit
    def test_parse_contract_data_with_missing_fields(self):
        """Test parsing with missing/empty fields."""
        raw_data = {
            'Player': 'TestPlayer',
            'Team': '',
            'ContractEnd': None,
            'ContractEndText': '',
            'IsRemoval': '',
            'NewsId': ''
        }
        
        contract = _parse_contract_data(raw_data)
        
        assert contract.player == 'TestPlayer'
        assert contract.team == ''
        assert contract.contract_end is None
        assert contract.is_removal is None

    @pytest.mark.unit
    def test_parse_contract_data_invalid_date(self):
        """Test parsing with invalid date format."""
        raw_data = {
            'Player': 'TestPlayer',
            'Team': 'TestTeam',
            'ContractEnd': 'invalid-date',
            'ContractEndText': 'Invalid Date',
            'IsRemoval': '0',
            'NewsId': 'TEST001'
        }
        
        contract = _parse_contract_data(raw_data)
        
        assert contract.contract_end is None  # Should handle invalid date gracefully


class TestContractQueries:
    """Test the contract query functions."""

    @pytest.mark.integration
    def test_get_contracts_all(self, mock_leaguepedia_query, contracts_mock_data):
        """Test getting all contracts."""
        mock_leaguepedia_query.return_value = contracts_mock_data
        
        contracts = get_contracts()
        
        assert len(contracts) == 4
        assert all(isinstance(contract, Contract) for contract in contracts)
        mock_leaguepedia_query.assert_called_once()
        
        # Verify the query parameters
        call_args = mock_leaguepedia_query.call_args
        assert call_args[1]['tables'] == 'Contracts'
        # Check that all required fields are in the fields parameter
        expected_fields = ['Player', 'Team', 'ContractEnd', 'ContractEndText', 'IsRemoval', 'NewsId']
        actual_fields = call_args[1]['fields']
        for field in expected_fields:
            assert field in actual_fields

    @pytest.mark.integration
    def test_get_contracts_by_player(self, mock_leaguepedia_query, contracts_mock_data):
        """Test getting contracts for a specific player."""
        # Filter mock data for Faker
        faker_contracts = [c for c in contracts_mock_data if c['Player'] == 'Faker']
        mock_leaguepedia_query.return_value = faker_contracts
        
        contracts = get_contracts(player="Faker")
        
        assert len(contracts) == 1
        assert contracts[0].player == "Faker"
        assert contracts[0].team == "T1"
        
        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "Contracts.Player='Faker'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contracts_by_team(self, mock_leaguepedia_query, contracts_mock_data):
        """Test getting contracts for a specific team."""
        # Filter mock data for G2 Esports
        g2_contracts = [c for c in contracts_mock_data if c['Team'] == 'G2 Esports']
        mock_leaguepedia_query.return_value = g2_contracts
        
        contracts = get_contracts(team="G2 Esports")
        
        assert len(contracts) == 2
        assert all(contract.team == "G2 Esports" for contract in contracts)
        
        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "Contracts.Team='G2 Esports'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contracts_exclude_removals(self, mock_leaguepedia_query, contracts_mock_data):
        """Test getting contracts excluding removals."""
        # Filter mock data to exclude removals
        active_contracts = [c for c in contracts_mock_data if c['IsRemoval'] != '1']
        mock_leaguepedia_query.return_value = active_contracts
        
        contracts = get_contracts(include_removals=False)
        
        assert len(contracts) == 3
        assert all(not contract.is_removal for contract in contracts)
        
        # Verify the where clause excludes removals
        call_args = mock_leaguepedia_query.call_args
        assert "IsRemoval IS NULL OR Contracts.IsRemoval='0'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contracts_active_only(self, mock_leaguepedia_query, contracts_mock_data):
        """Test getting only active contracts."""
        # Filter mock data for future contracts only
        future_contracts = [c for c in contracts_mock_data 
                          if c['ContractEnd'] > datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                          and c['IsRemoval'] != '1']
        mock_leaguepedia_query.return_value = future_contracts
        
        contracts = get_contracts(active_only=True)
        
        # Verify the where clause includes date filter
        call_args = mock_leaguepedia_query.call_args
        assert "ContractEnd >=" in call_args[1]['where']
        assert "IsRemoval IS NULL OR Contracts.IsRemoval='0'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contracts_sql_injection_protection(self, mock_leaguepedia_query, contracts_mock_data):
        """Test that SQL injection is prevented by escaping quotes."""
        mock_leaguepedia_query.return_value = []
        
        # Try to inject SQL with quotes
        get_contracts(player="Faker'; DROP TABLE Contracts; --")
        
        # Verify the quotes were escaped
        call_args = mock_leaguepedia_query.call_args
        assert "Faker''; DROP TABLE Contracts; --" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_player_contracts(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_player_contracts helper function."""
        faker_contracts = [c for c in contracts_mock_data if c['Player'] == 'Faker']
        mock_leaguepedia_query.return_value = faker_contracts
        
        contracts = get_player_contracts("Faker")
        
        assert len(contracts) == 1
        assert contracts[0].player == "Faker"

    @pytest.mark.integration
    def test_get_team_contracts(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_team_contracts helper function."""
        g2_contracts = [c for c in contracts_mock_data if c['Team'] == 'G2 Esports']
        mock_leaguepedia_query.return_value = g2_contracts
        
        contracts = get_team_contracts("G2 Esports")
        
        assert len(contracts) == 2
        assert all(contract.team == "G2 Esports" for contract in contracts)

    @pytest.mark.integration
    def test_get_team_contracts_active_only(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_team_contracts with active_only flag."""
        g2_active_contracts = [c for c in contracts_mock_data 
                             if c['Team'] == 'G2 Esports' and c['IsRemoval'] != '1']
        mock_leaguepedia_query.return_value = g2_active_contracts
        
        contracts = get_team_contracts("G2 Esports", active_only=True)
        
        # Verify active_only was applied
        call_args = mock_leaguepedia_query.call_args
        assert "ContractEnd >=" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_active_contracts(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_active_contracts helper function."""
        active_contracts = [c for c in contracts_mock_data if c['IsRemoval'] != '1']
        mock_leaguepedia_query.return_value = active_contracts
        
        contracts = get_active_contracts()
        
        assert len(contracts) == 3
        
        # Verify active_only=True was used
        call_args = mock_leaguepedia_query.call_args
        assert "ContractEnd >=" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_expiring_contracts(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_expiring_contracts function."""
        # Mock only contracts expiring soon
        expiring_contracts = [contracts_mock_data[1]]  # Caps contract expires 2024-11-30
        mock_leaguepedia_query.return_value = expiring_contracts
        
        contracts = get_expiring_contracts(days=365)  # Look ahead 1 year
        
        # Verify the query includes date range
        call_args = mock_leaguepedia_query.call_args
        assert "ContractEnd >=" in call_args[1]['where']
        assert "ContractEnd <=" in call_args[1]['where']
        assert "IsRemoval IS NULL OR Contracts.IsRemoval='0'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contract_removals(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_contract_removals function."""
        removal_contracts = [c for c in contracts_mock_data if c['IsRemoval'] == '1']
        mock_leaguepedia_query.return_value = removal_contracts
        
        contracts = get_contract_removals()
        
        assert len(contracts) == 1
        assert contracts[0].is_removal is True
        assert contracts[0].player == "Jankos"
        
        # Verify the where clause filters for removals
        call_args = mock_leaguepedia_query.call_args
        assert "Contracts.IsRemoval='1'" in call_args[1]['where']

    @pytest.mark.integration
    def test_get_contract_removals_by_player(self, mock_leaguepedia_query, contracts_mock_data):
        """Test get_contract_removals with player filter."""
        jankos_removals = [c for c in contracts_mock_data 
                          if c['Player'] == 'Jankos' and c['IsRemoval'] == '1']
        mock_leaguepedia_query.return_value = jankos_removals
        
        contracts = get_contract_removals(player="Jankos")
        
        assert len(contracts) == 1
        assert contracts[0].player == "Jankos"
        assert contracts[0].is_removal is True


class TestContractErrorHandling:
    """Test error handling in contract functions."""

    @pytest.mark.unit
    def test_get_contracts_api_error(self, mock_leaguepedia_query):
        """Test error handling when API call fails."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch contracts"):
            get_contracts()

    @pytest.mark.unit
    def test_get_expiring_contracts_api_error(self, mock_leaguepedia_query):
        """Test error handling in get_expiring_contracts."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch expiring contracts"):
            get_expiring_contracts()

    @pytest.mark.unit
    def test_get_contract_removals_api_error(self, mock_leaguepedia_query):
        """Test error handling in get_contract_removals."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch contract removals"):
            get_contract_removals()


class TestContractDataValidation:
    """Test data validation and edge cases."""

    @pytest.mark.unit
    def test_contract_with_empty_response(self, mock_leaguepedia_query):
        """Test handling empty API response."""
        mock_leaguepedia_query.return_value = []
        
        contracts = get_contracts()
        
        assert contracts == []

    @pytest.mark.integration
    def test_contracts_data_structure_validation(self, mock_leaguepedia_query, contracts_mock_data):
        """Test that returned contracts have expected structure."""
        mock_leaguepedia_query.return_value = contracts_mock_data
        
        contracts = get_contracts()
        
        for contract in contracts:
            assert_valid_dataclass_instance(
                contract, 
                Contract, 
                ['player', 'team', 'contract_end', 'contract_end_text', 'is_removal', 'news_id']
            )

    @pytest.mark.integration 
    def test_contracts_ordering(self, mock_leaguepedia_query, contracts_mock_data):
        """Test that contracts are ordered correctly."""
        mock_leaguepedia_query.return_value = contracts_mock_data
        
        get_contracts()
        
        # Verify order_by parameter
        call_args = mock_leaguepedia_query.call_args
        assert call_args[1]['order_by'] == 'Contracts.ContractEnd DESC'