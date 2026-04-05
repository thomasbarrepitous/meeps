"""Tests for Patches functionality in Leaguepedia parser."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

import meeps as lp
from meeps.parsers.patches_parser import Patch

from .conftest import TestConstants, assert_valid_dataclass_instance


class TestPatchesImports:
    """Test that Patches functions are properly importable."""

    @pytest.mark.unit
    def test_patches_functions_importable(self):
        """Test that all Patches functions are available in the main module."""
        expected_functions = [
            "get_patches",
            "get_patch_by_version",
            "get_patches_in_date_range",
            "get_latest_patch",
            "get_patches_by_major_version",
        ]

        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_patch_dataclass_importable(self):
        """Test that Patch dataclass is importable."""
        assert hasattr(lp, "Patch")


class TestPatchDataclass:
    """Test Patch dataclass functionality and computed properties."""

    @pytest.mark.unit
    def test_patch_initialization_complete(self):
        """Test Patch dataclass can be initialized with all fields."""
        release_date = datetime(2024, 1, 10, tzinfo=timezone.utc)
        patch = Patch(
            patch="14.1",
            release_date=release_date,
            highlights="Season 14 start",
            patch_notes_link="https://example.com/patch-14-1",
            disabled_champions="Viego",
            disabled_items="Heartsteel",
            new_champions="Smolder",
            updated_champions="Ahri, Lux",
        )

        assert_valid_dataclass_instance(patch, Patch, ["patch", "release_date"])
        assert patch.patch == "14.1"
        assert patch.release_date == release_date
        assert patch.highlights == "Season 14 start"

    @pytest.mark.unit
    def test_major_version_property(self):
        """Test major_version extracts first part of version string."""
        patch = Patch(patch="14.1")
        assert patch.major_version == 14

        patch2 = Patch(patch="13.24")
        assert patch2.major_version == 13

    @pytest.mark.unit
    def test_minor_version_property(self):
        """Test minor_version extracts second part of version string."""
        patch = Patch(patch="14.1")
        assert patch.minor_version == 1

        patch2 = Patch(patch="13.24")
        assert patch2.minor_version == 24

    @pytest.mark.unit
    def test_version_properties_none(self):
        """Test version properties return None for None patch."""
        patch = Patch(patch=None)
        assert patch.major_version is None
        assert patch.minor_version is None

    @pytest.mark.unit
    def test_version_properties_invalid_format(self):
        """Test version properties handle invalid formats."""
        patch = Patch(patch="invalid")
        assert patch.major_version is None
        assert patch.minor_version is None

    @pytest.mark.unit
    def test_disabled_champions_list(self):
        """Test disabled_champions_list parses comma-separated string."""
        patch = Patch(disabled_champions="Viego, K'Sante, Azir")

        champions = patch.disabled_champions_list
        assert isinstance(champions, list)
        assert len(champions) == 3
        assert "Viego" in champions
        assert "K'Sante" in champions
        assert "Azir" in champions

    @pytest.mark.unit
    def test_disabled_champions_list_empty(self):
        """Test disabled_champions_list returns empty list when None."""
        patch = Patch(disabled_champions=None)
        assert patch.disabled_champions_list == []

        patch2 = Patch(disabled_champions="")
        assert patch2.disabled_champions_list == []

    @pytest.mark.unit
    def test_disabled_items_list(self):
        """Test disabled_items_list parses comma-separated string."""
        patch = Patch(disabled_items="Heartsteel, Navori Quickblades")

        items = patch.disabled_items_list
        assert len(items) == 2
        assert "Heartsteel" in items
        assert "Navori Quickblades" in items

    @pytest.mark.unit
    def test_disabled_items_list_empty(self):
        """Test disabled_items_list returns empty list when None."""
        patch = Patch(disabled_items=None)
        assert patch.disabled_items_list == []

    @pytest.mark.unit
    def test_new_champions_list(self):
        """Test new_champions_list parses comma-separated string."""
        patch = Patch(new_champions="Smolder")

        champions = patch.new_champions_list
        assert len(champions) == 1
        assert "Smolder" in champions

    @pytest.mark.unit
    def test_new_champions_list_empty(self):
        """Test new_champions_list returns empty list when None."""
        patch = Patch(new_champions=None)
        assert patch.new_champions_list == []

    @pytest.mark.unit
    def test_updated_champions_list(self):
        """Test updated_champions_list parses comma-separated string."""
        patch = Patch(updated_champions="Ahri, Lux, Jinx")

        champions = patch.updated_champions_list
        assert len(champions) == 3
        assert "Ahri" in champions
        assert "Lux" in champions
        assert "Jinx" in champions

    @pytest.mark.unit
    def test_updated_champions_list_empty(self):
        """Test updated_champions_list returns empty list when None."""
        patch = Patch(updated_champions=None)
        assert patch.updated_champions_list == []


class TestPatchesAPI:
    """Test Patches API functions with mocked data."""

    @pytest.mark.integration
    def test_get_patches_basic_call(self, mock_leaguepedia_query, patches_mock_data):
        """Test basic get_patches call returns properly parsed Patch objects."""
        mock_leaguepedia_query.return_value = patches_mock_data

        patches = lp.get_patches()

        assert len(patches) == 3
        assert all(isinstance(p, Patch) for p in patches)
        assert patches[0].patch == "14.1"
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_patches_with_year_filter(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patches with year filter."""
        mock_leaguepedia_query.return_value = patches_mock_data[:2]  # Only 2024 patches

        patches = lp.get_patches(year=2024)

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "YEAR(Patches.ReleaseDate) = 2024" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_patches_default_ordering(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patches default ordering is by date descending."""
        mock_leaguepedia_query.return_value = patches_mock_data

        lp.get_patches()

        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs["order_by"] == "Patches.ReleaseDate DESC"

    @pytest.mark.integration
    def test_get_patches_with_limit(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patches with limit parameter."""
        mock_leaguepedia_query.return_value = [patches_mock_data[0]]

        patches = lp.get_patches(limit=1)

        assert len(patches) == 1
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs["limit"] == 1

    @pytest.mark.integration
    def test_get_patch_by_version(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patch_by_version returns single patch."""
        mock_leaguepedia_query.return_value = [patches_mock_data[0]]

        patch = lp.get_patch_by_version("14.1")

        assert isinstance(patch, Patch)
        assert patch.patch == "14.1"
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_patch_by_version_not_found(self, mock_leaguepedia_query):
        """Test get_patch_by_version returns None when not found."""
        mock_leaguepedia_query.return_value = []

        patch = lp.get_patch_by_version("99.99")

        assert patch is None

    @pytest.mark.integration
    def test_get_patches_in_date_range(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patches_in_date_range filters by dates."""
        mock_leaguepedia_query.return_value = patches_mock_data[:2]

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)

        patches = lp.get_patches_in_date_range(start, end)

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "2024-01-01" in call_kwargs["where"]
        assert "2024-12-31" in call_kwargs["where"]
        assert call_kwargs["order_by"] == "Patches.ReleaseDate ASC"

    @pytest.mark.integration
    def test_get_latest_patch(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_latest_patch returns most recent patch."""
        mock_leaguepedia_query.return_value = [patches_mock_data[0]]

        patch = lp.get_latest_patch()

        assert isinstance(patch, Patch)
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert call_kwargs["order_by"] == "Patches.ReleaseDate DESC"
        assert call_kwargs["limit"] == 1

    @pytest.mark.integration
    def test_get_latest_patch_empty(self, mock_leaguepedia_query):
        """Test get_latest_patch returns None when no patches."""
        mock_leaguepedia_query.return_value = []

        patch = lp.get_latest_patch()

        assert patch is None

    @pytest.mark.integration
    def test_get_patches_by_major_version(self, mock_leaguepedia_query, patches_mock_data):
        """Test get_patches_by_major_version filters by season."""
        # Only season 14 patches
        mock_leaguepedia_query.return_value = patches_mock_data[:2]

        patches = lp.get_patches_by_major_version(14)

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "LIKE '14.%'" in call_kwargs["where"]


class TestPatchesErrorHandling:
    """Test error handling in Patches functionality."""

    @pytest.mark.integration
    def test_get_patches_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch patches"):
            lp.get_patches()

    @pytest.mark.integration
    def test_get_patch_by_version_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_patch_by_version are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch patch 14.1"):
            lp.get_patch_by_version("14.1")

    @pytest.mark.integration
    def test_get_latest_patch_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_latest_patch are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch latest patch"):
            lp.get_latest_patch()

    @pytest.mark.integration
    def test_get_patches_in_date_range_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_patches_in_date_range are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        with pytest.raises(RuntimeError, match="Failed to fetch patches in date range"):
            lp.get_patches_in_date_range(start, end)

    @pytest.mark.integration
    def test_get_patches_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []

        patches = lp.get_patches()

        assert patches == []
        assert isinstance(patches, list)


class TestPatchesEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_patch_with_three_part_version(self):
        """Test Patch with three-part version string."""
        patch = Patch(patch="14.1.1")
        assert patch.major_version == 14
        assert patch.minor_version == 1

    @pytest.mark.unit
    def test_patch_list_properties_with_spaces(self):
        """Test list properties handle extra spaces."""
        patch = Patch(
            disabled_champions=" Viego , K'Sante , Azir ",
            updated_champions="  Ahri  ,  Lux  ",
        )

        disabled = patch.disabled_champions_list
        assert "Viego" in disabled
        assert all(champ.strip() == champ for champ in disabled)

        updated = patch.updated_champions_list
        assert "Ahri" in updated
        assert all(champ.strip() == champ for champ in updated)

    @pytest.mark.unit
    def test_patch_list_properties_only_commas(self):
        """Test list properties with only commas."""
        patch = Patch(
            disabled_champions=",,,",
            disabled_items=",",
        )

        assert patch.disabled_champions_list == []
        assert patch.disabled_items_list == []

    @pytest.mark.integration
    def test_get_patches_sql_injection_protection(self, mock_leaguepedia_query, patches_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "'; DROP TABLE Patches; --"

        # Should not raise an exception and should escape the input
        lp.get_patch_by_version(malicious_input)

        # Verify the input was escaped
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]  # Escaped single quotes


class TestPatchesDataParsing:
    """Test data parsing from API responses."""

    @pytest.mark.integration
    def test_release_date_parsing(self, mock_leaguepedia_query, patches_mock_data):
        """Test that release dates are properly parsed."""
        mock_leaguepedia_query.return_value = [patches_mock_data[0]]

        patches = lp.get_patches()

        assert patches[0].release_date is not None
        assert isinstance(patches[0].release_date, datetime)
        assert patches[0].release_date.tzinfo is not None  # Timezone-aware

    @pytest.mark.integration
    def test_empty_fields_converted_to_none(self, mock_leaguepedia_query):
        """Test that empty string fields are converted to None."""
        mock_data = [{
            "Patch": "14.1",
            "ReleaseDate": "2024-01-10T00:00:00Z",
            "Highlights": "",
            "PatchNotesLink": "",
            "DisabledChampions": "",
            "DisabledItems": "",
            "NewChampions": "",
            "UpdatedChampions": "",
        }]
        mock_leaguepedia_query.return_value = mock_data

        patches = lp.get_patches()

        assert patches[0].highlights is None
        assert patches[0].patch_notes_link is None
        assert patches[0].disabled_champions is None

    @pytest.mark.integration
    def test_missing_release_date_handled(self, mock_leaguepedia_query):
        """Test that missing release date is handled."""
        mock_data = [{
            "Patch": "14.1",
            "ReleaseDate": None,
            "Highlights": "Test",
            "PatchNotesLink": "",
            "DisabledChampions": "",
            "DisabledItems": "",
            "NewChampions": "",
            "UpdatedChampions": "",
        }]
        mock_leaguepedia_query.return_value = mock_data

        patches = lp.get_patches()

        assert patches[0].release_date is None


if __name__ == "__main__":
    pytest.main([__file__])
