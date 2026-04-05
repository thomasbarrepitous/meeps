"""Tests for the MatchScheduleGame parser module."""

import pytest
from unittest.mock import patch

from meeps.parsers.match_schedule_game_parser import (
    MatchScheduleGame,
    get_match_schedule_games,
    get_games_by_match,
    get_games_by_tournament,
    get_mvp_games,
    get_remakes,
    _parse_match_schedule_game_data,
)


class TestMatchScheduleGameDataclass:
    """Tests for the MatchScheduleGame dataclass."""

    def test_default_initialization(self):
        """Test default values for MatchScheduleGame."""
        game = MatchScheduleGame()
        assert game.blue is None
        assert game.red is None
        assert game.winner is None
        assert game.game_id is None
        assert game.is_remake is None

    def test_full_initialization(self):
        """Test MatchScheduleGame with all fields populated."""
        game = MatchScheduleGame(
            blue="T1",
            red="GenG",
            winner=1,
            blue_score=1,
            red_score=0,
            game_id="GAME001",
            match_id="MATCH001",
            overview_page="LCK/2024",
            n_game_in_match=1,
            mvp="Faker",
            vod="https://twitch.tv/vod",
        )
        assert game.blue == "T1"
        assert game.red == "GenG"
        assert game.winner == 1
        assert game.mvp == "Faker"

    def test_blue_won_true(self):
        """Test blue_won returns True when winner is 1."""
        game = MatchScheduleGame(winner=1)
        assert game.blue_won is True
        assert game.red_won is False

    def test_red_won_true(self):
        """Test red_won returns True when winner is 2."""
        game = MatchScheduleGame(winner=2)
        assert game.red_won is True
        assert game.blue_won is False

    def test_winner_none(self):
        """Test blue_won and red_won return False when winner is None."""
        game = MatchScheduleGame(winner=None)
        assert game.blue_won is False
        assert game.red_won is False

    def test_winning_team_blue(self):
        """Test winning_team returns blue team name when blue wins."""
        game = MatchScheduleGame(blue="T1", red="GenG", winner=1)
        assert game.winning_team == "T1"

    def test_winning_team_red(self):
        """Test winning_team returns red team name when red wins."""
        game = MatchScheduleGame(blue="T1", red="GenG", winner=2)
        assert game.winning_team == "GenG"

    def test_winning_team_none(self):
        """Test winning_team returns None when no winner."""
        game = MatchScheduleGame(blue="T1", red="GenG", winner=None)
        assert game.winning_team is None

    def test_has_vod_true(self):
        """Test has_vod returns True when VOD is available."""
        game = MatchScheduleGame(vod="https://twitch.tv/vod")
        assert game.has_vod is True

    def test_has_vod_false(self):
        """Test has_vod returns False when no VOD."""
        game = MatchScheduleGame(vod=None)
        assert game.has_vod is False

    def test_has_vod_empty_string(self):
        """Test has_vod returns False for empty string."""
        game = MatchScheduleGame(vod="")
        assert game.has_vod is False

    def test_is_special_game_remake(self):
        """Test is_special_game returns True for remake."""
        game = MatchScheduleGame(is_remake=True)
        assert game.is_special_game is True

    def test_is_special_game_chronobreak(self):
        """Test is_special_game returns True for chronobreak."""
        game = MatchScheduleGame(is_chronobreak=True)
        assert game.is_special_game is True

    def test_is_special_game_false(self):
        """Test is_special_game returns False for normal game."""
        game = MatchScheduleGame(is_remake=False, is_chronobreak=False)
        assert game.is_special_game is False

    def test_is_special_game_none(self):
        """Test is_special_game returns False when fields are None."""
        game = MatchScheduleGame()
        assert game.is_special_game is False


class TestParseMatchScheduleGameData:
    """Tests for the _parse_match_schedule_game_data function."""

    def test_parse_complete_data(self, match_schedule_game_mock_data):
        """Test parsing complete game data."""
        result = _parse_match_schedule_game_data(match_schedule_game_mock_data[0])
        assert result.blue == "T1"
        assert result.red == "GenG"
        assert result.winner == 1
        assert result.mvp == "Faker"

    def test_parse_empty_data(self):
        """Test parsing empty data."""
        result = _parse_match_schedule_game_data({})
        assert result.blue is None
        assert result.red is None
        assert result.winner is None

    def test_parse_partial_data(self):
        """Test parsing partial data."""
        data = {"Blue": "T1", "Red": "GenG", "Winner": "1"}
        result = _parse_match_schedule_game_data(data)
        assert result.blue == "T1"
        assert result.red == "GenG"
        assert result.winner == 1
        assert result.mvp is None


class TestGetMatchScheduleGames:
    """Tests for the get_match_schedule_games function."""

    def test_get_match_schedule_games_no_filters(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting all games without filters."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_match_schedule_games()
        assert len(result) == 2
        mock_leaguepedia_query.assert_called_once()

    def test_get_match_schedule_games_with_overview_page(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test filtering by overview page."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_match_schedule_games(overview_page="LCK/2024")
        assert len(result) == 2

    def test_get_match_schedule_games_with_match_id(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test filtering by match ID."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[0]]
        result = get_match_schedule_games(match_id="MATCH001")
        assert len(result) == 1

    def test_get_match_schedule_games_with_game_id(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test filtering by game ID."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[0]]
        result = get_match_schedule_games(game_id="GAME001")
        assert len(result) == 1

    def test_get_match_schedule_games_with_limit(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test applying limit."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_match_schedule_games(limit=1)
        assert len(result) == 1

    def test_get_match_schedule_games_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch match schedule games"):
            get_match_schedule_games()


class TestGetGamesByMatch:
    """Tests for the get_games_by_match function."""

    def test_get_games_by_match(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting games for a specific match."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_games_by_match("MATCH001")
        assert len(result) == 2


class TestGetGamesByTournament:
    """Tests for the get_games_by_tournament function."""

    def test_get_games_by_tournament(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting games for a tournament."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_games_by_tournament("LCK/2024")
        assert len(result) == 2

    def test_get_games_by_tournament_with_limit(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test applying limit to tournament games."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_games_by_tournament("LCK/2024", limit=1)
        assert len(result) == 1


class TestGetMvpGames:
    """Tests for the get_mvp_games function."""

    def test_get_mvp_games(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting games where player was MVP."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[0]]
        result = get_mvp_games("Faker")
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "Faker" in call_args[1]["where"]

    def test_get_mvp_games_with_tournament(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting MVP games with tournament filter."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[0]]
        result = get_mvp_games("Faker", overview_page="LCK/2024")
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "LCK/2024" in call_args[1]["where"]

    def test_get_mvp_games_with_limit(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test applying limit to MVP games."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_mvp_games("Faker", limit=1)
        assert len(result) == 1

    def test_get_mvp_games_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch MVP games"):
            get_mvp_games("Faker")


class TestGetRemakes:
    """Tests for the get_remakes function."""

    def test_get_remakes_no_filter(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting remakes without tournament filter."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[1]]
        result = get_remakes()
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "IsRemake='1'" in call_args[1]["where"]

    def test_get_remakes_with_tournament(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test getting remakes with tournament filter."""
        mock_leaguepedia_query.return_value = [match_schedule_game_mock_data[1]]
        result = get_remakes(overview_page="LCK/2024")
        assert len(result) == 1
        call_args = mock_leaguepedia_query.call_args
        assert "LCK/2024" in call_args[1]["where"]

    def test_get_remakes_with_limit(
        self, mock_leaguepedia_query, match_schedule_game_mock_data
    ):
        """Test applying limit to remakes."""
        mock_leaguepedia_query.return_value = match_schedule_game_mock_data
        result = get_remakes(limit=1)
        assert len(result) == 1

    def test_get_remakes_api_error(self, mock_leaguepedia_query):
        """Test handling of API errors."""
        mock_leaguepedia_query.side_effect = Exception("API Error")
        with pytest.raises(RuntimeError, match="Failed to fetch remakes"):
            get_remakes()
