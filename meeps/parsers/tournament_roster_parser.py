from typing import List, Dict, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.parsers.query_builder import QueryBuilder
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
    conditions = {"Team": team}
    if tournament:
        conditions["Tournament"] = tournament
    conditions.update(kwargs)
    where_clause = QueryBuilder.build_where("TournamentRosters", conditions)

    rosters = leaguepedia.query(
        tables="TournamentRosters",
        fields=",".join(tournament_rosters_fields),
        where=where_clause,
        **kwargs,
    )

    return rosters
