import dataclasses
from typing import List, Optional, Dict, Any
from collections import defaultdict

from meeps.site.leaguepedia import leaguepedia
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class ChampionTournamentStats:
    """Aggregated champion statistics for a tournament.

    Attributes:
        champion: Champion name
        tournament: Tournament overview page
        games_played: Number of games the champion was picked
        games_won: Number of games won when picked
        games_banned: Number of games the champion was banned
        total_games: Total games in the tournament (for rate calculations)
        total_kills: Total kills across all games
        total_deaths: Total deaths across all games
        total_assists: Total assists across all games
    """

    champion: Optional[str] = None
    tournament: Optional[str] = None
    games_played: int = 0
    games_won: int = 0
    games_banned: int = 0
    total_games: int = 0
    total_kills: int = 0
    total_deaths: int = 0
    total_assists: int = 0

    @property
    def pick_rate(self) -> Optional[float]:
        """Returns the pick rate as a percentage (0-100)."""
        if self.total_games == 0:
            return None
        return (self.games_played / self.total_games) * 100

    @property
    def ban_rate(self) -> Optional[float]:
        """Returns the ban rate as a percentage (0-100)."""
        if self.total_games == 0:
            return None
        return (self.games_banned / self.total_games) * 100

    @property
    def presence(self) -> Optional[float]:
        """Returns pick+ban presence as a percentage (0-100)."""
        if self.total_games == 0:
            return None
        return ((self.games_played + self.games_banned) / self.total_games) * 100

    @property
    def win_rate(self) -> Optional[float]:
        """Returns win rate as a percentage (0-100)."""
        if self.games_played == 0:
            return None
        return (self.games_won / self.games_played) * 100

    @property
    def average_kda(self) -> Optional[float]:
        """Returns average KDA ratio.

        Uses (K+A)/D formula; if deaths is 0, returns K+A as perfect KDA.
        """
        if self.games_played == 0:
            return None
        if self.total_deaths == 0:
            return float(self.total_kills + self.total_assists)
        return (self.total_kills + self.total_assists) / self.total_deaths


@dataclasses.dataclass
class PlayerChampionStats:
    """Player-specific champion statistics.

    Attributes:
        player: Player name
        champion: Champion name
        tournament: Tournament overview page (optional, can be career stats)
        games_played: Number of games played on the champion
        games_won: Number of games won on the champion
        total_kills: Total kills on the champion
        total_deaths: Total deaths on the champion
        total_assists: Total assists on the champion
        total_cs: Total CS across all games
        total_gold: Total gold earned
        total_damage: Total damage to champions
    """

    player: Optional[str] = None
    champion: Optional[str] = None
    tournament: Optional[str] = None
    games_played: int = 0
    games_won: int = 0
    total_kills: int = 0
    total_deaths: int = 0
    total_assists: int = 0
    total_cs: int = 0
    total_gold: int = 0
    total_damage: int = 0

    @property
    def win_rate(self) -> Optional[float]:
        """Returns win rate as a percentage (0-100)."""
        if self.games_played == 0:
            return None
        return (self.games_won / self.games_played) * 100

    @property
    def average_kda(self) -> Optional[float]:
        """Returns average KDA ratio."""
        if self.games_played == 0:
            return None
        if self.total_deaths == 0:
            return float(self.total_kills + self.total_assists)
        return (self.total_kills + self.total_assists) / self.total_deaths

    @property
    def average_kills(self) -> Optional[float]:
        """Returns average kills per game."""
        if self.games_played == 0:
            return None
        return self.total_kills / self.games_played

    @property
    def average_deaths(self) -> Optional[float]:
        """Returns average deaths per game."""
        if self.games_played == 0:
            return None
        return self.total_deaths / self.games_played

    @property
    def average_assists(self) -> Optional[float]:
        """Returns average assists per game."""
        if self.games_played == 0:
            return None
        return self.total_assists / self.games_played

    @property
    def average_cs(self) -> Optional[float]:
        """Returns average CS per game."""
        if self.games_played == 0:
            return None
        return self.total_cs / self.games_played

    @property
    def average_gold(self) -> Optional[float]:
        """Returns average gold per game."""
        if self.games_played == 0:
            return None
        return self.total_gold / self.games_played

    @property
    def average_damage(self) -> Optional[float]:
        """Returns average damage per game."""
        if self.games_played == 0:
            return None
        return self.total_damage / self.games_played


def _aggregate_champion_stats(
    pick_data: List[Dict[str, Any]],
    ban_data: List[Dict[str, Any]],
    tournament: str,
    total_games: int,
) -> List[ChampionTournamentStats]:
    """Aggregates raw pick and ban data into champion statistics."""
    stats_by_champion: Dict[str, ChampionTournamentStats] = {}

    # Process picks (from ScoreboardPlayers)
    for row in pick_data:
        champion = row.get("Champion")
        if not champion:
            continue

        if champion not in stats_by_champion:
            stats_by_champion[champion] = ChampionTournamentStats(
                champion=champion,
                tournament=tournament,
                total_games=total_games,
            )

        stats = stats_by_champion[champion]
        stats.games_played += 1

        # Check win
        player_win = row.get("PlayerWin", "")
        if player_win and player_win.lower() in ("yes", "1", "true"):
            stats.games_won += 1

        # Aggregate KDA stats
        try:
            stats.total_kills += int(row.get("Kills", 0) or 0)
            stats.total_deaths += int(row.get("Deaths", 0) or 0)
            stats.total_assists += int(row.get("Assists", 0) or 0)
        except (ValueError, TypeError):
            pass

    # Process bans (from PicksAndBansS7)
    for row in ban_data:
        # Each row has ban columns: Team1Ban1, Team1Ban2, etc.
        for key, value in row.items():
            if "Ban" in key and value:
                champion = value
                if champion not in stats_by_champion:
                    stats_by_champion[champion] = ChampionTournamentStats(
                        champion=champion,
                        tournament=tournament,
                        total_games=total_games,
                    )
                stats_by_champion[champion].games_banned += 1

    return list(stats_by_champion.values())


def _aggregate_player_champion_stats(
    data: List[Dict[str, Any]],
    tournament: str = None,
) -> List[PlayerChampionStats]:
    """Aggregates raw player performance data by champion."""
    stats_by_player_champion: Dict[tuple, PlayerChampionStats] = {}

    for row in data:
        player = row.get("Link") or row.get("Name")
        champion = row.get("Champion")
        if not player or not champion:
            continue

        key = (player, champion)
        if key not in stats_by_player_champion:
            stats_by_player_champion[key] = PlayerChampionStats(
                player=player,
                champion=champion,
                tournament=tournament,
            )

        stats = stats_by_player_champion[key]
        stats.games_played += 1

        # Check win
        player_win = row.get("PlayerWin", "")
        if player_win and player_win.lower() in ("yes", "1", "true"):
            stats.games_won += 1

        # Aggregate stats
        try:
            stats.total_kills += int(row.get("Kills", 0) or 0)
            stats.total_deaths += int(row.get("Deaths", 0) or 0)
            stats.total_assists += int(row.get("Assists", 0) or 0)
            stats.total_cs += int(row.get("CS", 0) or 0)
            stats.total_gold += int(row.get("Gold", 0) or 0)
            stats.total_damage += int(row.get("DamageToChampions", 0) or 0)
        except (ValueError, TypeError):
            pass

    return list(stats_by_player_champion.values())


def get_champion_tournament_stats(
    tournament: str,
    champion: str = None,
    min_games: int = None,
) -> List[ChampionTournamentStats]:
    """Returns aggregated champion statistics for a tournament.

    Args:
        tournament: Tournament overview page
        champion: Optional champion name to filter by
        min_games: Minimum games played to include (default: no minimum)

    Returns:
        A list of ChampionTournamentStats objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        # First get total games in tournament
        total_games_result = leaguepedia.query(
            tables="ScoreboardGames",
            fields="COUNT(DISTINCT GameId)=TotalGames",
            where=QueryBuilder.build_where("ScoreboardGames", {"OverviewPage": tournament}),
        )
        total_games = int(total_games_result[0].get("TotalGames", 0)) if total_games_result else 0

        # Get pick data from ScoreboardPlayers
        pick_where_conditions = [
            QueryBuilder.build_where("ScoreboardPlayers", {"OverviewPage": tournament})
        ]
        if champion:
            pick_where_conditions.append(
                QueryBuilder.build_where("ScoreboardPlayers", {"Champion": champion})
            )

        pick_data = leaguepedia.query(
            tables="ScoreboardPlayers",
            fields="Champion,PlayerWin,Kills,Deaths,Assists",
            where=" AND ".join(pick_where_conditions),
        )

        # Get ban data from PicksAndBansS7 joined with ScoreboardGames
        ban_fields = ",".join(
            [f"Team{t}Ban{b}" for t in [1, 2] for b in range(1, 6)]
        )
        ban_data = leaguepedia.query(
            tables="PicksAndBansS7, ScoreboardGames",
            join_on="PicksAndBansS7.GameId = ScoreboardGames.GameId",
            fields=ban_fields,
            where=QueryBuilder.build_where("ScoreboardGames", {"OverviewPage": tournament}),
        )

        # Aggregate stats
        stats = _aggregate_champion_stats(pick_data, ban_data, tournament, total_games)

        # Filter by champion if specified
        if champion:
            stats = [s for s in stats if s.champion == champion]

        # Filter by min games if specified
        if min_games:
            stats = [s for s in stats if s.games_played >= min_games]

        return stats

    except Exception as e:
        raise RuntimeError(f"Failed to fetch champion tournament stats: {str(e)}")


def get_champion_stats_by_name(
    champion: str,
    tournament: str,
) -> Optional[ChampionTournamentStats]:
    """Returns statistics for a specific champion in a tournament.

    Args:
        champion: Champion name
        tournament: Tournament overview page

    Returns:
        ChampionTournamentStats object if found, None otherwise

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_champion_tournament_stats(tournament=tournament, champion=champion)
    return stats[0] if stats else None


def get_most_picked_champions(
    tournament: str,
    limit: int = 10,
) -> List[ChampionTournamentStats]:
    """Returns champions sorted by pick rate.

    Args:
        tournament: Tournament overview page
        limit: Maximum number of champions to return

    Returns:
        A list of ChampionTournamentStats sorted by games_played descending

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_champion_tournament_stats(tournament=tournament)
    stats.sort(key=lambda x: x.games_played, reverse=True)
    return stats[:limit]


def get_most_banned_champions(
    tournament: str,
    limit: int = 10,
) -> List[ChampionTournamentStats]:
    """Returns champions sorted by ban rate.

    Args:
        tournament: Tournament overview page
        limit: Maximum number of champions to return

    Returns:
        A list of ChampionTournamentStats sorted by games_banned descending

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_champion_tournament_stats(tournament=tournament)
    stats.sort(key=lambda x: x.games_banned, reverse=True)
    return stats[:limit]


def get_highest_winrate_champions(
    tournament: str,
    min_games: int = 5,
    limit: int = 10,
) -> List[ChampionTournamentStats]:
    """Returns champions sorted by win rate.

    Args:
        tournament: Tournament overview page
        min_games: Minimum games played to include (default: 5)
        limit: Maximum number of champions to return

    Returns:
        A list of ChampionTournamentStats sorted by win_rate descending

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_champion_tournament_stats(tournament=tournament, min_games=min_games)
    stats.sort(key=lambda x: x.win_rate or 0, reverse=True)
    return stats[:limit]


def get_player_champion_stats(
    player: str,
    tournament: str = None,
    champion: str = None,
) -> List[PlayerChampionStats]:
    """Returns a player's champion statistics.

    Args:
        player: Player name/link
        tournament: Optional tournament to filter by
        champion: Optional champion to filter by

    Returns:
        A list of PlayerChampionStats objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = [QueryBuilder.build_like_condition("ScoreboardPlayers", "Link", player)]

        if tournament:
            where_conditions.append(
                QueryBuilder.build_where("ScoreboardPlayers", {"OverviewPage": tournament})
            )

        if champion:
            where_conditions.append(
                QueryBuilder.build_where("ScoreboardPlayers", {"Champion": champion})
            )

        data = leaguepedia.query(
            tables="ScoreboardPlayers",
            fields="Link,Champion,PlayerWin,Kills,Deaths,Assists,CS,Gold,DamageToChampions,OverviewPage",
            where=" AND ".join(where_conditions),
        )

        return _aggregate_player_champion_stats(data, tournament)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch player champion stats: {str(e)}")


def get_player_champion_pool(
    player: str,
    tournament: str = None,
    min_games: int = 1,
) -> List[PlayerChampionStats]:
    """Returns all champions a player has played.

    Args:
        player: Player name/link
        tournament: Optional tournament to filter by
        min_games: Minimum games on a champion to include (default: 1)

    Returns:
        A list of PlayerChampionStats sorted by games_played descending

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_player_champion_stats(player=player, tournament=tournament)

    if min_games > 1:
        stats = [s for s in stats if s.games_played >= min_games]

    stats.sort(key=lambda x: x.games_played, reverse=True)
    return stats


def get_player_signature_champions(
    player: str,
    tournament: str = None,
    min_games: int = 3,
    min_winrate: float = 60.0,
) -> List[PlayerChampionStats]:
    """Returns a player's signature champions (high games + high winrate).

    Args:
        player: Player name/link
        tournament: Optional tournament to filter by
        min_games: Minimum games played on champion (default: 3)
        min_winrate: Minimum win rate percentage (default: 60.0)

    Returns:
        A list of PlayerChampionStats for signature champions

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    stats = get_player_champion_stats(player=player, tournament=tournament)

    signature = [
        s for s in stats
        if s.games_played >= min_games and (s.win_rate or 0) >= min_winrate
    ]

    signature.sort(key=lambda x: (x.games_played, x.win_rate or 0), reverse=True)
    return signature
