"""Tests for QueryBuilder class - SQL query construction and escaping."""

import pytest
from meeps.parsers.query_builder import QueryBuilder


class TestQueryBuilderEscape:
    """Tests for QueryBuilder.escape() - SQL injection prevention."""

    def test_escape_single_quotes(self):
        """Single quotes are doubled to prevent SQL injection."""
        result = QueryBuilder.escape("O'Brien")
        assert result == "O''Brien"

    def test_escape_multiple_single_quotes(self):
        """Multiple single quotes are all escaped."""
        result = QueryBuilder.escape("it's a 'test'")
        assert result == "it''s a ''test''"

    def test_escape_no_quotes(self):
        """Strings without quotes pass through unchanged."""
        result = QueryBuilder.escape("Faker")
        assert result == "Faker"

    def test_escape_empty_string(self):
        """Empty strings are handled."""
        result = QueryBuilder.escape("")
        assert result == ""

    def test_escape_numeric_value(self):
        """Numeric values are converted to strings."""
        result = QueryBuilder.escape(123)
        assert result == "123"

    def test_escape_unicode(self):
        """Unicode characters pass through correctly."""
        result = QueryBuilder.escape("Smeb's 한글")
        assert result == "Smeb''s 한글"

    def test_escape_sql_injection_attempt(self):
        """Common SQL injection patterns are neutralized."""
        result = QueryBuilder.escape("'; DROP TABLE Players; --")
        assert result == "''; DROP TABLE Players; --"
        # The doubled quote prevents the string from being terminated early


class TestQueryBuilderBuildWhere:
    """Tests for QueryBuilder.build_where() - WHERE clause construction."""

    def test_build_where_single_condition(self):
        """Single condition produces correct WHERE clause."""
        result = QueryBuilder.build_where("Players", {"Name": "Faker"})
        assert result == "Players.Name='Faker'"

    def test_build_where_multiple_conditions(self):
        """Multiple conditions are joined with AND."""
        result = QueryBuilder.build_where("Players", {"Name": "Faker", "Team": "T1"})
        assert "Players.Name='Faker'" in result
        assert "Players.Team='T1'" in result
        assert " AND " in result

    def test_build_where_none_values_ignored(self):
        """None values are filtered out."""
        result = QueryBuilder.build_where("Players", {"Name": "Faker", "Team": None})
        assert result == "Players.Name='Faker'"
        assert "Team" not in result

    def test_build_where_all_none_returns_none(self):
        """All None values returns None."""
        result = QueryBuilder.build_where("Players", {"Name": None, "Team": None})
        assert result is None

    def test_build_where_empty_dict_returns_none(self):
        """Empty dictionary returns None."""
        result = QueryBuilder.build_where("Players", {})
        assert result is None

    def test_build_where_escapes_values(self):
        """Values are properly escaped."""
        result = QueryBuilder.build_where("Players", {"Name": "O'Brien"})
        assert result == "Players.Name='O''Brien'"

    def test_build_where_numeric_values(self):
        """Numeric values are converted to strings."""
        result = QueryBuilder.build_where("Tournaments", {"Year": 2024})
        assert result == "Tournaments.Year='2024'"

    def test_build_where_boolean_as_int(self):
        """Boolean-like integers are handled."""
        result = QueryBuilder.build_where("Tournaments", {"IsPlayoffs": 1})
        assert result == "Tournaments.IsPlayoffs='1'"


class TestQueryBuilderBuildLikeCondition:
    """Tests for QueryBuilder.build_like_condition() - LIKE pattern building."""

    def test_build_like_basic(self):
        """Basic LIKE condition with wildcards."""
        result = QueryBuilder.build_like_condition("Players", "Link", "Faker")
        assert result == "Players.Link LIKE '%Faker%'"

    def test_build_like_escapes_quotes(self):
        """Single quotes in value are escaped."""
        result = QueryBuilder.build_like_condition("Players", "Name", "O'Brien")
        assert result == "Players.Name LIKE '%O''Brien%'"

    def test_build_like_empty_value(self):
        """Empty value produces wildcard-only pattern."""
        result = QueryBuilder.build_like_condition("Players", "Name", "")
        assert result == "Players.Name LIKE '%%'"

    def test_build_like_numeric_value(self):
        """Numeric values are converted to strings."""
        result = QueryBuilder.build_like_condition("Players", "ID", 123)
        assert result == "Players.ID LIKE '%123%'"


class TestQueryBuilderBuildRangeCondition:
    """Tests for QueryBuilder.build_range_condition() - range condition building."""

    def test_build_range_min_only(self):
        """Min value only produces >= condition."""
        result = QueryBuilder.build_range_condition("Champions", "AttackRange", min_value=200)
        assert result == "Champions.AttackRange >= 200"

    def test_build_range_max_only(self):
        """Max value only produces <= condition."""
        result = QueryBuilder.build_range_condition("Champions", "AttackRange", max_value=500)
        assert result == "Champions.AttackRange <= 500"

    def test_build_range_both_values(self):
        """Both min and max produce combined condition."""
        result = QueryBuilder.build_range_condition(
            "Champions", "AttackRange", min_value=200, max_value=500
        )
        assert "Champions.AttackRange >= 200" in result
        assert "Champions.AttackRange <= 500" in result
        assert " AND " in result

    def test_build_range_no_values_returns_none(self):
        """No values returns None."""
        result = QueryBuilder.build_range_condition("Champions", "AttackRange")
        assert result is None

    def test_build_range_with_quoted_strings(self):
        """String values with quotes pass through as-is for date comparisons."""
        result = QueryBuilder.build_range_condition(
            "Contracts", "ContractEnd",
            min_value="'2024-01-01'",
            max_value="'2024-12-31'"
        )
        assert "Contracts.ContractEnd >= '2024-01-01'" in result
        assert "Contracts.ContractEnd <= '2024-12-31'" in result


class TestQueryBuilderRealWorldScenarios:
    """Tests for real-world usage patterns found in the codebase."""

    def test_tournament_filter(self):
        """Filtering tournaments by region and year."""
        result = QueryBuilder.build_where(
            "Tournaments",
            {
                "Region": "Korea",
                "Year": 2024,
                "TournamentLevel": "Primary",
            }
        )
        assert "Tournaments.Region='Korea'" in result
        assert "Tournaments.Year='2024'" in result
        assert "Tournaments.TournamentLevel='Primary'" in result

    def test_player_lookup(self):
        """Looking up a player by name."""
        result = QueryBuilder.build_where("P", {"Player": "Faker"})
        assert result == "P.Player='Faker'"

    def test_game_query(self):
        """Querying games by overview page."""
        result = QueryBuilder.build_where(
            "ScoreboardGames",
            {"OverviewPage": "LCK/2024 Season/Summer Season"}
        )
        assert "ScoreboardGames.OverviewPage='LCK/2024 Season/Summer Season'" in result

    def test_contract_filter(self):
        """Filtering contracts by player and team."""
        result = QueryBuilder.build_where(
            "Contracts",
            {"Player": "Faker", "Team": "T1"}
        )
        assert "Contracts.Player='Faker'" in result
        assert "Contracts.Team='T1'" in result

    def test_sql_injection_in_tournament_name(self):
        """Malicious tournament name is escaped."""
        result = QueryBuilder.build_where(
            "Tournaments",
            {"OverviewPage": "LCK'; DELETE FROM Tournaments; --"}
        )
        assert "LCK''" in result  # Quote is doubled


class TestQueryBuilderEdgeCases:
    """Edge cases and boundary conditions."""

    def test_table_with_alias(self):
        """Table aliases work correctly."""
        result = QueryBuilder.build_where("T", {"Team": "T1"})
        assert result == "T.Team='T1'"

    def test_long_table_name(self):
        """Long table names work correctly."""
        result = QueryBuilder.build_where("ScoreboardPlayers", {"Link": "Faker"})
        assert result == "ScoreboardPlayers.Link='Faker'"

    def test_special_field_names(self):
        """Fields with underscores work correctly."""
        result = QueryBuilder.build_where("Games", {"DateTime_UTC": "2024-01-01"})
        assert result == "Games.DateTime_UTC='2024-01-01'"

    def test_zero_value(self):
        """Zero is treated as a valid value, not filtered out."""
        result = QueryBuilder.build_where("Tournaments", {"IsPlayoffs": 0})
        assert result == "Tournaments.IsPlayoffs='0'"

    def test_false_value(self):
        """False boolean is converted to string."""
        result = QueryBuilder.build_where("Players", {"IsRetired": False})
        assert result == "Players.IsRetired='False'"

    def test_empty_string_value(self):
        """Empty string is treated as a valid value."""
        result = QueryBuilder.build_where("Players", {"Team": ""})
        assert result == "Players.Team=''"

    def test_whitespace_value(self):
        """Whitespace-only strings are preserved."""
        result = QueryBuilder.build_where("Players", {"Name": "  "})
        assert result == "Players.Name='  '"
