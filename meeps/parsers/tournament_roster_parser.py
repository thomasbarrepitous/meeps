import dataclasses
from typing import List, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.parsers.query_builder import QueryBuilder
from meeps.transmuters.field_names import (
    tournament_rosters_fields,
)


@dataclasses.dataclass
class TournamentRoster:
    """Represents a tournament roster from Leaguepedia's TournamentRosters table.

    Attributes:
        team: Team name
        overview_page: Tournament overview page
        region: Region of the tournament
        roster_links: Links to player pages (semicolon-delimited)
        roles: Player roles (semicolon-delimited)
        flags: Player nationality flags (semicolon-delimited)
        footnotes: Roster footnotes
        is_used: Whether this roster was used
        tournament: Tournament name
        short: Short tournament identifier
        is_complete: Whether the roster is complete
        page_and_team: Combined page and team identifier
        unique_line: Unique line identifier
    """

    team: Optional[str] = None
    overview_page: Optional[str] = None
    region: Optional[str] = None
    roster_links: Optional[str] = None
    roles: Optional[str] = None
    flags: Optional[str] = None
    footnotes: Optional[str] = None
    is_used: Optional[bool] = None
    tournament: Optional[str] = None
    short: Optional[str] = None
    is_complete: Optional[bool] = None
    page_and_team: Optional[str] = None
    unique_line: Optional[str] = None

    @property
    def roster_links_list(self) -> List[str]:
        """Returns roster links as a list."""
        if self.roster_links:
            return [link.strip() for link in self.roster_links.split(";;") if link.strip()]
        return []

    @property
    def roles_list(self) -> List[str]:
        """Returns roles as a list."""
        if self.roles:
            return [role.strip() for role in self.roles.split(";;") if role.strip()]
        return []

    @property
    def flags_list(self) -> List[str]:
        """Returns flags as a list."""
        if self.flags:
            return [flag.strip() for flag in self.flags.split(";;") if flag.strip()]
        return []


def _parse_tournament_roster_data(data: dict) -> TournamentRoster:
    """Parses raw API response data into a TournamentRoster object."""

    def parse_bool(value: Optional[str]) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        return value == "Yes" if value else None

    return TournamentRoster(
        team=data.get("Team"),
        overview_page=data.get("OverviewPage"),
        region=data.get("Region"),
        roster_links=data.get("RosterLinks"),
        roles=data.get("Roles"),
        flags=data.get("Flags"),
        footnotes=data.get("Footnotes"),
        is_used=parse_bool(data.get("IsUsed")),
        tournament=data.get("Tournament"),
        short=data.get("Short"),
        is_complete=parse_bool(data.get("IsComplete")),
        page_and_team=data.get("PageAndTeam"),
        unique_line=data.get("UniqueLine"),
    )


def get_tournament_rosters(
    team: str,
    tournament: str = None,
    region: str = None,
    is_complete: bool = None,
    order_by: str = None,
) -> List[TournamentRoster]:
    """Returns tournament roster information from Leaguepedia for a specific team.

    Args:
        team: The team name to filter by
        tournament: Optional tournament name to filter by
        region: Optional region to filter by
        is_complete: Optional filter for complete rosters only
        order_by: Optional ordering (e.g., "TournamentRosters.Tournament DESC")

    Returns:
        A list of TournamentRoster objects for the specified team

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        conditions = {"Team": team}
        if tournament:
            conditions["Tournament"] = tournament
        if region:
            conditions["Region"] = region
        if is_complete is not None:
            conditions["IsComplete"] = "Yes" if is_complete else "No"

        where_clause = QueryBuilder.build_where("TournamentRosters", conditions)

        query_kwargs = {}
        if order_by:
            query_kwargs["order_by"] = order_by

        rosters = leaguepedia.query(
            tables="TournamentRosters",
            fields=",".join(tournament_rosters_fields),
            where=where_clause,
            **query_kwargs,
        )

        return [_parse_tournament_roster_data(roster) for roster in rosters]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch tournament rosters: {str(e)}")
