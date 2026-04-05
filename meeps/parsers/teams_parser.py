"""Parser for Teams Cargo table from Leaguepedia."""

import dataclasses
from typing import List, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import teams_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class Team:
    """Represents a team from Leaguepedia's Teams table.

    Attributes:
        name: Full team name
        short: Short name/trigram (e.g., "T1", "GEN")
        region: Team's region (e.g., "Korea", "Europe")
        link: Wiki page link
        overview_page: Overview page path
        image: Team logo image filename
        is_disbanded: Whether the team has disbanded
        renamed_to: New name if team was renamed
        location: Team's location/headquarters
    """

    name: Optional[str] = None
    short: Optional[str] = None
    region: Optional[str] = None
    link: Optional[str] = None
    overview_page: Optional[str] = None
    image: Optional[str] = None
    is_disbanded: Optional[bool] = None
    renamed_to: Optional[str] = None
    location: Optional[str] = None

    @property
    def is_active(self) -> Optional[bool]:
        """Returns True if the team is not disbanded and not renamed."""
        if self.is_disbanded is True:
            return False
        if self.renamed_to:
            return False
        return True

    @property
    def display_name(self) -> Optional[str]:
        """Returns the full name, or short name if full name is unavailable."""
        return self.name or self.short

    @property
    def trigram(self) -> Optional[str]:
        """Alias for short name (team trigram/abbreviation)."""
        return self.short

    @property
    def has_rebranded(self) -> bool:
        """Returns True if the team has been renamed to another organization."""
        return self.renamed_to is not None and self.renamed_to != ""


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    """Parse a boolean value from the API response."""
    if isinstance(value, bool):
        return value
    if not value:
        return None
    return value.lower() in ["yes", "true", "1"]


def _parse_team_data(data: dict) -> Team:
    """Parses raw API response data into a Team object."""
    return Team(
        name=data.get("Name"),
        short=data.get("Short"),
        region=data.get("Region"),
        link=data.get("Link"),
        overview_page=data.get("OverviewPage"),
        image=data.get("Image"),
        is_disbanded=_parse_bool(data.get("IsDisbanded")),
        renamed_to=data.get("RenamedTo"),
        location=data.get("Location"),
    )


def get_teams(
    region: str = None,
    include_disbanded: bool = True,
    include_renamed: bool = True,
    limit: int = None,
) -> List[Team]:
    """Returns team information from Leaguepedia.

    Args:
        region: Region to filter by (e.g., "Korea", "Europe")
        include_disbanded: Whether to include disbanded teams
        include_renamed: Whether to include teams that have been renamed
        limit: Maximum number of teams to return

    Returns:
        A list of Team objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        if region:
            escaped_region = QueryBuilder.escape(region)
            where_conditions.append(f"Teams.Region='{escaped_region}'")

        if not include_disbanded:
            where_conditions.append(
                "(Teams.IsDisbanded IS NULL OR Teams.IsDisbanded='')"
            )

        if not include_renamed:
            where_conditions.append(
                "(Teams.RenamedTo IS NULL OR Teams.RenamedTo='')"
            )

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        teams = leaguepedia.query(
            tables="Teams",
            fields=",".join(teams_fields),
            where=where_clause,
            order_by="Teams.Name",
        )

        parsed_teams = [_parse_team_data(team) for team in teams]
        return parsed_teams[:limit] if limit else parsed_teams

    except Exception as e:
        raise RuntimeError(f"Failed to fetch teams: {str(e)}")


def get_team_by_name(name: str) -> Optional[Team]:
    """Returns a team by its full name.

    Args:
        name: Full team name to search for

    Returns:
        Team object if found, None otherwise

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_clause = QueryBuilder.build_where("Teams", {"Name": name})

        teams = leaguepedia.query(
            tables="Teams",
            fields=",".join(teams_fields),
            where=where_clause,
        )

        if teams:
            return _parse_team_data(teams[0])
        return None

    except Exception as e:
        raise RuntimeError(f"Failed to fetch team by name: {str(e)}")


def get_team_by_short(short: str) -> Optional[Team]:
    """Returns a team by its short name/trigram.

    Args:
        short: Short name/trigram to search for (e.g., "T1", "GEN")

    Returns:
        Team object if found, None otherwise

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_clause = QueryBuilder.build_where("Teams", {"Short": short})

        teams = leaguepedia.query(
            tables="Teams",
            fields=",".join(teams_fields),
            where=where_clause,
        )

        if teams:
            return _parse_team_data(teams[0])
        return None

    except Exception as e:
        raise RuntimeError(f"Failed to fetch team by short name: {str(e)}")


def get_teams_by_region(region: str, active_only: bool = False) -> List[Team]:
    """Returns all teams from a specific region.

    Args:
        region: Region to filter by (e.g., "Korea", "Europe")
        active_only: Whether to only return active teams

    Returns:
        A list of Team objects from the specified region
    """
    return get_teams(
        region=region,
        include_disbanded=not active_only,
        include_renamed=not active_only,
    )


def get_active_teams(region: str = None) -> List[Team]:
    """Returns only active teams (not disbanded or renamed).

    Args:
        region: Optional region to filter by

    Returns:
        A list of active Team objects
    """
    return get_teams(
        region=region,
        include_disbanded=False,
        include_renamed=False,
    )


def get_disbanded_teams(region: str = None, limit: int = None) -> List[Team]:
    """Returns disbanded teams.

    Args:
        region: Optional region to filter by
        limit: Maximum number of teams to return

    Returns:
        A list of disbanded Team objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = ["Teams.IsDisbanded='Yes'"]

        if region:
            escaped_region = QueryBuilder.escape(region)
            where_conditions.append(f"Teams.Region='{escaped_region}'")

        where_clause = " AND ".join(where_conditions)

        teams = leaguepedia.query(
            tables="Teams",
            fields=",".join(teams_fields),
            where=where_clause,
            order_by="Teams.Name",
        )

        parsed_teams = [_parse_team_data(team) for team in teams]
        return parsed_teams[:limit] if limit else parsed_teams

    except Exception as e:
        raise RuntimeError(f"Failed to fetch disbanded teams: {str(e)}")


def search_teams(query: str, region: str = None) -> List[Team]:
    """Search for teams with names matching the query.

    Uses LIKE matching to find teams whose name contains the query string.

    Args:
        query: Search string to match against team names
        region: Optional region to filter by

    Returns:
        A list of matching Team objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = [
            QueryBuilder.build_like_condition("Teams", "Name", query)
        ]

        if region:
            escaped_region = QueryBuilder.escape(region)
            where_conditions.append(f"Teams.Region='{escaped_region}'")

        where_clause = " AND ".join(where_conditions)

        teams = leaguepedia.query(
            tables="Teams",
            fields=",".join(teams_fields),
            where=where_clause,
            order_by="Teams.Name",
        )

        return [_parse_team_data(team) for team in teams]

    except Exception as e:
        raise RuntimeError(f"Failed to search teams: {str(e)}")
