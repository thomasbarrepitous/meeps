"""Tests for the scoreboard players parser module."""

import pytest
from unittest.mock import Mock, patch

from meeps.parsers.scoreboard_players_parser import (
    ScoreboardPlayer,
    get_scoreboard_players,
    get_player_match_history,
    get_team_match_performance,
    get_champion_performance_stats,
    get_game_scoreboard,
    get_tournament_mvp_candidates,
    get_role_performance_comparison,
    _parse_scoreboard_player_data,
)
from .conftest import TestConstants, assert_valid_dataclass_instance


class TestScoreboardPlayerDataclass:
    """Test the ScoreboardPlayer dataclass and its properties."""

    @pytest.mark.unit
    def test_scoreboard_player_dataclass_creation(self):
        """Test ScoreboardPlayer dataclass can be created with all fields."""
        player = ScoreboardPlayer(
            link="Faker",
            champion="Azir",
            kills=8,
            deaths=1,
            assists=12,
            gold=18500,
            cs=285,
            damage_to_champions=32000,
            vision_score=45,
            team="T1",
            team_kills=22,
            team_gold=85000,
            player_win="Yes",
            tournament="LCK/2024 Season/Summer Season",
            role="Mid",
        )

        assert player.link == "Faker"
        assert player.champion == "Azir"
        assert player.kills == 8
        assert player.deaths == 1
        assert player.assists == 12
        assert player.team == "T1"

    @pytest.mark.unit
    def test_scoreboard_player_optional_fields(self):
        """Test ScoreboardPlayer dataclass works with None values."""
        player = ScoreboardPlayer()

        assert player.link is None
        assert player.champion is None
        assert player.kills is None
        assert player.deaths is None

    @pytest.mark.unit
    def test_player_name_property(self):
        """Test the player_name property extracts name from link."""
        # Standard name
        player = ScoreboardPlayer(link="Faker")
        assert player.player_name == "Faker"

        # Name with disambiguation
        player = ScoreboardPlayer(link="Faker T1")
        assert player.player_name == "Faker"

        # No link
        player = ScoreboardPlayer()
        assert player.player_name is None

    @pytest.mark.unit
    def test_kda_ratio_property(self):
        """Test the KDA ratio calculation."""
        # Normal KDA
        player = ScoreboardPlayer(kills=8, deaths=1, assists=12)
        assert player.kda_ratio == 20.0  # (8 + 12) / 1

        # Perfect KDA (no deaths)
        player = ScoreboardPlayer(kills=5, deaths=0, assists=10)
        assert player.kda_ratio == float("inf")

        # Zero kills and assists with deaths
        player = ScoreboardPlayer(kills=0, deaths=3, assists=0)
        assert player.kda_ratio == 0.0

        # Missing data
        player = ScoreboardPlayer(kills=None, deaths=1, assists=5)
        assert player.kda_ratio is None

    @pytest.mark.unit
    def test_kill_participation_property(self):
        """Test kill participation calculation."""
        # Normal participation
        player = ScoreboardPlayer(kills=8, assists=12, team_kills=25)
        assert player.kill_participation == 80.0  # (8 + 12) / 25 * 100

        # Perfect participation
        player = ScoreboardPlayer(kills=5, assists=15, team_kills=20)
        assert player.kill_participation == 100.0

        # Zero team kills
        player = ScoreboardPlayer(kills=5, assists=5, team_kills=0)
        assert player.kill_participation is None

        # Missing data
        player = ScoreboardPlayer(kills=None, assists=5, team_kills=10)
        assert player.kill_participation is None

    @pytest.mark.unit
    def test_gold_share_property(self):
        """Test gold share calculation."""
        # Normal gold share
        player = ScoreboardPlayer(gold=18500, team_gold=85000)
        assert abs(player.gold_share - 21.76) < 0.01  # 18500/85000 * 100

        # Zero team gold
        player = ScoreboardPlayer(gold=10000, team_gold=0)
        assert player.gold_share is None

        # Missing data
        player = ScoreboardPlayer(gold=None, team_gold=85000)
        assert player.gold_share is None

    @pytest.mark.unit
    def test_did_win_property(self):
        """Test the did_win property logic."""
        # Win variations
        player = ScoreboardPlayer(player_win="Yes")
        assert player.did_win is True

        player = ScoreboardPlayer(player_win="true")
        assert player.did_win is True

        player = ScoreboardPlayer(player_win="1")
        assert player.did_win is True

        # Loss variations
        player = ScoreboardPlayer(player_win="No")
        assert player.did_win is False

        player = ScoreboardPlayer(player_win="false")
        assert player.did_win is False

        # No data
        player = ScoreboardPlayer(player_win=None)
        assert player.did_win is None

    @pytest.mark.unit
    def test_multikill_potential_property(self):
        """Test multikill potential assessment."""
        player = ScoreboardPlayer(kills=5)
        assert player.multikill_potential == "Pentakill potential"

        player = ScoreboardPlayer(kills=4)
        assert player.multikill_potential == "Quadrakill potential"

        player = ScoreboardPlayer(kills=3)
        assert player.multikill_potential == "Triplekill potential"

        player = ScoreboardPlayer(kills=2)
        assert player.multikill_potential == "Doublekill potential"

        player = ScoreboardPlayer(kills=1)
        assert player.multikill_potential == "Standard performance"

        player = ScoreboardPlayer(kills=None)
        assert player.multikill_potential is None

    @pytest.mark.unit
    def test_performance_grade_property(self):
        """Test performance grading system."""
        # S grade
        player = ScoreboardPlayer(kills=10, deaths=1, assists=15, team_kills=30)
        assert player.performance_grade == "S"  # KDA=25, KP=83%

        # A grade
        player = ScoreboardPlayer(kills=5, deaths=2, assists=8, team_kills=20)
        assert player.performance_grade == "A"  # KDA=6.5, KP=65%

        # B grade
        player = ScoreboardPlayer(kills=3, deaths=2, assists=5, team_kills=15)
        assert player.performance_grade == "B"  # KDA=4, KP=53%

        # C grade
        player = ScoreboardPlayer(kills=2, deaths=2, assists=2, team_kills=10)
        assert player.performance_grade == "C"  # KDA=2, KP=40%

        # D grade
        player = ScoreboardPlayer(kills=1, deaths=5, assists=2, team_kills=10)
        assert player.performance_grade == "D"  # KDA=0.6, KP=30%

        # Missing data
        player = ScoreboardPlayer(kills=None, deaths=2, assists=5)
        assert player.performance_grade is None


class TestScoreboardPlayerParser:
    """Test the scoreboard player parsing functions."""

    @pytest.mark.unit
    def test_parse_scoreboard_player_data(self):
        """Test _parse_scoreboard_player_data function."""
        raw_data = {
            "Link": "Faker",
            "Champion": "Azir",
            "Kills": "8",
            "Deaths": "1",
            "Assists": "12",
            "Gold": "18500",
            "CS": "285",
            "DamageToChampions": "32000",
            "VisionScore": "45",
            "SummonerSpells": "Flash,Teleport",
            "Items": "Nashor's Tooth;Rabadon's Deathcap;Zhonya's Hourglass",
            "TeamKills": "22",
            "TeamGold": "85000",
            "Team": "T1",
            "PlayerWin": "Yes",
            "Tournament": "LCK/2024 Season/Summer Season",
            "Role": "Mid",
            "DateTime_UTC": "2024-08-15T10:30:00Z",
        }

        player = _parse_scoreboard_player_data(raw_data)

        assert isinstance(player, ScoreboardPlayer)
        assert player.link == "Faker"
        assert player.champion == "Azir"
        assert player.kills == 8
        assert player.deaths == 1
        assert player.assists == 12
        assert player.gold == 18500
        assert player.cs == 285
        assert player.damage_to_champions == 32000
        assert player.vision_score == 45
        assert player.summoner_spells == ["Flash", "Teleport"]
        assert player.items == ["Nashor's Tooth", "Rabadon's Deathcap", "Zhonya's Hourglass"]
        assert player.team_kills == 22
        assert player.team_gold == 85000

    @pytest.mark.unit
    def test_parse_scoreboard_player_data_with_missing_fields(self):
        """Test parsing with missing/empty fields."""
        raw_data = {
            "Link": "TestPlayer",
            "Champion": "",
            "Kills": None,
            "Deaths": "",
            "Assists": "0",
            "SummonerSpells": "",
            "Items": "",
        }

        player = _parse_scoreboard_player_data(raw_data)

        assert player.link == "TestPlayer"
        assert player.champion == ""
        assert player.kills is None
        assert player.deaths is None
        assert player.assists == 0
        assert player.summoner_spells is None
        assert player.items is None

    @pytest.mark.unit
    def test_parse_scoreboard_player_data_invalid_numbers(self):
        """Test parsing with invalid number formats."""
        raw_data = {
            "Link": "TestPlayer",
            "Kills": "invalid",
            "Deaths": "3.5",  # Should handle as int
            "Gold": "not-a-number",
        }

        player = _parse_scoreboard_player_data(raw_data)

        assert player.kills is None  # Invalid number
        assert player.deaths is None  # Float should be None for int field
        assert player.gold is None  # Invalid number


class TestScoreboardPlayerQueries:
    """Test the scoreboard player query functions."""

    @pytest.mark.integration
    def test_get_scoreboard_players_all(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting all scoreboard players."""
        mock_leaguepedia_query.return_value = scoreboard_players_mock_data

        players = get_scoreboard_players()

        assert len(players) == 3
        assert all(isinstance(player, ScoreboardPlayer) for player in players)
        mock_leaguepedia_query.assert_called_once()

        # Verify the query parameters
        call_args = mock_leaguepedia_query.call_args
        assert call_args[1]["tables"] == "ScoreboardPlayers"
        expected_fields = ["Link", "Champion", "Kills", "Deaths", "Assists"]
        actual_fields = call_args[1]["fields"]
        for field in expected_fields:
            assert field in actual_fields

    @pytest.mark.integration
    def test_get_scoreboard_players_by_tournament(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific tournament."""
        mock_leaguepedia_query.return_value = scoreboard_players_mock_data

        players = get_scoreboard_players(tournament="LCK/2024 Season/Summer Season")

        assert len(players) == 3
        assert all(
            player.tournament == "LCK/2024 Season/Summer Season" for player in players
        )

        # Verify the where clause was used (should use OverviewPage, not Tournament)
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.OverviewPage='LCK/2024 Season/Summer Season'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_by_player(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific player."""
        faker_data = [p for p in scoreboard_players_mock_data if p["Link"] == "Faker"]
        mock_leaguepedia_query.return_value = faker_data

        players = get_scoreboard_players(player="Faker")

        assert len(players) == 1
        assert players[0].link == "Faker"

        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.Link LIKE '%Faker%'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_by_team(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific team."""
        t1_data = [p for p in scoreboard_players_mock_data if p["Team"] == "T1"]
        mock_leaguepedia_query.return_value = t1_data

        players = get_scoreboard_players(team="T1")

        assert len(players) == 2  # Faker and Gumayusi
        assert all(player.team == "T1" for player in players)

        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.Team='T1'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_by_champion(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific champion."""
        azir_data = [p for p in scoreboard_players_mock_data if p["Champion"] == "Azir"]
        mock_leaguepedia_query.return_value = azir_data

        players = get_scoreboard_players(champion="Azir")

        assert len(players) == 1
        assert players[0].champion == "Azir"

        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.Champion='Azir'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_by_role(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific role."""
        mid_data = [p for p in scoreboard_players_mock_data if p["Role"] == "Mid"]
        mock_leaguepedia_query.return_value = mid_data

        players = get_scoreboard_players(role="Mid")

        assert len(players) == 2  # Faker and Chovy
        assert all(player.role == "Mid" for player in players)

        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.Role='Mid'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_by_game_id(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test getting scoreboard players for a specific game."""
        game_data = [p for p in scoreboard_players_mock_data if p["GameId"] == "GAME001"]
        mock_leaguepedia_query.return_value = game_data

        players = get_scoreboard_players(game_id="GAME001")

        assert len(players) == 3
        assert all(player.game_id == "GAME001" for player in players)

        # Verify the where clause was used
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.GameId='GAME001'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_scoreboard_players_sql_injection_protection(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test that SQL injection is prevented by escaping quotes."""
        mock_leaguepedia_query.return_value = []

        # Try to inject SQL with quotes
        get_scoreboard_players(player="Faker'; DROP TABLE ScoreboardPlayers; --")

        # Verify the quotes were escaped
        call_args = mock_leaguepedia_query.call_args
        assert "Faker''; DROP TABLE ScoreboardPlayers; --" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_player_match_history(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_player_match_history helper function."""
        faker_data = [p for p in scoreboard_players_mock_data if p["Link"] == "Faker"]
        mock_leaguepedia_query.return_value = faker_data

        players = get_player_match_history("Faker", limit=5)

        assert len(players) == 1
        assert players[0].link == "Faker"

        # Verify player filter was applied (limit is handled post-query)
        call_args = mock_leaguepedia_query.call_args
        assert "ScoreboardPlayers.Link LIKE '%Faker%'" in call_args[1]["where"]

    @pytest.mark.integration
    def test_get_team_match_performance(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_team_match_performance helper function."""
        t1_data = [p for p in scoreboard_players_mock_data if p["Team"] == "T1"]
        mock_leaguepedia_query.return_value = t1_data

        players = get_team_match_performance("T1", tournament="LCK/2024 Season/Summer Season")

        assert len(players) == 2
        assert all(player.team == "T1" for player in players)

    @pytest.mark.integration
    def test_get_champion_performance_stats(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_champion_performance_stats helper function."""
        azir_data = [p for p in scoreboard_players_mock_data if p["Champion"] == "Azir"]
        mock_leaguepedia_query.return_value = azir_data

        players = get_champion_performance_stats("Azir", role="Mid")

        assert len(players) == 1
        assert players[0].champion == "Azir"
        assert players[0].role == "Mid"

    @pytest.mark.integration
    def test_get_game_scoreboard(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_game_scoreboard helper function."""
        mock_leaguepedia_query.return_value = scoreboard_players_mock_data

        players = get_game_scoreboard("GAME001")

        assert len(players) == 3
        assert all(player.game_id == "GAME001" for player in players)

    @pytest.mark.integration
    def test_get_role_performance_comparison(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_role_performance_comparison helper function."""
        mid_data = [p for p in scoreboard_players_mock_data if p["Role"] == "Mid"]
        mock_leaguepedia_query.return_value = mid_data

        players = get_role_performance_comparison("LCK/2024 Season/Summer Season", "Mid")

        assert len(players) == 2
        assert all(player.role == "Mid" for player in players)


class TestScoreboardPlayerErrorHandling:
    """Test error handling in scoreboard player functions."""

    @pytest.mark.unit
    def test_get_scoreboard_players_api_error(self, mock_leaguepedia_query):
        """Test error handling when API call fails."""
        mock_leaguepedia_query.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError, match="Failed to fetch scoreboard players"):
            get_scoreboard_players()


class TestScoreboardPlayerDataValidation:
    """Test data validation and edge cases."""

    @pytest.mark.unit
    def test_scoreboard_players_with_empty_response(self, mock_leaguepedia_query):
        """Test handling empty API response."""
        mock_leaguepedia_query.return_value = []

        players = get_scoreboard_players()

        assert players == []

    @pytest.mark.integration
    def test_scoreboard_players_data_structure_validation(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test that returned players have expected structure."""
        mock_leaguepedia_query.return_value = scoreboard_players_mock_data

        players = get_scoreboard_players()

        for player in players:
            assert_valid_dataclass_instance(
                player,
                ScoreboardPlayer,
                ["link", "champion", "kills", "deaths", "assists", "gold"],
            )

    @pytest.mark.integration
    def test_scoreboard_players_ordering(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test that players are ordered correctly."""
        mock_leaguepedia_query.return_value = scoreboard_players_mock_data

        get_scoreboard_players()

        # Verify order_by parameter
        call_args = mock_leaguepedia_query.call_args
        assert call_args[1]["order_by"] == "ScoreboardPlayers.DateTime_UTC DESC"


class TestScoreboardPlayerAdvancedFeatures:
    """Test advanced features like MVP candidates."""

    @pytest.mark.integration
    def test_get_tournament_mvp_candidates(
        self, mock_leaguepedia_query, scoreboard_players_mock_data
    ):
        """Test get_tournament_mvp_candidates function."""
        # Simulate multiple games for same players
        extended_data = scoreboard_players_mock_data * 3  # Repeat data 3 times
        mock_leaguepedia_query.return_value = extended_data

        mvp_candidates = get_tournament_mvp_candidates(
            "LCK/2024 Season/Summer Season", min_games=2
        )

        # Should return players who meet minimum games criteria
        assert len(mvp_candidates) > 0
        # MVP candidates should be sorted by performance
        if len(mvp_candidates) > 1:
            first_kda = mvp_candidates[0].kda_ratio or 0
            second_kda = mvp_candidates[1].kda_ratio or 0
            assert first_kda >= second_kda

    @pytest.mark.unit
    def test_performance_metrics_edge_cases(self):
        """Test edge cases in performance metric calculations."""
        # Perfect game (no deaths, high participation)
        perfect_player = ScoreboardPlayer(
            kills=10, deaths=0, assists=15, team_kills=20, gold=20000, team_gold=80000
        )

        assert perfect_player.kda_ratio == float("inf")
        assert perfect_player.kill_participation == 125.0  # Over 100% due to high assists
        assert perfect_player.gold_share == 25.0
        assert perfect_player.performance_grade == "S"

        # Terrible game (high deaths, low participation)
        bad_player = ScoreboardPlayer(
            kills=0, deaths=10, assists=1, team_kills=5, gold=5000, team_gold=60000
        )

        assert bad_player.kda_ratio == 0.1
        assert bad_player.kill_participation == 20.0
        assert bad_player.gold_share < 10.0
        assert bad_player.performance_grade == "D"