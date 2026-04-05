"""Parser for Tenures Cargo table from Leaguepedia."""

import dataclasses
from typing import List, Optional
from datetime import datetime, timezone

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import tenures_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class Tenure:
    """Represents a player tenure from Leaguepedia's Tenures table.

    Attributes:
        player: Player name
        team: Team name
        date_join: Date the player joined the team
        date_leave: Date the player left the team (None if still on team)
        duration: Duration in days
        is_current: Whether this is the player's current team
        next_team: The team the player joined after leaving
        next_is_retired: Whether the player retired after this tenure
        contract_end: Contract end date/info
        roster_change_id_join: ID of the roster change for joining
        roster_change_id_leave: ID of the roster change for leaving
        residency_leave: Player's residency status when leaving
        name_leave: Player's name when leaving (if renamed)
    """

    player: Optional[str] = None
    team: Optional[str] = None
    date_join: Optional[datetime] = None
    date_leave: Optional[datetime] = None
    duration: Optional[int] = None
    is_current: Optional[bool] = None
    next_team: Optional[str] = None
    next_is_retired: Optional[bool] = None
    contract_end: Optional[str] = None
    roster_change_id_join: Optional[str] = None
    roster_change_id_leave: Optional[str] = None
    residency_leave: Optional[str] = None
    name_leave: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Returns True if this is a current tenure with no leave date."""
        return bool(self.is_current) and self.date_leave is None

    @property
    def duration_months(self) -> Optional[float]:
        """Returns the duration converted to months (approx 30.44 days/month)."""
        if self.duration is None:
            return None
        return round(self.duration / 30.44, 1)

    @property
    def duration_years(self) -> Optional[float]:
        """Returns the duration converted to years."""
        if self.duration is None:
            return None
        return round(self.duration / 365.25, 2)

    @property
    def ended_in_retirement(self) -> bool:
        """Returns True if the player retired after this tenure."""
        return bool(self.next_is_retired)


def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a datetime value from the API response."""
    try:
        if date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        return None
    except (ValueError, AttributeError):
        return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    """Parse an integer value from the API response."""
    try:
        if value and str(value).strip() and str(value).strip().lstrip("-").isdigit():
            return int(value)
        return None
    except (ValueError, TypeError):
        return None


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    """Parse a boolean value from the API response."""
    if isinstance(value, bool):
        return value
    if not value:
        return None
    return str(value).lower() in ["yes", "true", "1"]


def _parse_tenure_data(data: dict) -> Tenure:
    """Parses raw API response data into a Tenure object."""
    return Tenure(
        player=data.get("Player"),
        team=data.get("Team"),
        date_join=_parse_datetime(data.get("DateJoin")),
        date_leave=_parse_datetime(data.get("DateLeave")),
        duration=_parse_int(data.get("Duration")),
        is_current=_parse_bool(data.get("IsCurrent")),
        next_team=data.get("NextTeam"),
        next_is_retired=_parse_bool(data.get("NextIsRetired")),
        contract_end=data.get("ContractEnd"),
        roster_change_id_join=data.get("RosterChangeIdJoin"),
        roster_change_id_leave=data.get("RosterChangeIdLeave"),
        residency_leave=data.get("ResidencyLeave"),
        name_leave=data.get("NameLeave"),
    )


def get_tenures(
    player: str = None,
    team: str = None,
    current_only: bool = False,
    limit: int = None,
) -> List[Tenure]:
    """Returns tenure information from Leaguepedia.

    Args:
        player: Player name to filter by
        team: Team name to filter by
        current_only: Only return current tenures
        limit: Maximum number of tenures to return

    Returns:
        A list of Tenure objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        exact_where = QueryBuilder.build_where(
            "Tenures",
            {
                "Player": player,
                "Team": team,
            }
        )
        if exact_where:
            where_conditions.append(exact_where)

        if current_only:
            where_conditions.append("Tenures.IsCurrent='1'")

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        tenures = leaguepedia.query(
            tables="Tenures",
            fields=",".join(tenures_fields),
            where=where_clause,
            order_by="Tenures.DateJoin DESC",
        )

        parsed_tenures = [_parse_tenure_data(tenure) for tenure in tenures]
        return parsed_tenures[:limit] if limit else parsed_tenures

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tenures: {str(e)}")


def get_player_tenures(player: str) -> List[Tenure]:
    """Returns all tenures for a specific player.

    Args:
        player: Player name

    Returns:
        A list of Tenure objects for the specified player, ordered by join date
    """
    return get_tenures(player=player)


def get_team_tenures(team: str, current_only: bool = False) -> List[Tenure]:
    """Returns all tenures at a specific team.

    Args:
        team: Team name
        current_only: Only return current tenures

    Returns:
        A list of Tenure objects for the specified team
    """
    return get_tenures(team=team, current_only=current_only)


def get_current_roster_tenures(team: str) -> List[Tenure]:
    """Returns tenures for the current roster of a team.

    Args:
        team: Team name

    Returns:
        A list of Tenure objects for current players on the team
    """
    return get_tenures(team=team, current_only=True)


def get_longest_tenures(team: str = None, limit: int = 10) -> List[Tenure]:
    """Returns the longest tenures, optionally filtered by team.

    Args:
        team: Optional team name to filter by
        limit: Maximum number of tenures to return (default: 10)

    Returns:
        A list of Tenure objects sorted by duration (longest first)

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        if team:
            escaped = QueryBuilder.escape(team)
            where_conditions.append(f"Tenures.Team='{escaped}'")

        where_conditions.append("Tenures.Duration IS NOT NULL")

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        tenures = leaguepedia.query(
            tables="Tenures",
            fields=",".join(tenures_fields),
            where=where_clause,
            order_by="Tenures.Duration DESC",
        )

        parsed_tenures = [_parse_tenure_data(tenure) for tenure in tenures]
        return parsed_tenures[:limit] if limit else parsed_tenures

    except Exception as e:
        raise RuntimeError(f"Failed to fetch longest tenures: {str(e)}")
