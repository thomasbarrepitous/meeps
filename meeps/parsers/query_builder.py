"""Query builder utilities for constructing SQL WHERE clauses safely."""

from typing import Optional, Dict, Any


class QueryBuilder:
    """Builds SQL WHERE clauses with proper escaping and consistency."""

    @staticmethod
    def escape(value: str) -> str:
        """Escape single quotes in SQL values to prevent injection.

        Args:
            value: The value to escape

        Returns:
            Escaped string with single quotes doubled
        """
        return str(value).replace("'", "''")

    @staticmethod
    def build_where(table: str, conditions: Dict[str, Any]) -> Optional[str]:
        """Build a WHERE clause from a dictionary of conditions.

        Args:
            table: Table name to prefix fields with
            conditions: Dictionary of {field: value} pairs. None values are ignored.

        Returns:
            WHERE clause string, or None if no conditions

        Example:
            >>> QueryBuilder.build_where("Teams", {"Name": "T1", "Region": "Korea"})
            "Teams.Name='T1' AND Teams.Region='Korea'"
        """
        clauses = []

        for field, value in conditions.items():
            if value is not None:
                escaped_value = QueryBuilder.escape(str(value))
                clauses.append(f"{table}.{field}='{escaped_value}'")

        return " AND ".join(clauses) if clauses else None

    @staticmethod
    def build_like_condition(table: str, field: str, value: str) -> str:
        """Build a LIKE condition for partial matching.

        Args:
            table: Table name to prefix the field with
            field: Field name to search
            value: Value to match (will be wrapped with %)

        Returns:
            LIKE condition string

        Example:
            >>> QueryBuilder.build_like_condition("Players", "Link", "Faker")
            "Players.Link LIKE '%Faker%'"
        """
        escaped_value = QueryBuilder.escape(str(value))
        return f"{table}.{field} LIKE '%{escaped_value}%'"

    @staticmethod
    def build_range_condition(
        table: str, field: str, min_value: Any = None, max_value: Any = None
    ) -> Optional[str]:
        """Build a range condition (>=, <=, or both).

        Args:
            table: Table name to prefix the field with
            field: Field name to filter
            min_value: Minimum value (inclusive), or None
            max_value: Maximum value (inclusive), or None

        Returns:
            Range condition string, or None if both values are None

        Example:
            >>> QueryBuilder.build_range_condition("Champions", "AttackRange", min_value=200)
            "Champions.AttackRange >= 200"
        """
        conditions = []

        if min_value is not None:
            conditions.append(f"{table}.{field} >= {min_value}")

        if max_value is not None:
            conditions.append(f"{table}.{field} <= {max_value}")

        return " AND ".join(conditions) if conditions else None
