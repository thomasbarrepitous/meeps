"""Tests for player_parser module - player data extraction and parsing."""

import pytest
import datetime
from unittest.mock import patch, Mock

from meeps.parsers.player_parser import (
    PlayerInfo,
    PlayerStatus,
    get_player_by_name,
    is_active,
    _parse_player_data,
    _FULL_QUERY_FIELDS,
)


class TestPlayerInfoDataclass:
    """Tests for PlayerInfo dataclass initialization and properties."""

    def test_player_info_minimal_initialization(self):
        """PlayerInfo can be created with minimal data."""
        player = PlayerInfo(player="Faker")
        assert player.player == "Faker"
        assert player.team is None
        assert player.role is None

    def test_player_info_full_initialization(self):
        """PlayerInfo can be created with all fields."""
        player = PlayerInfo(
            id="12345",
            overview_page="Faker",
            player="Faker",
            name="Lee Sang-hyeok",
            native_name="이상혁",
            country="Korea",
            nationality=["Korean"],
            team="T1",
            role="Mid",
            age=28,
            birthdate=datetime.date(1996, 5, 7),
            twitter="faker",
            is_retired=False,
        )
        assert player.id == "12345"
        assert player.player == "Faker"
        assert player.name == "Lee Sang-hyeok"
        assert player.team == "T1"
        assert player.role == "Mid"
        assert player.age == 28
        assert player.nationality == ["Korean"]

    def test_player_info_default_lists(self):
        """List fields default to empty lists."""
        player = PlayerInfo()
        assert player.nationality == []
        assert player.current_teams == []
        assert player.role_last == []
        assert player.fav_champs == []

    def test_player_info_status_active(self):
        """Active players have ACTIVE status."""
        player = PlayerInfo(is_retired=False, to_wildrift=False, to_valorant=False)
        assert player.status == PlayerStatus.ACTIVE

    def test_player_info_status_moved_to_wildrift(self):
        """Players who moved to Wild Rift have MOVED_TO_WILDRIFT status."""
        player = PlayerInfo(to_wildrift=True)
        assert player.status == PlayerStatus.MOVED_TO_WILDRIFT

    def test_player_info_status_moved_to_valorant(self):
        """Players who moved to Valorant have MOVED_TO_VALORANT status."""
        player = PlayerInfo(to_valorant=True)
        assert player.status == PlayerStatus.MOVED_TO_VALORANT

    def test_player_info_status_wildrift_takes_precedence(self):
        """Wild Rift status takes precedence over Valorant."""
        player = PlayerInfo(to_wildrift=True, to_valorant=True)
        assert player.status == PlayerStatus.MOVED_TO_WILDRIFT


class TestPlayerStatusEnum:
    """Tests for PlayerStatus enum."""

    def test_player_status_values(self):
        """All status values are defined."""
        assert PlayerStatus.ACTIVE.value == 0
        assert PlayerStatus.RETIRED.value == 1
        assert PlayerStatus.MOVED_TO_WILDRIFT.value == 2
        assert PlayerStatus.MOVED_TO_VALORANT.value == 3


class TestIsActiveFunction:
    """Tests for is_active() helper function."""

    def test_is_active_true(self):
        """Active players return True."""
        player = PlayerInfo(is_retired=False, to_wildrift=False, to_valorant=False)
        assert is_active(player) is True

    def test_is_active_none_values(self):
        """None values are treated as falsy."""
        player = PlayerInfo(is_retired=None, to_wildrift=None, to_valorant=None)
        assert is_active(player) is True

    def test_is_active_retired(self):
        """Retired players return False."""
        player = PlayerInfo(is_retired=True)
        assert is_active(player) is False

    def test_is_active_moved_to_wildrift(self):
        """Players who moved to Wild Rift return False."""
        player = PlayerInfo(to_wildrift=True)
        assert is_active(player) is False

    def test_is_active_moved_to_valorant(self):
        """Players who moved to Valorant return False."""
        player = PlayerInfo(to_valorant=True)
        assert is_active(player) is False


class TestParsePlayerData:
    """Tests for _parse_player_data() function."""

    def test_parse_basic_fields(self):
        """Basic string fields are parsed correctly."""
        data = {
            "ID": "12345",
            "OverviewPage": "Faker",
            "Player": "Faker",
            "Name": "Lee Sang-hyeok",
            "Team": "T1",
            "Role": "Mid",
        }
        player = _parse_player_data(data)
        assert player.id == "12345"
        assert player.overview_page == "Faker"
        assert player.player == "Faker"
        assert player.name == "Lee Sang-hyeok"
        assert player.team == "T1"
        assert player.role == "Mid"

    def test_parse_date_fields(self):
        """Date fields are parsed to date objects."""
        data = {
            "Birthdate": "1996-05-07",
            "Contract": "2025-12-31",
        }
        player = _parse_player_data(data)
        assert player.birthdate == datetime.date(1996, 5, 7)
        assert player.contract == datetime.date(2025, 12, 31)

    def test_parse_invalid_date_returns_none(self):
        """Invalid date strings return None."""
        data = {
            "Birthdate": "not-a-date",
            "Contract": "invalid",
        }
        player = _parse_player_data(data)
        assert player.birthdate is None
        assert player.contract is None

    def test_parse_empty_date_returns_none(self):
        """Empty date strings return None."""
        data = {"Birthdate": "", "Contract": None}
        player = _parse_player_data(data)
        assert player.birthdate is None
        assert player.contract is None

    def test_parse_list_fields_comma_separated(self):
        """Comma-separated lists are parsed correctly."""
        data = {
            "Nationality": "Korean, American",
            "CurrentTeams": "T1, T1 Academy",
            "FavChamps": "Azir, Ryze, LeBlanc",
        }
        player = _parse_player_data(data)
        assert player.nationality == ["Korean", "American"]
        assert player.current_teams == ["T1", "T1 Academy"]
        assert player.fav_champs == ["Azir", "Ryze", "LeBlanc"]

    def test_parse_list_fields_semicolon_separated(self):
        """Semicolon-separated lists are parsed correctly."""
        data = {"RoleLast": "Mid;Top;Support"}
        player = _parse_player_data(data)
        assert player.role_last == ["Mid", "Top", "Support"]

    def test_parse_empty_list_fields(self):
        """Empty list fields return empty lists."""
        data = {"Nationality": "", "FavChamps": None}
        player = _parse_player_data(data)
        assert player.nationality == []
        assert player.fav_champs == []

    def test_parse_age_field(self):
        """Age field is parsed to integer."""
        data = {"Age": "28"}
        player = _parse_player_data(data)
        assert player.age == 28

    def test_parse_age_non_numeric_returns_none(self):
        """Non-numeric age returns None."""
        data = {"Age": "unknown"}
        player = _parse_player_data(data)
        assert player.age is None

    def test_parse_boolean_fields(self):
        """Boolean fields parse 'Yes' to True."""
        data = {
            "IsRetired": "Yes",
            "ToWildrift": "Yes",
            "ToValorant": "Yes",
            "IsPersonality": "Yes",
            "IsSubstitute": "Yes",
        }
        player = _parse_player_data(data)
        assert player.is_retired is True
        assert player.to_wildrift is True
        assert player.to_valorant is True
        assert player.is_personality is True
        assert player.is_substitute is True

    def test_parse_boolean_fields_no(self):
        """Boolean fields parse 'No' to False, empty to None."""
        data = {
            "IsRetired": "No",
            "ToWildrift": "",
        }
        player = _parse_player_data(data)
        assert player.is_retired is False  # "No" == "Yes" is False
        assert player.to_wildrift is None  # Empty string returns None

    def test_parse_social_media_fields(self):
        """Social media fields are parsed correctly."""
        data = {
            "Twitter": "faker",
            "Instagram": "faker",
            "Stream": "https://twitch.tv/faker",
            "Youtube": "faker_official",
            "Discord": "faker#1234",
        }
        player = _parse_player_data(data)
        assert player.twitter == "faker"
        assert player.instagram == "faker"
        assert player.stream == "https://twitch.tv/faker"
        assert player.youtube == "faker_official"
        assert player.discord == "faker#1234"

    def test_parse_missing_fields_default_to_none(self):
        """Missing fields default to None or empty lists."""
        data = {}
        player = _parse_player_data(data)
        assert player.player is None
        assert player.team is None
        assert player.nationality == []

    def test_parse_all_full_query_fields(self):
        """All fields in _FULL_QUERY_FIELDS can be parsed."""
        data = {field: f"test_{field}" for field in _FULL_QUERY_FIELDS}
        # Override specific fields that need special handling
        data["Age"] = "25"
        data["Birthdate"] = "2000-01-01"
        data["IsRetired"] = "Yes"

        player = _parse_player_data(data)
        # Verify it doesn't raise an exception
        assert player is not None


class TestGetPlayerByName:
    """Tests for get_player_by_name() function."""

    @patch("meeps.parsers.player_parser.leaguepedia.query")
    def test_get_player_by_name_success(self, mock_query):
        """Successfully retrieves player by name."""
        mock_query.return_value = [
            {
                "ID": "12345",
                "Player": "Faker",
                "Name": "Lee Sang-hyeok",
                "Team": "T1",
                "Role": "Mid",
                "Country": "Korea",
            }
        ]

        player = get_player_by_name("Faker")

        assert player.player == "Faker"
        assert player.name == "Lee Sang-hyeok"
        assert player.team == "T1"
        assert player.role == "Mid"
        mock_query.assert_called_once()

    @patch("meeps.parsers.player_parser.leaguepedia.query")
    def test_get_player_by_name_not_found(self, mock_query):
        """Raises ValueError when player is not found."""
        mock_query.return_value = []

        with pytest.raises(RuntimeError) as exc_info:
            get_player_by_name("NonexistentPlayer")

        assert "not found" in str(exc_info.value)

    @patch("meeps.parsers.player_parser.leaguepedia.query")
    def test_get_player_by_name_api_error(self, mock_query):
        """Raises RuntimeError on API error."""
        mock_query.side_effect = Exception("API connection failed")

        with pytest.raises(RuntimeError) as exc_info:
            get_player_by_name("Faker")

        assert "Failed to fetch player data" in str(exc_info.value)

    @patch("meeps.parsers.player_parser.leaguepedia.query")
    def test_get_player_by_name_queries_correct_table(self, mock_query):
        """Queries the Players table with correct fields."""
        mock_query.return_value = [{"Player": "Faker"}]

        get_player_by_name("Faker")

        call_args = mock_query.call_args
        assert call_args[1]["tables"] == "Players=P"
        assert "P.Player='Faker'" in call_args[1]["where"]

    @patch("meeps.parsers.player_parser.leaguepedia.query")
    def test_get_player_by_name_sql_injection_protection(self, mock_query):
        """Player name is properly escaped."""
        mock_query.return_value = [{"Player": "O'Brien"}]

        get_player_by_name("O'Brien")

        call_args = mock_query.call_args
        assert "O''Brien" in call_args[1]["where"]


class TestPlayerInfoComplexScenarios:
    """Tests for complex real-world player data scenarios."""

    def test_korean_player_with_native_name(self):
        """Korean players with native names are parsed correctly."""
        data = {
            "Player": "Faker",
            "Name": "Lee Sang-hyeok",
            "NativeName": "이상혁",
            "Country": "Korea",
            "Nationality": "Korean",
            "Residency": "Korea",
        }
        player = _parse_player_data(data)
        assert player.player == "Faker"
        assert player.native_name == "이상혁"
        assert player.nationality == ["Korean"]

    def test_player_with_multiple_nationalities(self):
        """Players with multiple nationalities are parsed correctly."""
        data = {
            "Player": "CoreJJ",
            "Nationality": "Korean, American",
            "NationalityPrimary": "American",
            "Residency": "North America",
            "ResidencyFormer": "Korea",
        }
        player = _parse_player_data(data)
        assert player.nationality == ["Korean", "American"]
        assert player.nationality_primary == "American"
        assert player.residency == "North America"
        assert player.residency_former == "Korea"

    def test_retired_player(self):
        """Retired player data is parsed correctly."""
        data = {
            "Player": "Madlife",
            "Team": "",
            "TeamLast": "CJ Entus",
            "Role": "",
            "RoleLast": "Support",
            "IsRetired": "Yes",
        }
        player = _parse_player_data(data)
        assert player.is_retired is True
        assert player.team_last == "CJ Entus"
        assert is_active(player) is False

    def test_player_moved_to_valorant(self):
        """Player who moved to Valorant is parsed correctly."""
        data = {
            "Player": "TenZ",
            "ToValorant": "Yes",
            "TeamLast": "Cloud9",
        }
        player = _parse_player_data(data)
        assert player.to_valorant is True
        assert player.status == PlayerStatus.MOVED_TO_VALORANT
        assert is_active(player) is False

    def test_substitute_player(self):
        """Substitute players are parsed correctly."""
        data = {
            "Player": "Ellim",
            "Team": "T1",
            "Role": "Jungle",
            "IsSubstitute": "Yes",
        }
        player = _parse_player_data(data)
        assert player.is_substitute is True

    def test_player_with_all_social_media(self):
        """Player with all social media links is parsed correctly."""
        data = {
            "Player": "Faker",
            "Twitter": "faker",
            "Instagram": "faker",
            "Stream": "https://twitch.tv/faker",
            "Youtube": "faker",
            "Discord": "faker#0001",
            "Facebook": "faker.lol",
            "Reddit": "u/faker",
            "Website": "https://faker.com",
            "Bluesky": "@faker.bsky.social",
            "Threads": "faker",
            "LinkedIn": "faker-lol",
        }
        player = _parse_player_data(data)
        assert player.twitter == "faker"
        assert player.instagram == "faker"
        assert player.stream == "https://twitch.tv/faker"
        assert player.youtube == "faker"
        assert player.discord == "faker#0001"
        assert player.facebook == "faker.lol"
        assert player.reddit == "u/faker"
        assert player.website == "https://faker.com"
        assert player.bluesky == "@faker.bsky.social"
        assert player.threads == "faker"
        assert player.linkedin == "faker-lol"


class TestFullQueryFields:
    """Tests for _FULL_QUERY_FIELDS constant."""

    def test_full_query_fields_contains_required_fields(self):
        """All essential fields are in _FULL_QUERY_FIELDS."""
        required = [
            "ID", "OverviewPage", "Player", "Name", "Team", "Role",
            "Country", "Nationality", "Age", "Birthdate",
            "Twitter", "IsRetired",
        ]
        for field in required:
            assert field in _FULL_QUERY_FIELDS, f"Missing field: {field}"

    def test_full_query_fields_no_duplicates(self):
        """No duplicate fields in _FULL_QUERY_FIELDS."""
        assert len(_FULL_QUERY_FIELDS) == len(set(_FULL_QUERY_FIELDS))
