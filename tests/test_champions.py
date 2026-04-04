"""Tests for champions functionality in Leaguepedia parser."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from typing import List

import meeps as lp
from meeps.parsers.champions_parser import Champion
from meeps.enums import ChampionResource, ChampionAttribute

from .conftest import TestConstants, assert_valid_dataclass_instance, assert_mock_called_with_table


class TestChampionsImports:
    """Test that champions functions are properly importable."""
    
    @pytest.mark.unit
    def test_champions_functions_importable(self):
        """Test that all champions functions are available in the main module."""
        expected_functions = [
            'get_champions',
            'get_champion_by_name',
            'get_champions_by_attributes',
            'get_champions_by_resource',
            'get_melee_champions',
            'get_ranged_champions'
        ]
        
        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"


class TestChampionDataclass:
    """Test Champion dataclass functionality and computed properties."""
    
    @pytest.mark.unit
    def test_champion_initialization_complete(self):
        """Test Champion dataclass can be initialized with all fields."""
        release_date = datetime(2013, 10, 10)
        champion = Champion(
            name=TestConstants.CHAMPION_JINX,
            title="The Loose Cannon",
            release_date=release_date,
            be=6300,
            rp=975,
            attributes="Marksman",
            resource="Mana",
            real_name="Jinx",
            health=610.0,
            attack_damage=59.0,
            attack_range=525.0,
            movespeed=325.0,
            armor=28.0,
            magic_resist=30.0
        )
        
        assert_valid_dataclass_instance(champion, Champion, ['name', 'attack_range'])
        assert champion.name == TestConstants.CHAMPION_JINX
        assert champion.title == "The Loose Cannon"
        assert champion.release_date == release_date
        assert champion.be == 6300
        assert champion.rp == 975
        assert champion.attributes == "Marksman"
        assert champion.resource == "Mana"
        assert champion.attack_range == 525.0
    
    @pytest.mark.unit
    def test_champion_is_ranged_property(self):
        """Test Champion is_ranged property for ranged champion."""
        champion = Champion(
            name=TestConstants.CHAMPION_JINX,
            attack_range=525.0  # > 200, should be ranged
        )
        
        assert champion.is_ranged is True
        assert champion.is_melee is False
    
    @pytest.mark.unit
    def test_champion_is_melee_property(self):
        """Test Champion is_melee property for melee champion."""
        champion = Champion(
            name=TestConstants.CHAMPION_YASUO,
            attack_range=175.0  # <= 200, should be melee
        )
        
        assert champion.is_melee is True
        assert champion.is_ranged is False
    
    @pytest.mark.unit
    def test_champion_range_boundary_conditions(self):
        """Test edge cases for melee/ranged classification."""
        # Exactly 200 range should be melee
        champion_200 = Champion(name="TestChamp", attack_range=200.0)
        assert champion_200.is_melee is True
        assert champion_200.is_ranged is False
        
        # Just over 200 should be ranged
        champion_201 = Champion(name="TestChamp", attack_range=201.0)
        assert champion_201.is_ranged is True
        assert champion_201.is_melee is False
    
    @pytest.mark.unit
    def test_champion_attributes_list_property(self):
        """Test attributes_list property correctly parses comma-separated attributes."""
        champion = Champion(
            name=TestConstants.CHAMPION_YASUO,
            attributes="Fighter,Assassin"
        )
        
        attributes_list = champion.attributes_list
        assert isinstance(attributes_list, list)
        assert len(attributes_list) == 2
        assert "Fighter" in attributes_list
        assert "Assassin" in attributes_list
    
    @pytest.mark.unit
    def test_champion_attributes_list_single_attribute(self):
        """Test attributes_list with single attribute."""
        champion = Champion(
            name=TestConstants.CHAMPION_JINX,
            attributes="Marksman"
        )
        
        attributes_list = champion.attributes_list
        assert attributes_list == ["Marksman"]
    
    @pytest.mark.unit
    def test_champion_attributes_list_empty(self):
        """Test attributes_list with no attributes."""
        champion = Champion(name="TestChamp", attributes=None)
        
        attributes_list = champion.attributes_list
        assert attributes_list == []
    
    @pytest.mark.unit
    def test_champion_attributes_list_with_spaces(self):
        """Test attributes_list properly handles spaces around commas."""
        champion = Champion(
            name="TestChamp",
            attributes="Fighter, Assassin, Tank"
        )
        
        attributes_list = champion.attributes_list
        assert len(attributes_list) == 3
        assert all(attr.strip() == attr for attr in attributes_list)  # No leading/trailing spaces
        assert "Fighter" in attributes_list
        assert "Assassin" in attributes_list
        assert "Tank" in attributes_list
    
    @pytest.mark.unit
    def test_champion_properties_with_none_values(self):
        """Test that properties handle None values gracefully."""
        champion = Champion(name="TestChamp")
        
        assert champion.is_ranged is None
        assert champion.is_melee is None
        assert champion.attributes_list == []


class TestChampionsAPI:
    """Test champions API functions with mocked data."""
    
    @pytest.mark.integration
    def test_get_champions_basic_call(self, mock_leaguepedia_query, champions_mock_data):
        """Test basic get_champions call returns properly parsed Champion objects."""
        mock_leaguepedia_query.return_value = champions_mock_data
        
        champions = lp.get_champions()
        
        assert len(champions) == 2
        assert all(isinstance(c, Champion) for c in champions)
        assert champions[0].name == TestConstants.CHAMPION_JINX
        assert champions[1].name == TestConstants.CHAMPION_YASUO
        assert_mock_called_with_table(mock_leaguepedia_query, "Champions")
    
    @pytest.mark.integration
    def test_get_champions_with_resource_filter_string(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions with resource filter using string."""
        # Return only mana champions
        filtered_data = [champions_mock_data[0]]  # Jinx uses Mana
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions(resource="Mana")

        assert len(champions) == 1
        assert champions[0].resource == "Mana"
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes resource filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Resource='Mana'" in call_kwargs['where']

    @pytest.mark.integration
    def test_get_champions_with_resource_filter_enum(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions with resource filter using ChampionResource enum."""
        # Return only mana champions
        filtered_data = [champions_mock_data[0]]  # Jinx uses Mana
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions(resource=ChampionResource.MANA)

        assert len(champions) == 1
        assert champions[0].resource == "Mana"
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes resource filter (enum value converted to string)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Resource='Mana'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_champions_with_attributes_filter_string(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions with attributes filter using string."""
        # Return only marksman champions
        filtered_data = [champions_mock_data[0]]  # Jinx is Marksman
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions(attributes="Marksman")

        assert len(champions) == 1
        assert "Marksman" in champions[0].attributes
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause uses LIKE for attributes
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "LIKE '%Marksman%'" in call_kwargs['where']

    @pytest.mark.integration
    def test_get_champions_with_attributes_filter_enum(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions with attributes filter using ChampionAttribute enum."""
        # Return only marksman champions
        filtered_data = [champions_mock_data[0]]  # Jinx is Marksman
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions(attributes=ChampionAttribute.MARKSMAN)

        assert len(champions) == 1
        assert "Marksman" in champions[0].attributes
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause uses LIKE for attributes (enum value converted to string)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "LIKE '%Marksman%'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_champion_by_name(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champion_by_name returns single champion."""
        # Return only Jinx
        single_champion_data = [champions_mock_data[0]]
        mock_leaguepedia_query.return_value = single_champion_data
        
        champion = lp.get_champion_by_name(TestConstants.CHAMPION_JINX)
        
        assert isinstance(champion, Champion)
        assert champion.name == TestConstants.CHAMPION_JINX
        mock_leaguepedia_query.assert_called_once()
        # Verify exact name match in WHERE clause
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert f"Name='{TestConstants.CHAMPION_JINX}'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_champion_by_name_not_found(self, mock_leaguepedia_query):
        """Test get_champion_by_name returns None when champion not found."""
        mock_leaguepedia_query.return_value = []
        
        champion = lp.get_champion_by_name("NonexistentChampion")
        
        assert champion is None
    
    @pytest.mark.integration
    def test_get_champions_by_attributes_string(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions_by_attributes convenience function with string."""
        filtered_data = [champions_mock_data[1]]  # Yasuo has Fighter,Assassin
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions_by_attributes("Fighter")

        assert len(champions) == 1
        assert "Fighter" in champions[0].attributes
        assert_mock_called_with_table(mock_leaguepedia_query, "Champions")

    @pytest.mark.integration
    def test_get_champions_by_attributes_enum(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions_by_attributes convenience function with ChampionAttribute enum."""
        filtered_data = [champions_mock_data[1]]  # Yasuo has Fighter,Assassin
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions_by_attributes(ChampionAttribute.FIGHTER)

        assert len(champions) == 1
        assert "Fighter" in champions[0].attributes
        assert_mock_called_with_table(mock_leaguepedia_query, "Champions")
    
    @pytest.mark.integration
    def test_get_champions_by_resource_string(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions_by_resource convenience function with string."""
        filtered_data = [champions_mock_data[1]]  # Yasuo uses Flow
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions_by_resource("Flow")

        assert len(champions) == 1
        assert champions[0].resource == "Flow"
        assert_mock_called_with_table(mock_leaguepedia_query, "Champions")

    @pytest.mark.integration
    def test_get_champions_by_resource_enum(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_champions_by_resource convenience function with ChampionResource enum."""
        filtered_data = [champions_mock_data[1]]  # Yasuo uses Flow
        mock_leaguepedia_query.return_value = filtered_data

        champions = lp.get_champions_by_resource(ChampionResource.FLOW)

        assert len(champions) == 1
        assert champions[0].resource == "Flow"
        assert_mock_called_with_table(mock_leaguepedia_query, "Champions")
    
    @pytest.mark.integration
    def test_get_melee_champions(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_melee_champions filters correctly."""
        mock_leaguepedia_query.return_value = champions_mock_data
        
        melee_champions = lp.get_melee_champions()
        
        # Should only return Yasuo (175 range <= 200)
        assert len(melee_champions) == 1
        assert melee_champions[0].name == TestConstants.CHAMPION_YASUO
        assert melee_champions[0].is_melee is True
    
    @pytest.mark.integration
    def test_get_ranged_champions(self, mock_leaguepedia_query, champions_mock_data):
        """Test get_ranged_champions filters correctly."""
        mock_leaguepedia_query.return_value = champions_mock_data
        
        ranged_champions = lp.get_ranged_champions()
        
        # Should only return Jinx (525 range > 200)
        assert len(ranged_champions) == 1
        assert ranged_champions[0].name == TestConstants.CHAMPION_JINX
        assert ranged_champions[0].is_ranged is True


class TestChampionsErrorHandling:
    """Test error handling in champions functionality."""
    
    @pytest.mark.integration
    def test_get_champions_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to fetch champions"):
            lp.get_champions()
    
    @pytest.mark.integration
    def test_get_champion_by_name_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_champion_by_name are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match=f"Failed to fetch champion {TestConstants.CHAMPION_JINX}"):
            lp.get_champion_by_name(TestConstants.CHAMPION_JINX)
    
    @pytest.mark.integration
    def test_get_champions_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []
        
        champions = lp.get_champions()
        
        assert champions == []
        assert isinstance(champions, list)


class TestChampionsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_champion_with_zero_attack_range(self):
        """Test Champion with zero attack range (should be melee)."""
        champion = Champion(name="TestChamp", attack_range=0.0)
        
        assert champion.is_melee is True
        assert champion.is_ranged is False
    
    @pytest.mark.unit
    def test_champion_with_very_high_attack_range(self):
        """Test Champion with very high attack range."""
        champion = Champion(name="TestChamp", attack_range=1000.0)
        
        assert champion.is_ranged is True
        assert champion.is_melee is False
    
    @pytest.mark.unit
    def test_champion_with_special_characters_in_name(self):
        """Test Champion with special characters in name."""
        special_name = "Kai'Sa"
        champion = Champion(name=special_name)
        
        assert champion.name == special_name
    
    @pytest.mark.unit
    def test_champion_release_date_parsing(self):
        """Test various release date formats.""" 
        # Test with None
        champion_none = Champion(name="TestChamp", release_date=None)
        assert champion_none.release_date is None
        
        # Test with datetime object
        test_date = datetime(2013, 10, 10)
        champion_date = Champion(name="TestChamp", release_date=test_date)
        assert champion_date.release_date == test_date
    
    @pytest.mark.integration
    def test_champions_sql_injection_protection(self, mock_leaguepedia_query, champions_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = champions_mock_data
        
        malicious_input = "'; DROP TABLE Champions; --"
        
        # Should not raise an exception and should escape the input
        champions = lp.get_champions(resource=malicious_input)
        
        # Verify the input was escaped (single quotes doubled)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']  # Escaped single quotes
    
    @pytest.mark.unit
    def test_champion_attributes_list_edge_cases(self):
        """Test attributes_list with various edge cases."""
        # Empty string
        champion_empty = Champion(name="TestChamp", attributes="")
        assert champion_empty.attributes_list == []
        
        # Only commas
        champion_commas = Champion(name="TestChamp", attributes=",,,")
        assert champion_commas.attributes_list == []
        
        # Commas with spaces
        champion_spaces = Champion(name="TestChamp", attributes=" , , ")
        assert champion_spaces.attributes_list == []


class TestChampionsDataParsing:
    """Test data parsing from API responses."""
    
    @pytest.mark.unit
    def test_champion_numeric_field_parsing(self):
        """Test that numeric fields are properly parsed from strings."""
        # This would typically be tested in the internal parsing function
        # but we can test the dataclass accepts the expected types
        champion = Champion(
            name="TestChamp",
            be=6300,  # Should accept int
            rp=975,   # Should accept int
            health=610.0,  # Should accept float
            attack_range=525.0  # Should accept float
        )
        
        assert isinstance(champion.be, int)
        assert isinstance(champion.rp, int)
        assert isinstance(champion.health, float)
        assert isinstance(champion.attack_range, float)


if __name__ == "__main__":
    pytest.main([__file__])
