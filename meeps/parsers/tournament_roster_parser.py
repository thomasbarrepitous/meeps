from typing import List, Dict, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import (
    tournament_rosters_fields,
)


def get_tournament_rosters(team: str, tournament: str = None, **kwargs) -> List[Dict]:
    """Returns tournament roster information from Leaguepedia for a specific team.

    Typical usage examples:
        get_tournament_rosters(team="G2 Esports")
        get_tournament_rosters(team="G2 Esports", tournament="LEC 2023 Summer")

    Args:
        team: The team name to filter by
        tournament: Optional tournament name to further filter results
        **kwargs: Additional filters to apply to the query

    Returns:
        A list of dictionaries containing tournament roster information for the specified team
    """
    where_conditions = [f"TournamentRosters.Team='{team}'"]

    if tournament:
        where_conditions.append(f"TournamentRosters.Tournament='{tournament}'")

    # Add any additional filters from kwargs
    for key, value in kwargs.items():
        if isinstance(value, str):
            where_conditions.append(f"TournamentRosters.{key}='{value}'")
        else:
            where_conditions.append(f"TournamentRosters.{key}={value}")

    where_clause = " AND ".join(where_conditions)

    rosters = leaguepedia.query(
        tables="TournamentRosters",
        fields=",".join(tournament_rosters_fields),
        where=where_clause,
        **kwargs,
    )

    return rosters
