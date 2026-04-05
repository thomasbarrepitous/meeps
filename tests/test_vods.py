"""Tests for VODs functionality in Leaguepedia parser."""

import pytest
from unittest.mock import patch

import meeps as lp
from meeps.parsers.vods_parser import GameVod

from .conftest import TestConstants, assert_valid_dataclass_instance


class TestVodsImports:
    """Test that VODs functions are properly importable."""

    @pytest.mark.unit
    def test_vods_functions_importable(self):
        """Test that all VODs functions are available in the main module."""
        expected_functions = [
            "get_vods",
            "get_vod_by_game_id",
            "get_vods_by_match",
            "get_team_vods",
            "get_tournament_vods",
        ]

        for func_name in expected_functions:
            assert hasattr(lp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_game_vod_dataclass_importable(self):
        """Test that GameVod dataclass is importable."""
        assert hasattr(lp, "GameVod")


class TestGameVodDataclass:
    """Test GameVod dataclass functionality and computed properties."""

    @pytest.mark.unit
    def test_game_vod_initialization_complete(self):
        """Test GameVod dataclass can be initialized with all fields."""
        vod = GameVod(
            game_id="GAME001",
            match_id="MATCH001",
            vod_url="https://twitch.tv/videos/123456",
            vod_game_start="00:15:30",
            team_blue="T1",
            team_red="GenG",
            tournament="LCK/2024 Season/Summer Season",
            winner=1,
            game_number=1,
            mvp="Faker",
            match_history_url="https://matchhistory.example.com/game1",
        )

        assert_valid_dataclass_instance(vod, GameVod, ["game_id", "vod_url"])
        assert vod.game_id == "GAME001"
        assert vod.vod_url == "https://twitch.tv/videos/123456"
        assert vod.winner == 1

    @pytest.mark.unit
    def test_has_vod_property_true(self):
        """Test has_vod returns True when VOD URL exists."""
        vod = GameVod(vod_url="https://twitch.tv/videos/123456")
        assert vod.has_vod is True

    @pytest.mark.unit
    def test_has_vod_property_false_empty(self):
        """Test has_vod returns False when VOD URL is empty."""
        vod = GameVod(vod_url="")
        assert vod.has_vod is False

    @pytest.mark.unit
    def test_has_vod_property_false_none(self):
        """Test has_vod returns False when VOD URL is None."""
        vod = GameVod(vod_url=None)
        assert vod.has_vod is False

    @pytest.mark.unit
    def test_winning_team_blue_wins(self):
        """Test winning_team returns blue team when winner is 1."""
        vod = GameVod(team_blue="T1", team_red="GenG", winner=1)
        assert vod.winning_team == "T1"

    @pytest.mark.unit
    def test_winning_team_red_wins(self):
        """Test winning_team returns red team when winner is 2."""
        vod = GameVod(team_blue="T1", team_red="GenG", winner=2)
        assert vod.winning_team == "GenG"

    @pytest.mark.unit
    def test_winning_team_no_winner(self):
        """Test winning_team returns None when no winner."""
        vod = GameVod(team_blue="T1", team_red="GenG", winner=None)
        assert vod.winning_team is None

    @pytest.mark.unit
    def test_vod_start_seconds_hhmmss_format(self):
        """Test vod_start_seconds parses HH:MM:SS format."""
        vod = GameVod(vod_game_start="01:30:45")
        assert vod.vod_start_seconds == 5445  # 1*3600 + 30*60 + 45

    @pytest.mark.unit
    def test_vod_start_seconds_mmss_format(self):
        """Test vod_start_seconds parses MM:SS format."""
        vod = GameVod(vod_game_start="15:30")
        assert vod.vod_start_seconds == 930  # 15*60 + 30

    @pytest.mark.unit
    def test_vod_start_seconds_none(self):
        """Test vod_start_seconds returns None when not available."""
        vod = GameVod(vod_game_start=None)
        assert vod.vod_start_seconds is None

    @pytest.mark.unit
    def test_vod_start_seconds_empty_string(self):
        """Test vod_start_seconds returns None for empty string."""
        vod = GameVod(vod_game_start="")
        assert vod.vod_start_seconds is None

    @pytest.mark.unit
    def test_vod_start_seconds_invalid_format(self):
        """Test vod_start_seconds handles invalid format gracefully."""
        vod = GameVod(vod_game_start="invalid")
        assert vod.vod_start_seconds is None


class TestVodsAPI:
    """Test VODs API functions with mocked data."""

    @pytest.mark.integration
    def test_get_vods_basic_call(self, mock_leaguepedia_query, vods_mock_data):
        """Test basic get_vods call returns properly parsed GameVod objects."""
        # Return only items with VODs (first two)
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_vods()

        assert len(vods) == 2
        assert all(isinstance(v, GameVod) for v in vods)
        assert vods[0].game_id == "GAME001"
        assert vods[0].has_vod is True

    @pytest.mark.integration
    def test_get_vods_with_tournament_filter(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_vods with tournament filter."""
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_vods(tournament=TestConstants.LCK_2024_SUMMER)

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "OverviewPage" in call_kwargs["where"]
        assert TestConstants.LCK_2024_SUMMER.replace("/", "''") in call_kwargs["where"] or \
               TestConstants.LCK_2024_SUMMER in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_vods_with_team_filter(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_vods with team filter."""
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_vods(team="T1")

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "Blue='T1'" in call_kwargs["where"] or "Red='T1'" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_vods_with_vod_only_false(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_vods with with_vod_only=False returns all games."""
        mock_leaguepedia_query.return_value = vods_mock_data

        vods = lp.get_vods(with_vod_only=False)

        assert len(vods) == 3
        # Third VOD has no URL
        assert vods[2].has_vod is False

    @pytest.mark.integration
    def test_get_vod_by_game_id(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_vod_by_game_id returns single game."""
        mock_leaguepedia_query.return_value = [vods_mock_data[0]]

        vod = lp.get_vod_by_game_id("GAME001")

        assert isinstance(vod, GameVod)
        assert vod.game_id == "GAME001"
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_vod_by_game_id_not_found(self, mock_leaguepedia_query):
        """Test get_vod_by_game_id returns None when not found."""
        mock_leaguepedia_query.return_value = []

        vod = lp.get_vod_by_game_id("NONEXISTENT")

        assert vod is None

    @pytest.mark.integration
    def test_get_vods_by_match(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_vods_by_match returns all games in a match."""
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_vods_by_match("MATCH001")

        assert len(vods) == 2
        assert all(v.match_id == "MATCH001" for v in vods)
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_team_vods(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_team_vods convenience function."""
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_team_vods("T1")

        assert len(vods) == 2
        mock_leaguepedia_query.assert_called_once()

    @pytest.mark.integration
    def test_get_tournament_vods(self, mock_leaguepedia_query, vods_mock_data):
        """Test get_tournament_vods convenience function."""
        mock_leaguepedia_query.return_value = vods_mock_data[:2]

        vods = lp.get_tournament_vods(TestConstants.LCK_2024_SUMMER)

        assert len(vods) == 2
        mock_leaguepedia_query.assert_called_once()


class TestVodsErrorHandling:
    """Test error handling in VODs functionality."""

    @pytest.mark.integration
    def test_get_vods_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch VODs"):
            lp.get_vods()

    @pytest.mark.integration
    def test_get_vod_by_game_id_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_vod_by_game_id are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch VOD for game"):
            lp.get_vod_by_game_id("GAME001")

    @pytest.mark.integration
    def test_get_vods_by_match_api_error(self, mock_leaguepedia_query):
        """Test that API errors in get_vods_by_match are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch VODs for match"):
            lp.get_vods_by_match("MATCH001")

    @pytest.mark.integration
    def test_get_vods_empty_response(self, mock_leaguepedia_query):
        """Test handling of empty API response."""
        mock_leaguepedia_query.return_value = []

        vods = lp.get_vods()

        assert vods == []
        assert isinstance(vods, list)


class TestVodsEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_game_vod_with_special_characters(self):
        """Test GameVod with special characters in fields."""
        vod = GameVod(
            team_blue="G2 Esports",
            team_red="Fnatic",
            mvp="Caps",
        )
        assert vod.team_blue == "G2 Esports"

    @pytest.mark.unit
    def test_game_vod_vod_start_boundary(self):
        """Test vod_start_seconds with boundary values."""
        # Zero
        vod_zero = GameVod(vod_game_start="00:00:00")
        assert vod_zero.vod_start_seconds == 0

        # Large value
        vod_large = GameVod(vod_game_start="10:59:59")
        assert vod_large.vod_start_seconds == 39599

    @pytest.mark.integration
    def test_get_vods_sql_injection_protection(self, mock_leaguepedia_query, vods_mock_data):
        """Test that SQL injection attempts are properly escaped."""
        mock_leaguepedia_query.return_value = []

        malicious_input = "'; DROP TABLE MatchScheduleGame; --"

        # Should not raise an exception and should escape the input
        lp.get_vods(team=malicious_input)

        # Verify the input was escaped
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "''" in call_kwargs["where"]  # Escaped single quotes

    @pytest.mark.unit
    def test_game_vod_winner_invalid_value(self):
        """Test winning_team with invalid winner values."""
        vod = GameVod(team_blue="T1", team_red="GenG", winner=3)
        assert vod.winning_team is None

        vod2 = GameVod(team_blue="T1", team_red="GenG", winner=0)
        assert vod2.winning_team is None


class TestVodsDataParsing:
    """Test data parsing from API responses."""

    @pytest.mark.integration
    def test_vod_url_empty_string_handling(self, mock_leaguepedia_query):
        """Test that empty string VOD URLs are converted to None."""
        mock_data = [{
            "GameId": "GAME001",
            "MatchId": "MATCH001",
            "Vod": "",
            "VodGameStart": "",
            "Blue": "T1",
            "Red": "GenG",
            "OverviewPage": "LCK/2024 Season/Summer Season",
            "Winner": "1",
            "N_GameInMatch": "1",
            "MVP": "",
            "MatchHistory": "",
        }]
        mock_leaguepedia_query.return_value = mock_data

        vods = lp.get_vods(with_vod_only=False)

        assert len(vods) == 1
        assert vods[0].vod_url is None
        assert vods[0].vod_game_start is None
        assert vods[0].mvp is None
        assert vods[0].match_history_url is None

    @pytest.mark.integration
    def test_numeric_fields_parsed_correctly(self, mock_leaguepedia_query, vods_mock_data):
        """Test that numeric fields are correctly parsed."""
        mock_leaguepedia_query.return_value = [vods_mock_data[0]]

        vods = lp.get_vods()

        assert vods[0].winner == 1
        assert vods[0].game_number == 1


if __name__ == "__main__":
    pytest.main([__file__])
