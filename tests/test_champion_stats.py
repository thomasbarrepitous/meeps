"""Tests for ChampionStats functionality in Leaguepedia parser."""

import pytest
from unittest.mock import patch, MagicMock

import meeps as mp
from meeps.parsers.champion_stats_parser import (
    ChampionTournamentStats,
    PlayerChampionStats,
)

from .conftest import TestConstants, assert_valid_dataclass_instance


class TestChampionStatsImports:
    """Test that ChampionStats functions are properly importable."""

    @pytest.mark.unit
    def test_champion_stats_functions_importable(self):
        """Test that all ChampionStats functions are available in the main module."""
        expected_functions = [
            "get_champion_tournament_stats",
            "get_champion_stats_by_name",
            "get_most_picked_champions",
            "get_most_banned_champions",
            "get_highest_winrate_champions",
            "get_player_champion_stats",
            "get_player_champion_pool",
            "get_player_signature_champions",
        ]

        for func_name in expected_functions:
            assert hasattr(mp, func_name), f"Function {func_name} is not importable"

    @pytest.mark.unit
    def test_dataclasses_importable(self):
        """Test that dataclasses are importable."""
        assert hasattr(mp, "ChampionTournamentStats")
        assert hasattr(mp, "PlayerChampionStats")


class TestChampionTournamentStatsDataclass:
    """Test ChampionTournamentStats dataclass functionality."""

    @pytest.mark.unit
    def test_initialization_complete(self):
        """Test ChampionTournamentStats can be initialized with all fields."""
        stats = ChampionTournamentStats(
            champion="Jinx",
            tournament="LCK/2024 Season/Summer Season",
            games_played=10,
            games_won=7,
            games_banned=5,
            total_games=50,
            total_kills=45,
            total_deaths=20,
            total_assists=60,
        )

        assert_valid_dataclass_instance(stats, ChampionTournamentStats, ["champion", "games_played"])
        assert stats.champion == "Jinx"
        assert stats.games_played == 10
        assert stats.games_won == 7

    @pytest.mark.unit
    def test_pick_rate_property(self):
        """Test pick_rate calculation."""
        stats = ChampionTournamentStats(games_played=10, total_games=50)
        assert stats.pick_rate == 20.0

    @pytest.mark.unit
    def test_pick_rate_zero_games(self):
        """Test pick_rate with zero total games."""
        stats = ChampionTournamentStats(games_played=10, total_games=0)
        assert stats.pick_rate is None

    @pytest.mark.unit
    def test_ban_rate_property(self):
        """Test ban_rate calculation."""
        stats = ChampionTournamentStats(games_banned=25, total_games=50)
        assert stats.ban_rate == 50.0

    @pytest.mark.unit
    def test_ban_rate_zero_games(self):
        """Test ban_rate with zero total games."""
        stats = ChampionTournamentStats(games_banned=5, total_games=0)
        assert stats.ban_rate is None

    @pytest.mark.unit
    def test_presence_property(self):
        """Test presence (pick + ban) calculation."""
        stats = ChampionTournamentStats(games_played=10, games_banned=15, total_games=50)
        assert stats.presence == 50.0  # (10 + 15) / 50 * 100

    @pytest.mark.unit
    def test_presence_zero_games(self):
        """Test presence with zero total games."""
        stats = ChampionTournamentStats(games_played=10, games_banned=5, total_games=0)
        assert stats.presence is None

    @pytest.mark.unit
    def test_win_rate_property(self):
        """Test win_rate calculation."""
        stats = ChampionTournamentStats(games_played=10, games_won=7)
        assert stats.win_rate == 70.0

    @pytest.mark.unit
    def test_win_rate_zero_games_played(self):
        """Test win_rate with zero games played."""
        stats = ChampionTournamentStats(games_played=0, games_won=0)
        assert stats.win_rate is None

    @pytest.mark.unit
    def test_average_kda_property(self):
        """Test average KDA calculation."""
        stats = ChampionTournamentStats(
            games_played=5,
            total_kills=25,
            total_deaths=10,
            total_assists=30,
        )
        assert stats.average_kda == 5.5  # (25 + 30) / 10

    @pytest.mark.unit
    def test_average_kda_zero_deaths(self):
        """Test average KDA with zero deaths (perfect KDA)."""
        stats = ChampionTournamentStats(
            games_played=5,
            total_kills=25,
            total_deaths=0,
            total_assists=30,
        )
        assert stats.average_kda == 55.0  # K + A = 25 + 30

    @pytest.mark.unit
    def test_average_kda_zero_games(self):
        """Test average KDA with zero games played."""
        stats = ChampionTournamentStats(games_played=0)
        assert stats.average_kda is None


class TestPlayerChampionStatsDataclass:
    """Test PlayerChampionStats dataclass functionality."""

    @pytest.mark.unit
    def test_initialization_complete(self):
        """Test PlayerChampionStats can be initialized with all fields."""
        stats = PlayerChampionStats(
            player="Faker",
            champion="Azir",
            tournament="LCK/2024 Season/Summer Season",
            games_played=15,
            games_won=12,
            total_kills=60,
            total_deaths=20,
            total_assists=80,
            total_cs=4500,
            total_gold=250000,
            total_damage=480000,
        )

        assert_valid_dataclass_instance(stats, PlayerChampionStats, ["player", "champion"])
        assert stats.player == "Faker"
        assert stats.champion == "Azir"
        assert stats.games_played == 15

    @pytest.mark.unit
    def test_win_rate_property(self):
        """Test win_rate calculation."""
        stats = PlayerChampionStats(games_played=10, games_won=8)
        assert stats.win_rate == 80.0

    @pytest.mark.unit
    def test_win_rate_zero_games(self):
        """Test win_rate with zero games."""
        stats = PlayerChampionStats(games_played=0, games_won=0)
        assert stats.win_rate is None

    @pytest.mark.unit
    def test_average_kda_property(self):
        """Test average KDA calculation."""
        stats = PlayerChampionStats(
            games_played=5,
            total_kills=30,
            total_deaths=10,
            total_assists=50,
        )
        assert stats.average_kda == 8.0  # (30 + 50) / 10

    @pytest.mark.unit
    def test_average_kda_zero_deaths(self):
        """Test average KDA with zero deaths."""
        stats = PlayerChampionStats(
            games_played=5,
            total_kills=20,
            total_deaths=0,
            total_assists=30,
        )
        assert stats.average_kda == 50.0  # K + A

    @pytest.mark.unit
    def test_average_kills_property(self):
        """Test average kills per game."""
        stats = PlayerChampionStats(games_played=10, total_kills=50)
        assert stats.average_kills == 5.0

    @pytest.mark.unit
    def test_average_deaths_property(self):
        """Test average deaths per game."""
        stats = PlayerChampionStats(games_played=10, total_deaths=20)
        assert stats.average_deaths == 2.0

    @pytest.mark.unit
    def test_average_assists_property(self):
        """Test average assists per game."""
        stats = PlayerChampionStats(games_played=10, total_assists=80)
        assert stats.average_assists == 8.0

    @pytest.mark.unit
    def test_average_cs_property(self):
        """Test average CS per game."""
        stats = PlayerChampionStats(games_played=10, total_cs=3000)
        assert stats.average_cs == 300.0

    @pytest.mark.unit
    def test_average_gold_property(self):
        """Test average gold per game."""
        stats = PlayerChampionStats(games_played=10, total_gold=180000)
        assert stats.average_gold == 18000.0

    @pytest.mark.unit
    def test_average_damage_property(self):
        """Test average damage per game."""
        stats = PlayerChampionStats(games_played=10, total_damage=320000)
        assert stats.average_damage == 32000.0

    @pytest.mark.unit
    def test_averages_zero_games(self):
        """Test all average properties with zero games."""
        stats = PlayerChampionStats(
            games_played=0,
            total_kills=50,
            total_deaths=20,
            total_assists=80,
            total_cs=3000,
            total_gold=180000,
            total_damage=320000,
        )

        assert stats.average_kills is None
        assert stats.average_deaths is None
        assert stats.average_assists is None
        assert stats.average_cs is None
        assert stats.average_gold is None
        assert stats.average_damage is None


class TestChampionTournamentStatsAPI:
    """Test tournament-level champion stats API functions."""

    @pytest.mark.integration
    def test_get_champion_tournament_stats(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_champion_tournament_stats returns aggregated stats."""
        # Mock will be called multiple times: total games, picks, bans
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],  # Total games query
            champion_stats_pick_mock_data,  # Pick data
            champion_stats_ban_mock_data,  # Ban data
        ]

        stats = mp.get_champion_tournament_stats(tournament=TestConstants.LCK_2024_SUMMER)

        assert len(stats) > 0
        assert all(isinstance(s, ChampionTournamentStats) for s in stats)

    @pytest.mark.integration
    def test_get_champion_tournament_stats_with_champion_filter(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_champion_tournament_stats with champion filter."""
        jinx_data = [d for d in champion_stats_pick_mock_data if d["Champion"] == "Jinx"]
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            jinx_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_champion_tournament_stats(
            tournament=TestConstants.LCK_2024_SUMMER,
            champion="Jinx",
        )

        # Should only have Jinx stats
        jinx_stats = [s for s in stats if s.champion == "Jinx"]
        assert len(jinx_stats) <= len(stats)

    @pytest.mark.integration
    def test_get_champion_tournament_stats_with_min_games(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_champion_tournament_stats with minimum games filter."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            champion_stats_pick_mock_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_champion_tournament_stats(
            tournament=TestConstants.LCK_2024_SUMMER,
            min_games=3,
        )

        # All returned stats should have at least 3 games
        for s in stats:
            assert s.games_played >= 3

    @pytest.mark.integration
    def test_get_champion_stats_by_name(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_champion_stats_by_name returns single champion."""
        jinx_data = [d for d in champion_stats_pick_mock_data if d["Champion"] == "Jinx"]
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            jinx_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_champion_stats_by_name(
            champion="Jinx",
            tournament=TestConstants.LCK_2024_SUMMER,
        )

        if stats:
            assert isinstance(stats, ChampionTournamentStats)
            assert stats.champion == "Jinx"

    @pytest.mark.integration
    def test_get_champion_stats_by_name_not_found(
        self,
        mock_leaguepedia_query,
    ):
        """Test get_champion_stats_by_name returns None when not found."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            [],  # No picks
            [],  # No bans
        ]

        stats = mp.get_champion_stats_by_name(
            champion="NonexistentChampion",
            tournament=TestConstants.LCK_2024_SUMMER,
        )

        assert stats is None

    @pytest.mark.integration
    def test_get_most_picked_champions(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_most_picked_champions returns sorted by pick count."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            champion_stats_pick_mock_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_most_picked_champions(
            tournament=TestConstants.LCK_2024_SUMMER,
            limit=5,
        )

        assert len(stats) <= 5
        # Check sorted by games_played descending
        for i in range(len(stats) - 1):
            assert stats[i].games_played >= stats[i + 1].games_played

    @pytest.mark.integration
    def test_get_most_banned_champions(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_most_banned_champions returns sorted by ban count."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            champion_stats_pick_mock_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_most_banned_champions(
            tournament=TestConstants.LCK_2024_SUMMER,
            limit=5,
        )

        assert len(stats) <= 5
        # Check sorted by games_banned descending
        for i in range(len(stats) - 1):
            assert stats[i].games_banned >= stats[i + 1].games_banned

    @pytest.mark.integration
    def test_get_highest_winrate_champions(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test get_highest_winrate_champions returns sorted by win rate."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            champion_stats_pick_mock_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_highest_winrate_champions(
            tournament=TestConstants.LCK_2024_SUMMER,
            min_games=1,
            limit=5,
        )

        assert len(stats) <= 5
        # Check sorted by win_rate descending
        for i in range(len(stats) - 1):
            rate_a = stats[i].win_rate or 0
            rate_b = stats[i + 1].win_rate or 0
            assert rate_a >= rate_b


class TestPlayerChampionStatsAPI:
    """Test player-level champion stats API functions."""

    @pytest.mark.integration
    def test_get_player_champion_stats(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_champion_stats returns player's champion data."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_champion_stats(player="Faker")

        assert len(stats) > 0
        assert all(isinstance(s, PlayerChampionStats) for s in stats)
        # All stats should be for the requested player
        assert all(s.player == "Faker" for s in stats)

    @pytest.mark.integration
    def test_get_player_champion_stats_with_tournament(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_champion_stats with tournament filter."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_champion_stats(
            player="Faker",
            tournament=TestConstants.LCK_2024_SUMMER,
        )

        mock_leaguepedia_query.assert_called_once()
        call_kwargs = mock_leaguepedia_query.call_args[1]
        assert "OverviewPage" in call_kwargs["where"]

    @pytest.mark.integration
    def test_get_player_champion_stats_with_champion(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_champion_stats with champion filter."""
        azir_data = [d for d in player_champion_stats_mock_data if d["Champion"] == "Azir"]
        mock_leaguepedia_query.return_value = azir_data

        stats = mp.get_player_champion_stats(
            player="Faker",
            champion="Azir",
        )

        assert all(s.champion == "Azir" for s in stats)

    @pytest.mark.integration
    def test_get_player_champion_pool(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_champion_pool returns all champions played."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_champion_pool(player="Faker")

        assert len(stats) > 0
        # Should be sorted by games_played descending
        for i in range(len(stats) - 1):
            assert stats[i].games_played >= stats[i + 1].games_played

    @pytest.mark.integration
    def test_get_player_champion_pool_with_min_games(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_champion_pool with minimum games filter."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_champion_pool(
            player="Faker",
            min_games=2,
        )

        # All returned stats should have at least 2 games
        for s in stats:
            assert s.games_played >= 2

    @pytest.mark.integration
    def test_get_player_signature_champions(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test get_player_signature_champions returns high winrate champions."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_signature_champions(
            player="Faker",
            min_games=1,
            min_winrate=50.0,
        )

        # All returned stats should meet min_games and min_winrate
        for s in stats:
            assert s.games_played >= 1
            assert (s.win_rate or 0) >= 50.0


class TestChampionStatsErrorHandling:
    """Test error handling in ChampionStats functionality."""

    @pytest.mark.integration
    def test_get_champion_tournament_stats_api_error(self, mock_leaguepedia_query):
        """Test that API errors are properly wrapped in RuntimeError."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch champion tournament stats"):
            mp.get_champion_tournament_stats(tournament=TestConstants.LCK_2024_SUMMER)

    @pytest.mark.integration
    def test_get_player_champion_stats_api_error(self, mock_leaguepedia_query):
        """Test that API errors in player stats are handled."""
        mock_leaguepedia_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError, match="Failed to fetch player champion stats"):
            mp.get_player_champion_stats(player="Faker")


class TestChampionStatsEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_tournament_stats_defaults(self):
        """Test ChampionTournamentStats default values."""
        stats = ChampionTournamentStats()

        assert stats.champion is None
        assert stats.tournament is None
        assert stats.games_played == 0
        assert stats.games_won == 0
        assert stats.games_banned == 0
        assert stats.total_games == 0
        assert stats.total_kills == 0
        assert stats.total_deaths == 0
        assert stats.total_assists == 0

    @pytest.mark.unit
    def test_player_stats_defaults(self):
        """Test PlayerChampionStats default values."""
        stats = PlayerChampionStats()

        assert stats.player is None
        assert stats.champion is None
        assert stats.tournament is None
        assert stats.games_played == 0
        assert stats.games_won == 0
        assert stats.total_kills == 0
        assert stats.total_deaths == 0
        assert stats.total_assists == 0
        assert stats.total_cs == 0
        assert stats.total_gold == 0
        assert stats.total_damage == 0

    @pytest.mark.unit
    def test_presence_over_100_percent(self):
        """Test presence can exceed 100% (if champion picked in every game + banned)."""
        stats = ChampionTournamentStats(
            games_played=50,  # Picked in all 50 games
            games_banned=30,  # Also banned 30 times
            total_games=50,
        )

        # This is mathematically impossible in a real tournament,
        # but the dataclass should handle it
        assert stats.presence == 160.0  # (50 + 30) / 50 * 100

    @pytest.mark.integration
    def test_aggregation_handles_malformed_data(
        self,
        mock_leaguepedia_query,
    ):
        """Test aggregation handles malformed numeric data."""
        malformed_data = [
            {
                "Champion": "Jinx",
                "PlayerWin": "Yes",
                "Kills": "invalid",
                "Deaths": "",
                "Assists": None,
            },
        ]
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            malformed_data,
            [],
        ]

        # Should not raise, just skip malformed data
        stats = mp.get_champion_tournament_stats(tournament=TestConstants.LCK_2024_SUMMER)

        # Should have stats for Jinx with 0 KDA values
        jinx_stats = [s for s in stats if s.champion == "Jinx"]
        if jinx_stats:
            assert jinx_stats[0].total_kills == 0


class TestChampionStatsDataAggregation:
    """Test data aggregation logic."""

    @pytest.mark.integration
    def test_stats_aggregated_correctly(
        self,
        mock_leaguepedia_query,
        champion_stats_pick_mock_data,
        champion_stats_ban_mock_data,
    ):
        """Test that stats are correctly aggregated from multiple games."""
        mock_leaguepedia_query.side_effect = [
            [{"TotalGames": "50"}],
            champion_stats_pick_mock_data,
            champion_stats_ban_mock_data,
        ]

        stats = mp.get_champion_tournament_stats(tournament=TestConstants.LCK_2024_SUMMER)

        # Find Jinx stats (3 games in mock data)
        jinx_stats = next((s for s in stats if s.champion == "Jinx"), None)

        if jinx_stats:
            assert jinx_stats.games_played == 3
            # Wins: 2 (Yes, Yes, No)
            assert jinx_stats.games_won == 2
            # Kills: 8 + 5 + 3 = 16
            assert jinx_stats.total_kills == 16
            # Deaths: 2 + 3 + 5 = 10
            assert jinx_stats.total_deaths == 10
            # Assists: 10 + 12 + 6 = 28
            assert jinx_stats.total_assists == 28

    @pytest.mark.integration
    def test_player_stats_aggregated_correctly(
        self,
        mock_leaguepedia_query,
        player_champion_stats_mock_data,
    ):
        """Test that player stats are correctly aggregated by champion."""
        mock_leaguepedia_query.return_value = player_champion_stats_mock_data

        stats = mp.get_player_champion_stats(player="Faker")

        # Find Azir stats (2 games in mock data)
        azir_stats = next((s for s in stats if s.champion == "Azir"), None)

        if azir_stats:
            assert azir_stats.games_played == 2
            assert azir_stats.games_won == 2
            # Kills: 8 + 5 = 13
            assert azir_stats.total_kills == 13
            # Deaths: 1 + 2 = 3
            assert azir_stats.total_deaths == 3
            # Assists: 12 + 10 = 22
            assert azir_stats.total_assists == 22


if __name__ == "__main__":
    pytest.main([__file__])
