import dataclasses
from typing import List, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import match_schedule_game_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class GameVod:
    """Represents VOD information for a single game.

    Attributes:
        game_id: Unique identifier for the game
        match_id: Identifier for the match containing this game
        vod_url: URL to the VOD
        vod_game_start: Timestamp within the VOD where the game starts (format: HH:MM:SS)
        team_blue: Team on blue side
        team_red: Team on red side
        tournament: Tournament overview page
        winner: 1 for blue team win, 2 for red team win
        game_number: Game number within the match
        mvp: MVP player for this game
        match_history_url: URL to match history
    """

    game_id: Optional[str] = None
    match_id: Optional[str] = None
    vod_url: Optional[str] = None
    vod_game_start: Optional[str] = None
    team_blue: Optional[str] = None
    team_red: Optional[str] = None
    tournament: Optional[str] = None
    winner: Optional[int] = None
    game_number: Optional[int] = None
    mvp: Optional[str] = None
    match_history_url: Optional[str] = None

    @property
    def has_vod(self) -> bool:
        """Returns True if a VOD URL is available."""
        return bool(self.vod_url)

    @property
    def winning_team(self) -> Optional[str]:
        """Returns the name of the winning team."""
        if self.winner == 1:
            return self.team_blue
        elif self.winner == 2:
            return self.team_red
        return None

    @property
    def vod_start_seconds(self) -> Optional[int]:
        """Converts vod_game_start timestamp to seconds.

        Returns:
            Total seconds from start of VOD, or None if not available
        """
        if not self.vod_game_start:
            return None

        try:
            parts = self.vod_game_start.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
        except (ValueError, AttributeError):
            return None

        return None


def _parse_vod_data(data: dict) -> GameVod:
    """Parses raw API response data into a GameVod object."""

    def parse_int(value: Optional[str]) -> Optional[int]:
        try:
            return int(value) if value and str(value).strip() else None
        except (ValueError, TypeError):
            return None

    return GameVod(
        game_id=data.get("GameId"),
        match_id=data.get("MatchId"),
        vod_url=data.get("Vod") or None,
        vod_game_start=data.get("VodGameStart") or None,
        team_blue=data.get("Blue"),
        team_red=data.get("Red"),
        tournament=data.get("OverviewPage"),
        winner=parse_int(data.get("Winner")),
        game_number=parse_int(data.get("N_GameInMatch")),
        mvp=data.get("MVP") or None,
        match_history_url=data.get("MatchHistory") or None,
    )


# Fields to query for VOD information
vods_fields = {
    "GameId",
    "MatchId",
    "Vod",
    "VodGameStart",
    "Blue",
    "Red",
    "OverviewPage",
    "Winner",
    "N_GameInMatch",
    "MVP",
    "MatchHistory",
}


def get_vods(
    tournament: str = None,
    team: str = None,
    with_vod_only: bool = True,
    limit: int = None,
    order_by: str = None,
) -> List[GameVod]:
    """Returns VOD information for games.

    Args:
        tournament: Tournament overview page to filter by
        team: Team name to filter by (matches either blue or red side)
        with_vod_only: If True, only return games with VODs (default: True)
        limit: Maximum number of results to return
        order_by: SQL ORDER BY clause

    Returns:
        A list of GameVod objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        if tournament:
            where_conditions.append(
                QueryBuilder.build_where("MatchScheduleGame", {"OverviewPage": tournament})
            )

        if team:
            escaped_team = QueryBuilder.escape(team)
            where_conditions.append(
                f"(MatchScheduleGame.Blue='{escaped_team}' OR MatchScheduleGame.Red='{escaped_team}')"
            )

        if with_vod_only:
            where_conditions.append("MatchScheduleGame.Vod IS NOT NULL")
            where_conditions.append("MatchScheduleGame.Vod != ''")

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        query_kwargs = {}
        if limit:
            query_kwargs["limit"] = limit
        if order_by:
            query_kwargs["order_by"] = order_by

        results = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(vods_fields),
            where=where_clause,
            **query_kwargs,
        )

        return [_parse_vod_data(row) for row in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch VODs: {str(e)}")


def get_vod_by_game_id(game_id: str) -> Optional[GameVod]:
    """Returns VOD information for a specific game.

    Args:
        game_id: The unique game identifier

    Returns:
        GameVod object if found, None otherwise

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_clause = QueryBuilder.build_where("MatchScheduleGame", {"GameId": game_id})

        results = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(vods_fields),
            where=where_clause,
        )

        return _parse_vod_data(results[0]) if results else None

    except Exception as e:
        raise RuntimeError(f"Failed to fetch VOD for game {game_id}: {str(e)}")


def get_vods_by_match(match_id: str) -> List[GameVod]:
    """Returns VOD information for all games in a match.

    Args:
        match_id: The match identifier

    Returns:
        A list of GameVod objects for all games in the match

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_clause = QueryBuilder.build_where("MatchScheduleGame", {"MatchId": match_id})

        results = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(vods_fields),
            where=where_clause,
            order_by="MatchScheduleGame.N_GameInMatch",
        )

        return [_parse_vod_data(row) for row in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch VODs for match {match_id}: {str(e)}")


def get_team_vods(
    team: str,
    tournament: str = None,
    limit: int = None,
) -> List[GameVod]:
    """Returns VOD information for a specific team's games.

    Args:
        team: Team name to filter by
        tournament: Optional tournament to filter by
        limit: Maximum number of results to return

    Returns:
        A list of GameVod objects for the team's games

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    return get_vods(tournament=tournament, team=team, with_vod_only=True, limit=limit)


def get_tournament_vods(
    tournament: str,
    with_vod_only: bool = True,
    limit: int = None,
) -> List[GameVod]:
    """Returns VOD information for all games in a tournament.

    Args:
        tournament: Tournament overview page
        with_vod_only: If True, only return games with VODs (default: True)
        limit: Maximum number of results to return

    Returns:
        A list of GameVod objects for the tournament

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    return get_vods(tournament=tournament, with_vod_only=with_vod_only, limit=limit)
