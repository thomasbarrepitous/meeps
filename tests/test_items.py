"""Tests for items functionality in Leaguepedia parser."""

import pytest
from unittest.mock import Mock
from typing import List

import meeps as lp
from meeps.parsers.items_parser import Item

from .conftest import TestConstants, assert_valid_dataclass_instance, assert_mock_called_with_table


class TestItemsImports:
    """Test that items functions are properly importable."""
    
    @pytest.mark.unit
    def test_items_functions_importable(self):
        """Test that all items functions are available in the main module."""
        expected_functions = [
            'get_items',
            'get_item_by_name',
            'get_items_by_tier',
            'get_ad_items',
            'get_ap_items',
            'get_tank_items',
            'get_health_items',
            'get_mana_items',
            'search_items_by_stat'
        ]
        
        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"


class TestItemDataclass:
    """Test Item dataclass functionality and computed properties."""
    
    @pytest.mark.unit
    def test_item_initialization_complete(self):
        """Test Item dataclass can be initialized with all fields."""
        item = Item(
            name=TestConstants.ITEM_INFINITY_EDGE,
            tier="Legendary",
            riot_id=3031,
            recipe="B.F. Sword + Cloak of Agility + Pickaxe",
            cost=425,
            total_cost=3400,
            ad=70,
            life_steal=0,
            health=0,
            hp_regen=0,
            armor=0,
            mr=0,
            attack_damage=0,
            crit=20,
            ap=0,
            mana=0
        )
        
        assert_valid_dataclass_instance(item, Item, ['name'])
        assert item.name == TestConstants.ITEM_INFINITY_EDGE
        assert item.tier == "Legendary"
        assert item.riot_id == 3031
        assert item.total_cost == 3400
        assert item.ad == 70
        assert item.crit == 20
    
    @pytest.mark.unit
    def test_item_provides_ad_property(self):
        """Test Item provides_ad property with AD sources."""
        # Test with ad field
        item_ad = Item(name="TestItem", ad=70)
        assert item_ad.provides_ad is True
        
        # Test with attack_damage field
        item_attack_damage = Item(name="TestItem", attack_damage=70)
        assert item_attack_damage.provides_ad is True
        
        # Test with both fields
        item_both = Item(name="TestItem", ad=30, attack_damage=40)
        assert item_both.provides_ad is True
        
        # Test with no AD
        item_no_ad = Item(name="TestItem", ad=0, attack_damage=0)
        assert item_no_ad.provides_ad is False
        
        # Test with None values
        item_none = Item(name="TestItem", ad=None, attack_damage=None)
        assert item_none.provides_ad is False
    
    @pytest.mark.unit
    def test_item_provides_ap_property(self):
        """Test Item provides_ap property."""
        # Test with AP
        item_ap = Item(name="TestItem", ap=120)
        assert item_ap.provides_ap is True
        
        # Test with no AP
        item_no_ap = Item(name="TestItem", ap=0)
        assert item_no_ap.provides_ap is False
        
        # Test with None AP
        item_none_ap = Item(name="TestItem", ap=None)
        assert item_none_ap.provides_ap is False
    
    @pytest.mark.unit
    def test_item_provides_armor_property(self):
        """Test Item provides_armor property."""
        # Test with armor
        item_armor = Item(name="TestItem", armor=80)
        assert item_armor.provides_armor is True
        
        # Test with no armor
        item_no_armor = Item(name="TestItem", armor=0)
        assert item_no_armor.provides_armor is False
        
        # Test with None armor
        item_none_armor = Item(name="TestItem", armor=None)
        assert item_none_armor.provides_armor is False
    
    @pytest.mark.unit
    def test_item_provides_mr_property(self):
        """Test Item provides_mr property."""
        # Test with MR
        item_mr = Item(name="TestItem", mr=50)
        assert item_mr.provides_mr is True
        
        # Test with no MR
        item_no_mr = Item(name="TestItem", mr=0)
        assert item_no_mr.provides_mr is False
    
    @pytest.mark.unit
    def test_item_provides_health_property(self):
        """Test Item provides_health property with health sources."""
        # Test with health field
        item_health = Item(name="TestItem", health=350)
        assert item_health.provides_health is True
        
        # Test with bonus_hp field
        item_bonus_hp = Item(name="TestItem", bonus_hp=350)
        assert item_bonus_hp.provides_health is True
        
        # Test with both fields
        item_both = Item(name="TestItem", health=200, bonus_hp=150)
        assert item_both.provides_health is True
        
        # Test with no health
        item_no_health = Item(name="TestItem", health=0, bonus_hp=0)
        assert item_no_health.provides_health is False
    
    @pytest.mark.unit
    def test_item_provides_mana_property(self):
        """Test Item provides_mana property."""
        # Test with mana
        item_mana = Item(name="TestItem", mana=250)
        assert item_mana.provides_mana is True
        
        # Test with no mana
        item_no_mana = Item(name="TestItem", mana=0)
        assert item_no_mana.provides_mana is False
    
    @pytest.mark.unit
    def test_item_properties_with_none_values(self):
        """Test that properties handle None values gracefully."""
        item = Item(name="TestItem")
        
        assert item.provides_ad is False
        assert item.provides_ap is False
        assert item.provides_armor is False
        assert item.provides_mr is False
        assert item.provides_health is False
        assert item.provides_mana is False


class TestItemsAPI:
    """Test items API functions with mocked data."""
    
    @pytest.mark.integration
    def test_get_items_basic_call(self, mock_leaguepedia_query, items_mock_data):
        """Test basic get_items call returns properly parsed Item objects."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        items = lp.get_items()
        
        assert len(items) == 3
        assert all(isinstance(item, Item) for item in items)
        assert items[0].name == TestConstants.ITEM_INFINITY_EDGE
        assert items[1].name == TestConstants.ITEM_RABADONS
        assert items[2].name == TestConstants.ITEM_THORNMAIL
        assert_mock_called_with_table(mock_leaguepedia_query, "Items")
    
    @pytest.mark.integration
    def test_get_items_with_tier_filter(self, mock_leaguepedia_query, items_mock_data):
        """Test get_items with tier filter."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        items = lp.get_items(tier="Legendary")
        
        assert len(items) == 3
        assert all(item.tier == "Legendary" for item in items)
        mock_leaguepedia_query.assert_called_once()
        # Verify WHERE clause includes tier filter
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Tier='Legendary'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_item_by_name(self, mock_leaguepedia_query, items_mock_data):
        """Test get_item_by_name returns single item."""
        # Return only Infinity Edge
        single_item_data = [items_mock_data[0]]
        mock_leaguepedia_query.return_value = single_item_data
        
        item = lp.get_item_by_name(TestConstants.ITEM_INFINITY_EDGE)
        
        assert isinstance(item, Item)
        assert item.name == TestConstants.ITEM_INFINITY_EDGE
        mock_leaguepedia_query.assert_called_once()
        # Verify exact name match in WHERE clause
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert f"Name='{TestConstants.ITEM_INFINITY_EDGE}'" in call_kwargs['where']
    
    @pytest.mark.integration
    def test_get_item_by_name_not_found(self, mock_leaguepedia_query):
        """Test get_item_by_name returns None when item not found."""
        mock_leaguepedia_query.return_value = []
        
        item = lp.get_item_by_name("NonexistentItem")
        
        assert item is None
    
    @pytest.mark.integration
    def test_get_items_by_tier(self, mock_leaguepedia_query, items_mock_data):
        """Test get_items_by_tier convenience function."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        items = lp.get_items_by_tier("Legendary")
        
        assert len(items) == 3
        assert all(item.tier == "Legendary" for item in items)
        assert_mock_called_with_table(mock_leaguepedia_query, "Items")
    
    @pytest.mark.integration
    def test_get_ad_items(self, mock_leaguepedia_query, items_mock_data):
        """Test get_ad_items filters correctly."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        ad_items = lp.get_ad_items()
        
        # Should only return Infinity Edge (has AD)
        assert len(ad_items) == 1
        assert ad_items[0].name == TestConstants.ITEM_INFINITY_EDGE
        assert ad_items[0].provides_ad is True
    
    @pytest.mark.integration
    def test_get_ap_items(self, mock_leaguepedia_query, items_mock_data):
        """Test get_ap_items filters correctly."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        ap_items = lp.get_ap_items()
        
        # Should only return Rabadon's Deathcap (has AP)
        assert len(ap_items) == 1
        assert ap_items[0].name == TestConstants.ITEM_RABADONS
        assert ap_items[0].provides_ap is True
    
    @pytest.mark.integration
    def test_get_tank_items(self, mock_leaguepedia_query, items_mock_data):
        """Test get_tank_items filters correctly."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        tank_items = lp.get_tank_items()
        
        # Should only return Thornmail (has armor)
        assert len(tank_items) == 1
        assert tank_items[0].name == TestConstants.ITEM_THORNMAIL
        assert tank_items[0].provides_armor is True
    
    @pytest.mark.integration
    def test_get_health_items(self, mock_leaguepedia_query, items_mock_data):
        """Test get_health_items filters correctly."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        health_items = lp.get_health_items()
        
        # Should only return Thornmail (has health)
        assert len(health_items) == 1
        assert health_items[0].name == TestConstants.ITEM_THORNMAIL
        assert health_items[0].provides_health is True
    
    @pytest.mark.integration
    def test_get_mana_items(self, mock_leaguepedia_query, items_mock_data):
        """Test get_mana_items returns items with mana."""
        # Create mock data with mana item
        mana_item_data = [{
            'Name': 'Tear of the Goddess',
            'Tier': 'Basic',
            'Mana': '240',
            'AD': '0',
            'AP': '0',
            'Health': '0',
            'Armor': '0'
        }]
        mock_leaguepedia_query.return_value = mana_item_data
        
        mana_items = lp.get_mana_items()
        
        assert len(mana_items) == 1
        assert mana_items[0].provides_mana is True


class TestItemsSearchByStats:
    """Test search_items_by_stat functionality."""
    
    @pytest.mark.integration
    def test_search_items_by_single_stat(self, mock_leaguepedia_query, items_mock_data):
        """Test searching items by single stat requirement."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        ad_items = lp.search_items_by_stat(provides_ad=True)
        
        assert len(ad_items) == 1
        assert ad_items[0].provides_ad is True
        assert ad_items[0].name == TestConstants.ITEM_INFINITY_EDGE
    
    @pytest.mark.integration
    def test_search_items_by_multiple_stats(self, mock_leaguepedia_query, items_mock_data):
        """Test searching items by multiple stat requirements."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        # Look for items that provide both armor and health
        tank_items = lp.search_items_by_stat(provides_armor=True, provides_health=True)
        
        assert len(tank_items) == 1
        assert tank_items[0].name == TestConstants.ITEM_THORNMAIL
        assert tank_items[0].provides_armor is True
        assert tank_items[0].provides_health is True
    
    @pytest.mark.integration
    def test_search_items_by_exclusion(self, mock_leaguepedia_query, items_mock_data):
        """Test searching items by excluding certain stats."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        # Look for items that don't provide AD
        non_ad_items = lp.search_items_by_stat(provides_ad=False)
        
        assert len(non_ad_items) == 2
        item_names = [item.name for item in non_ad_items]
        assert TestConstants.ITEM_RABADONS in item_names
        assert TestConstants.ITEM_THORNMAIL in item_names
        assert TestConstants.ITEM_INFINITY_EDGE not in item_names
    
    @pytest.mark.integration
    def test_search_items_no_matches(self, mock_leaguepedia_query, items_mock_data):
        """Test search that returns no matches."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        # Look for items that provide both AD and AP (none in our test data)
        hybrid_items = lp.search_items_by_stat(provides_ad=True, provides_ap=True)
        
        assert len(hybrid_items) == 0


class TestItemsErrorHandling:
    """Test error handling in items functionality."""
    
    @pytest.mark.integration
    def test_get_items_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match="Failed to fetch items"):
            lp.get_items()
    
    @pytest.mark.integration
    def test_get_item_by_name_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_item_by_name are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")
        
        with pytest.raises(RuntimeError, match=f"Failed to fetch item {TestConstants.ITEM_INFINITY_EDGE}"):
            lp.get_item_by_name(TestConstants.ITEM_INFINITY_EDGE)
    
    @pytest.mark.integration
    def test_get_items_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []
        
        items = lp.get_items()
        
        assert items == []
        assert isinstance(items, list)


class TestItemsEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_item_with_zero_stats(self):
        """Test Item with all zero stats."""
        item = Item(
            name="TestItem",
            ad=0,
            ap=0,
            armor=0,
            mr=0,
            health=0,
            mana=0
        )
        
        assert item.provides_ad is False
        assert item.provides_ap is False
        assert item.provides_armor is False
        assert item.provides_mr is False
        assert item.provides_health is False
        assert item.provides_mana is False
    
    @pytest.mark.unit
    def test_item_with_negative_stats(self):
        """Test Item with negative stats (should be considered as not providing)."""
        item = Item(
            name="TestItem",
            ad=-10,
            ap=-5,
            armor=-20
        )
        
        assert item.provides_ad is False
        assert item.provides_ap is False
        assert item.provides_armor is False
    
    @pytest.mark.unit
    def test_item_with_special_characters_in_name(self):
        """Test Item with special characters in name."""
        special_names = [
            "Zhonya's Hourglass",
            "Wit's End",
            "Seraph's Embrace",
            "Lich Bane"
        ]
        
        for name in special_names:
            item = Item(name=name)
            assert item.name == name
    
    @pytest.mark.integration
    def test_items_sql_injection_protection(self, mock_leaguepedia_query, items_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = items_mock_data
        
        malicious_input = "'; DROP TABLE Items; --"
        
        # Should not raise an exception and should escape the input
        items = lp.get_items(tier=malicious_input)
        
        # Verify the input was escaped (single quotes doubled)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs['where']  # Escaped single quotes
    
    @pytest.mark.unit
    def test_item_cost_fields(self):
        """Test item cost-related fields."""
        item = Item(
            name="TestItem",
            cost=425,      # Combine cost
            total_cost=3400  # Total cost to purchase
        )
        
        assert item.cost == 425
        assert item.total_cost == 3400
    
    @pytest.mark.unit
    def test_item_recipe_field(self):
        """Test item recipe field."""
        recipe = "B.F. Sword + Cloak of Agility + Pickaxe"
        item = Item(name="TestItem", recipe=recipe)
        
        assert item.recipe == recipe
    
    @pytest.mark.unit
    def test_item_tier_field(self):
        """Test item tier field with various tiers."""
        tiers = ["Basic", "Epic", "Legendary", "Mythic", "Boots", "Consumable"]
        
        for tier in tiers:
            item = Item(name="TestItem", tier=tier)
            assert item.tier == tier


class TestItemsDataParsing:
    """Test data parsing from API responses."""
    
    @pytest.mark.unit
    def test_item_numeric_field_parsing(self):
        """Test that numeric fields are properly handled."""
        item = Item(
            name="TestItem",
            riot_id=3031,      # Should accept int
            cost=425,          # Should accept int
            total_cost=3400,   # Should accept int
            ad=70,             # Should accept int
            ap=120             # Should accept int
        )
        
        assert isinstance(item.riot_id, int)
        assert isinstance(item.cost, int) 
        assert isinstance(item.total_cost, int)
        assert isinstance(item.ad, int)
        assert isinstance(item.ap, int)


if __name__ == "__main__":
    pytest.main([__file__])