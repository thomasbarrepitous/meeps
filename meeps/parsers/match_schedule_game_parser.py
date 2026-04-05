"""Parser for MatchScheduleGame Cargo table from Leaguepedia."""

import dataclasses
from typing import List, Optional

from meeps.site.leaguepedia import leaguepedia
from meeps.transmuters.field_names import match_schedule_game_fields
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class MatchScheduleGame:
    """Represents a game from Leaguepedia's MatchScheduleGame table.

    Attributes:
        blue: Blue side team name
        red: Red side team name
        winner: Winner indicator (1=Blue, 2=Red)
        blue_score: Blue team's score
        red_score: Red team's score
        game_id: Unique game identifier
        match_id: Parent match identifier
        overview_page: Tournament overview page
        n_game_in_match: Game number within the match
        is_chronobreak: Whether chronobreak was used
        is_remake: Whether the game was remade
        ff: Forfeit indicator
        first_pick: Team with first pick
        selection: Draft selection info
        mvp: MVP player name
        mvp_points: MVP points awarded
        vod: VOD URL
        vod_game_start: Timestamp when game starts in VOD
        match_history: Match history URL
        riot_platform_game_id: Riot's platform game ID
    """

    blue: Optional[str] = None
    red: Optional[str] = None
    winner: Optional[int] = None
    blue_score: Optional[int] = None
    red_score: Optional[int] = None
    game_id: Optional[str] = None
    match_id: Optional[str] = None
    overview_page: Optional[str] = None
    n_game_in_match: Optional[int] = None
    is_chronobreak: Optional[bool] = None
    is_remake: Optional[bool] = None
    ff: Optional[int] = None
    first_pick: Optional[str] = None
    selection: Optional[str] = None
    mvp: Optional[str] = None
    mvp_points: Optional[int] = None
    vod: Optional[str] = None
    vod_game_start: Optional[str] = None
    match_history: Optional[str] = None
    riot_platform_game_id: Optional[str] = None

    @property
    def blue_won(self) -> bool:
        """Returns True if blue team won."""
        return self.winner == 1

    @property
    def red_won(self) -> bool:
        """Returns True if red team won."""
        return self.winner == 2

    @property
    def winning_team(self) -> Optional[str]:
        """Returns the name of the winning team."""
        if self.winner == 1:
            return self.blue
        if self.winner == 2:
            return self.red
        return None

    @property
    def has_vod(self) -> bool:
        """Returns True if VOD is available."""
        return bool(self.vod)

    @property
    def is_special_game(self) -> bool:
        """Returns True if game was a remake or used chronobreak."""
        return bool(self.is_remake) or bool(self.is_chronobreak)


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


def _parse_match_schedule_game_data(data: dict) -> MatchScheduleGame:
    """Parses raw API response data into a MatchScheduleGame object."""
    return MatchScheduleGame(
        blue=data.get("Blue"),
        red=data.get("Red"),
        winner=_parse_int(data.get("Winner")),
        blue_score=_parse_int(data.get("BlueScore")),
        red_score=_parse_int(data.get("RedScore")),
        game_id=data.get("GameId"),
        match_id=data.get("MatchId"),
        overview_page=data.get("OverviewPage"),
        n_game_in_match=_parse_int(data.get("N_GameInMatch")),
        is_chronobreak=_parse_bool(data.get("IsChronobreak")),
        is_remake=_parse_bool(data.get("IsRemake")),
        ff=_parse_int(data.get("FF")),
        first_pick=data.get("FirstPick"),
        selection=data.get("Selection"),
        mvp=data.get("MVP"),
        mvp_points=_parse_int(data.get("MVPPoints")),
        vod=data.get("Vod"),
        vod_game_start=data.get("VodGameStart"),
        match_history=data.get("MatchHistory"),
        riot_platform_game_id=data.get("RiotPlatformGameId"),
    )


def get_match_schedule_games(
    overview_page: str = None,
    match_id: str = None,
    game_id: str = None,
    limit: int = None,
) -> List[MatchScheduleGame]:
    """Returns match schedule game information from Leaguepedia.

    Args:
        overview_page: Tournament overview page to filter by
        match_id: Match ID to filter by
        game_id: Game ID to filter by
        limit: Maximum number of games to return

    Returns:
        A list of MatchScheduleGame objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        exact_where = QueryBuilder.build_where(
            "MatchScheduleGame",
            {
                "OverviewPage": overview_page,
                "MatchId": match_id,
                "GameId": game_id,
            }
        )
        if exact_where:
            where_conditions.append(exact_where)

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        games = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(match_schedule_game_fields),
            where=where_clause,
            order_by="MatchScheduleGame.N_GameInMatch ASC",
        )

        parsed_games = [_parse_match_schedule_game_data(game) for game in games]
        return parsed_games[:limit] if limit else parsed_games

    except Exception as e:
        raise RuntimeError(f"Failed to fetch match schedule games: {str(e)}")


def get_games_by_match(match_id: str) -> List[MatchScheduleGame]:
    """Returns all games for a specific match.

    Args:
        match_id: The match ID

    Returns:
        A list of MatchScheduleGame objects for the match
    """
    return get_match_schedule_games(match_id=match_id)


def get_games_by_tournament(overview_page: str, limit: int = None) -> List[MatchScheduleGame]:
    """Returns all games for a tournament.

    Args:
        overview_page: Tournament overview page
        limit: Maximum number of games to return

    Returns:
        A list of MatchScheduleGame objects for the tournament
    """
    return get_match_schedule_games(overview_page=overview_page, limit=limit)


def get_mvp_games(
    mvp_player: str,
    overview_page: str = None,
    limit: int = None,
) -> List[MatchScheduleGame]:
    """Returns games where a specific player was MVP.

    Args:
        mvp_player: Player name
        overview_page: Optional tournament to filter by
        limit: Maximum number of games to return

    Returns:
        A list of MatchScheduleGame objects where the player was MVP

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        escaped = QueryBuilder.escape(mvp_player)
        where_conditions.append(f"MatchScheduleGame.MVP='{escaped}'")

        if overview_page:
            escaped_page = QueryBuilder.escape(overview_page)
            where_conditions.append(f"MatchScheduleGame.OverviewPage='{escaped_page}'")

        where_clause = " AND ".join(where_conditions)

        games = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(match_schedule_game_fields),
            where=where_clause,
            order_by="MatchScheduleGame.N_GameInMatch ASC",
        )

        parsed_games = [_parse_match_schedule_game_data(game) for game in games]
        return parsed_games[:limit] if limit else parsed_games

    except Exception as e:
        raise RuntimeError(f"Failed to fetch MVP games: {str(e)}")


def get_remakes(overview_page: str = None, limit: int = None) -> List[MatchScheduleGame]:
    """Returns games that were remakes.

    Args:
        overview_page: Optional tournament to filter by
        limit: Maximum number of games to return

    Returns:
        A list of MatchScheduleGame objects that were remakes

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = ["MatchScheduleGame.IsRemake='1'"]

        if overview_page:
            escaped = QueryBuilder.escape(overview_page)
            where_conditions.append(f"MatchScheduleGame.OverviewPage='{escaped}'")

        where_clause = " AND ".join(where_conditions)

        games = leaguepedia.query(
            tables="MatchScheduleGame",
            fields=",".join(match_schedule_game_fields),
            where=where_clause,
            order_by="MatchScheduleGame.N_GameInMatch ASC",
        )

        parsed_games = [_parse_match_schedule_game_data(game) for game in games]
        return parsed_games[:limit] if limit else parsed_games

    except Exception as e:
        raise RuntimeError(f"Failed to fetch remakes: {str(e)}")
