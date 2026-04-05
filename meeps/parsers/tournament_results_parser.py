"""Parser for TournamentResults Cargo table from Leaguepedia."""

import dataclasses
from typing import List, Optional
from datetime import datetime, timezone

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import tournament_results_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class TournamentResult:
    """Represents a tournament result from Leaguepedia's TournamentResults table.

    Attributes:
        event: Tournament event name
        team: Team name
        place: Placement string (e.g., "1st", "2nd", "3rd-4th")
        place_number: Numeric placement value
        overview_page: Tournament overview page
        tier: Tournament tier
        date: Tournament date
        phase: Tournament phase
        prize: Prize amount (in local currency)
        prize_usd: Prize amount in USD
        prize_unit: Currency unit for prize
        qualified: Whether the team qualified for something
        is_achievement: Whether this is an achievement result
        is_showmatch: Whether this was a showmatch
        last_result: Result of the team's last match
        last_opponent_markup: Markup for the last opponent
        last_outcome: Outcome of the last match
    """

    event: Optional[str] = None
    team: Optional[str] = None
    place: Optional[str] = None
    place_number: Optional[int] = None
    overview_page: Optional[str] = None
    tier: Optional[str] = None
    date: Optional[datetime] = None
    phase: Optional[str] = None
    prize: Optional[int] = None
    prize_usd: Optional[float] = None
    prize_unit: Optional[str] = None
    qualified: Optional[bool] = None
    is_achievement: Optional[bool] = None
    is_showmatch: Optional[bool] = None
    last_result: Optional[str] = None
    last_opponent_markup: Optional[str] = None
    last_outcome: Optional[str] = None

    @property
    def is_winner(self) -> bool:
        """Returns True if the team won (place_number == 1)."""
        return self.place_number == 1

    @property
    def is_top_4(self) -> bool:
        """Returns True if the team placed in top 4."""
        return self.place_number is not None and self.place_number <= 4

    @property
    def has_prize(self) -> bool:
        """Returns True if prize data exists."""
        return self.prize is not None or self.prize_usd is not None

    @property
    def prize_display(self) -> Optional[str]:
        """Returns formatted prize string (e.g., '$50,000 USD')."""
        if self.prize_usd is not None:
            return f"${self.prize_usd:,.0f} USD"
        if self.prize is not None:
            unit = self.prize_unit or ""
            return f"{self.prize:,} {unit}".strip()
        return None


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


def _parse_float(value: Optional[str]) -> Optional[float]:
    """Parse a float value from the API response."""
    try:
        if value and str(value).strip():
            return float(value)
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


def _parse_tournament_result_data(data: dict) -> TournamentResult:
    """Parses raw API response data into a TournamentResult object."""
    return TournamentResult(
        event=data.get("Event"),
        team=data.get("Team"),
        place=data.get("Place"),
        place_number=_parse_int(data.get("Place_Number")),
        overview_page=data.get("OverviewPage"),
        tier=data.get("Tier"),
        date=_parse_datetime(data.get("Date")),
        phase=data.get("Phase"),
        prize=_parse_int(data.get("Prize")),
        prize_usd=_parse_float(data.get("Prize_USD")),
        prize_unit=data.get("PrizeUnit"),
        qualified=_parse_bool(data.get("Qualified")),
        is_achievement=_parse_bool(data.get("IsAchievement")),
        is_showmatch=_parse_bool(data.get("Showmatch")),
        last_result=data.get("LastResult"),
        last_opponent_markup=data.get("LastOpponent_Markup"),
        last_outcome=data.get("LastOutcome"),
    )


def get_tournament_results(
    overview_page: str = None,
    team: str = None,
    tier: str = None,
    limit: int = None,
) -> List[TournamentResult]:
    """Returns tournament results from Leaguepedia.

    Args:
        overview_page: Tournament overview page to filter by
        team: Team name to filter by
        tier: Tournament tier to filter by
        limit: Maximum number of results to return

    Returns:
        A list of TournamentResult objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        exact_where = QueryBuilder.build_where(
            "TournamentResults",
            {
                "OverviewPage": overview_page,
                "Team": team,
                "Tier": tier,
            }
        )
        if exact_where:
            where_conditions.append(exact_where)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        results = leaguepedia.query(
            tables="TournamentResults",
            fields=",".join(tournament_results_fields),
            where=where_clause,
            order_by="TournamentResults.Date DESC",
        )

        parsed_results = [_parse_tournament_result_data(result) for result in results]
        return parsed_results[:limit] if limit else parsed_results

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tournament results: {str(e)}")


def get_team_tournament_history(
    team: str,
    tier: str = None,
    limit: int = None,
) -> List[TournamentResult]:
    """Returns all tournament results for a specific team.

    Args:
        team: Team name
        tier: Optional tournament tier to filter by
        limit: Maximum number of results to return

    Returns:
        A list of TournamentResult objects for the specified team
    """
    return get_tournament_results(team=team, tier=tier, limit=limit)


def get_tournament_placements(overview_page: str) -> List[TournamentResult]:
    """Returns all placements in a tournament.

    Args:
        overview_page: Tournament overview page

    Returns:
        A list of TournamentResult objects ordered by placement

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        escaped = QueryBuilder.escape(overview_page)
        where_clause = f"TournamentResults.OverviewPage='{escaped}'"

        results = leaguepedia.query(
            tables="TournamentResults",
            fields=",".join(tournament_results_fields),
            where=where_clause,
            order_by="TournamentResults.Place_Number ASC",
        )

        return [_parse_tournament_result_data(result) for result in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tournament placements: {str(e)}")


def get_tournament_winners(tier: str = None, limit: int = None) -> List[TournamentResult]:
    """Returns first place finishes, optionally filtered by tier.

    Args:
        tier: Optional tournament tier to filter by
        limit: Maximum number of results to return

    Returns:
        A list of TournamentResult objects for first place finishes

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = ["TournamentResults.Place_Number='1'"]

        if tier:
            escaped = QueryBuilder.escape(tier)
            where_conditions.append(f"TournamentResults.Tier='{escaped}'")

        where_clause = " AND ".join(where_conditions)

        results = leaguepedia.query(
            tables="TournamentResults",
            fields=",".join(tournament_results_fields),
            where=where_clause,
            order_by="TournamentResults.Date DESC",
        )

        parsed_results = [_parse_tournament_result_data(result) for result in results]
        return parsed_results[:limit] if limit else parsed_results

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tournament winners: {str(e)}")


def get_prize_earnings(team: str) -> float:
    """Returns total prize earnings in USD for a team.

    Args:
        team: Team name

    Returns:
        Total prize earnings in USD

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        escaped = QueryBuilder.escape(team)
        where_clause = f"TournamentResults.Team='{escaped}' AND TournamentResults.Prize_USD IS NOT NULL"

        results = leaguepedia.query(
            tables="TournamentResults",
            fields=",".join(tournament_results_fields),
            where=where_clause,
        )

        total = 0.0
        for result in results:
            prize = _parse_float(result.get("Prize_USD"))
            if prize:
                total += prize

        return total

    except Exception as e:
        raise RuntimeError(f"Failed to fetch prize earnings: {str(e)}")
