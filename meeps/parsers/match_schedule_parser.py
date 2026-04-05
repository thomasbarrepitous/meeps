"""Parser for MatchSchedule Cargo table from Leaguepedia."""

import dataclasses
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import match_schedule_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class MatchSchedule:
    """Represents a match from Leaguepedia's MatchSchedule table.

    Attributes:
        team1: First team name
        team2: Second team name
        datetime_utc: Match start time in UTC
        overview_page: Tournament overview page
        best_of: Match format (e.g., 1, 3, 5)
        winner: Winning team (1, 2, or None if not played)
        team1_score: Team 1's game score
        team2_score: Team 2's game score
        team1_points: Team 1's points (for point-based formats)
        team2_points: Team 2's points (for point-based formats)
        stream: Stream URL or identifier
        round: Tournament round/stage
        shown_name: Display name for the match
        is_tiebreaker: Whether this is a tiebreaker match
        has_time: Whether the match has a confirmed time
    """

    team1: Optional[str] = None
    team2: Optional[str] = None
    datetime_utc: Optional[datetime] = None
    overview_page: Optional[str] = None
    best_of: Optional[int] = None
    winner: Optional[str] = None
    team1_score: Optional[int] = None
    team2_score: Optional[int] = None
    team1_points: Optional[int] = None
    team2_points: Optional[int] = None
    stream: Optional[str] = None
    round: Optional[str] = None
    shown_name: Optional[str] = None
    is_tiebreaker: Optional[bool] = None
    has_time: Optional[bool] = None

    @property
    def is_upcoming(self) -> Optional[bool]:
        """Returns True if the match hasn't started yet."""
        if self.datetime_utc is None:
            return None
        return self.datetime_utc > datetime.now(timezone.utc)

    @property
    def is_completed(self) -> bool:
        """Returns True if the match has a winner."""
        return self.winner is not None and self.winner != ""

    @property
    def is_live(self) -> Optional[bool]:
        """Returns True if the match might be in progress.

        A match is considered potentially live if:
        - It has started (datetime is in the past)
        - It has no winner yet
        """
        if self.datetime_utc is None:
            return None
        if self.is_completed:
            return False
        return self.datetime_utc <= datetime.now(timezone.utc)

    @property
    def hours_until_match(self) -> Optional[float]:
        """Returns hours until match start (negative if past)."""
        if self.datetime_utc is None:
            return None
        delta = self.datetime_utc - datetime.now(timezone.utc)
        return delta.total_seconds() / 3600

    @property
    def match_display(self) -> str:
        """Returns a display string like 'Team1 vs Team2'."""
        team1 = self.team1 or "TBD"
        team2 = self.team2 or "TBD"
        return f"{team1} vs {team2}"

    @property
    def score_display(self) -> Optional[str]:
        """Returns score display like '2-1' or None if no scores."""
        if self.team1_score is None or self.team2_score is None:
            return None
        return f"{self.team1_score}-{self.team2_score}"


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
    return value.lower() in ["yes", "true", "1"]


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


def _parse_match_data(data: dict) -> MatchSchedule:
    """Parses raw API response data into a MatchSchedule object."""
    return MatchSchedule(
        team1=data.get("Team1"),
        team2=data.get("Team2"),
        datetime_utc=_parse_datetime(data.get("DateTime_UTC")),
        overview_page=data.get("OverviewPage"),
        best_of=_parse_int(data.get("BestOf")),
        winner=data.get("Winner"),
        team1_score=_parse_int(data.get("Team1Score")),
        team2_score=_parse_int(data.get("Team2Score")),
        team1_points=_parse_int(data.get("Team1Points")),
        team2_points=_parse_int(data.get("Team2Points")),
        stream=data.get("Stream"),
        round=data.get("Round"),
        shown_name=data.get("ShownName"),
        is_tiebreaker=_parse_bool(data.get("IsTiebreaker")),
        has_time=_parse_bool(data.get("HasTime")),
    )


def get_match_schedule(
    tournament: str = None,
    team: str = None,
    start_date: str = None,
    end_date: str = None,
    completed_only: bool = False,
    upcoming_only: bool = False,
    order_by: str = None,
    limit: int = None,
) -> List[MatchSchedule]:
    """Returns match schedule information from Leaguepedia.

    Args:
        tournament: Tournament overview page to filter by
        team: Team name to filter by (matches Team1 OR Team2)
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
        completed_only: Only return completed matches (with winner)
        upcoming_only: Only return upcoming matches (no winner)
        order_by: Optional ordering (e.g., "MatchSchedule.DateTime_UTC ASC")
        limit: Maximum number of matches to return

    Returns:
        A list of MatchSchedule objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        if tournament:
            escaped = QueryBuilder.escape(tournament)
            where_conditions.append(f"MatchSchedule.OverviewPage='{escaped}'")

        if team:
            escaped = QueryBuilder.escape(team)
            where_conditions.append(
                f"(MatchSchedule.Team1='{escaped}' OR MatchSchedule.Team2='{escaped}')"
            )

        if start_date:
            escaped = QueryBuilder.escape(start_date)
            where_conditions.append(f"MatchSchedule.DateTime_UTC >= '{escaped}'")

        if end_date:
            escaped = QueryBuilder.escape(end_date)
            where_conditions.append(f"MatchSchedule.DateTime_UTC <= '{escaped}'")

        if completed_only:
            where_conditions.append(
                "(MatchSchedule.Winner IS NOT NULL AND MatchSchedule.Winner != '')"
            )

        if upcoming_only:
            where_conditions.append(
                "(MatchSchedule.Winner IS NULL OR MatchSchedule.Winner = '')"
            )

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        matches = leaguepedia.query(
            tables="MatchSchedule",
            fields=",".join(match_schedule_fields),
            where=where_clause,
            order_by=order_by or "MatchSchedule.DateTime_UTC ASC",
        )

        parsed_matches = [_parse_match_data(match) for match in matches]
        return parsed_matches[:limit] if limit else parsed_matches

    except Exception as e:
        raise RuntimeError(f"Failed to fetch match schedule: {str(e)}")


def get_upcoming_matches(
    tournament: str = None,
    team: str = None,
    days_ahead: int = 7,
    limit: int = None,
) -> List[MatchSchedule]:
    """Returns upcoming matches within the specified number of days.

    Args:
        tournament: Optional tournament to filter by
        team: Optional team to filter by
        days_ahead: Number of days to look ahead (default: 7)
        limit: Maximum number of matches to return

    Returns:
        A list of upcoming MatchSchedule objects
    """
    start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end_date = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).strftime(
        "%Y-%m-%d"
    )

    return get_match_schedule(
        tournament=tournament,
        team=team,
        start_date=start_date,
        end_date=end_date,
        upcoming_only=True,
        limit=limit,
    )


def get_recent_results(
    tournament: str = None,
    team: str = None,
    days_back: int = 7,
    limit: int = None,
) -> List[MatchSchedule]:
    """Returns recent match results within the specified number of days.

    Args:
        tournament: Optional tournament to filter by
        team: Optional team to filter by
        days_back: Number of days to look back (default: 7)
        limit: Maximum number of matches to return

    Returns:
        A list of completed MatchSchedule objects, ordered by most recent first
    """
    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%d"
    )
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return get_match_schedule(
        tournament=tournament,
        team=team,
        start_date=start_date,
        end_date=end_date,
        completed_only=True,
        order_by="MatchSchedule.DateTime_UTC DESC",
        limit=limit,
    )


def get_team_schedule(
    team: str,
    tournament: str = None,
    include_completed: bool = True,
) -> List[MatchSchedule]:
    """Returns all scheduled matches for a team.

    Args:
        team: Team name to get schedule for
        tournament: Optional tournament to filter by
        include_completed: Whether to include completed matches

    Returns:
        A list of MatchSchedule objects for the team
    """
    return get_match_schedule(
        tournament=tournament,
        team=team,
        completed_only=False,
        upcoming_only=not include_completed,
    )


def get_tournament_schedule(
    tournament: str,
    round_filter: str = None,
) -> List[MatchSchedule]:
    """Returns match schedule for a tournament.

    Args:
        tournament: Tournament overview page
        round_filter: Optional round/stage to filter by

    Returns:
        A list of MatchSchedule objects for the tournament

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = [
            f"MatchSchedule.OverviewPage='{QueryBuilder.escape(tournament)}'"
        ]

        if round_filter:
            escaped = QueryBuilder.escape(round_filter)
            where_conditions.append(f"MatchSchedule.Round='{escaped}'")

        where_clause = " AND ".join(where_conditions)

        matches = leaguepedia.query(
            tables="MatchSchedule",
            fields=",".join(match_schedule_fields),
            where=where_clause,
            order_by="MatchSchedule.DateTime_UTC ASC",
        )

        return [_parse_match_data(match) for match in matches]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tournament schedule: {str(e)}")


def get_today_matches(tournament: str = None) -> List[MatchSchedule]:
    """Returns matches scheduled for today.

    Args:
        tournament: Optional tournament to filter by

    Returns:
        A list of MatchSchedule objects for today
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    return get_match_schedule(
        tournament=tournament,
        start_date=today,
        end_date=tomorrow,
    )


def get_head_to_head(
    team1: str,
    team2: str,
    tournament: str = None,
) -> List[MatchSchedule]:
    """Returns matches between two specific teams.

    Args:
        team1: First team name
        team2: Second team name
        tournament: Optional tournament to filter by

    Returns:
        A list of MatchSchedule objects for matches between the teams

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        escaped_team1 = QueryBuilder.escape(team1)
        escaped_team2 = QueryBuilder.escape(team2)

        where_conditions = [
            f"((MatchSchedule.Team1='{escaped_team1}' AND MatchSchedule.Team2='{escaped_team2}') "
            f"OR (MatchSchedule.Team1='{escaped_team2}' AND MatchSchedule.Team2='{escaped_team1}'))"
        ]

        if tournament:
            escaped = QueryBuilder.escape(tournament)
            where_conditions.append(f"MatchSchedule.OverviewPage='{escaped}'")

        where_clause = " AND ".join(where_conditions)

        matches = leaguepedia.query(
            tables="MatchSchedule",
            fields=",".join(match_schedule_fields),
            where=where_clause,
            order_by="MatchSchedule.DateTime_UTC DESC",
        )

        return [_parse_match_data(match) for match in matches]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch head-to-head matches: {str(e)}")
