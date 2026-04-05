__version__ = "0.2.0"

from meeps.parsers.game_parser import (
    get_regions,
    get_tournaments,
    get_games,
    get_game_details,
)
from meeps.parsers.team_parser import (
    get_active_players,
    get_team_logo,
    get_long_team_name_from_trigram,
    get_team_thumbnail,
    get_all_team_assets,
    TeamAssets,
    TeamPlayer,
)
from meeps.parsers.player_parser import (
    get_player_by_name,
    PlayerInfo,
    PlayerStatus,
)

# Tournament roster information
from meeps.parsers.tournament_roster_parser import (
    get_tournament_rosters,
    TournamentRoster,
)

# Standings
from meeps.parsers.standings_parser import (
    get_standings,
    get_tournament_standings,
    get_team_standings,
    get_standings_by_overview_page,
    Standing,
)

# Champions and items data
from meeps.parsers.champions_parser import (
    get_champions,
    get_champion_by_name,
    get_champions_by_attributes,
    get_champions_by_resource,
    get_melee_champions,
    get_ranged_champions,
    Champion,
)
from meeps.parsers.items_parser import (
    get_items,
    get_item_by_name,
    get_items_by_tier,
    get_ad_items,
    get_ap_items,
    get_tank_items,
    get_health_items,
    get_mana_items,
    search_items_by_stat,
    Item,
)

# Enhanced roster tracking
from meeps.parsers.roster_changes_parser import (
    get_roster_changes,
    get_team_roster_changes,
    get_player_roster_changes,
    get_recent_roster_changes,
    get_roster_additions,
    get_roster_removals,
    get_retirements,
    RosterChange,
    RosterAction,
)

# Enums for valid values
from meeps.enums import (
    ItemTier,
    ChampionResource,
    ChampionAttribute,
    Role,
)

# Contracts
from meeps.parsers.contracts_parser import (
    get_contracts,
    get_player_contracts,
    get_team_contracts,
    get_active_contracts,
    get_expiring_contracts,
    get_contract_removals,
    Contract,
)

# ScoreboardPlayers - Match Performance Statistics
from meeps.parsers.scoreboard_players_parser import (
    get_scoreboard_players,
    get_player_match_history,
    get_team_match_performance,
    get_champion_performance_stats,
    get_game_scoreboard,
    get_tournament_mvp_candidates,
    get_role_performance_comparison,
    ScoreboardPlayer,
)

# Teams - Team Metadata
from meeps.parsers.teams_parser import (
    get_teams,
    get_team_by_name,
    get_team_by_short,
    get_teams_by_region,
    get_active_teams,
    get_disbanded_teams,
    search_teams,
    Team,
)

# MatchSchedule - Match Schedules and Results
from meeps.parsers.match_schedule_parser import (
    get_match_schedule,
    get_upcoming_matches,
    get_recent_results,
    get_team_schedule,
    get_tournament_schedule,
    get_today_matches,
    get_head_to_head,
    MatchSchedule,
)

# MatchScheduleGame - Individual Game Data
from meeps.parsers.match_schedule_game_parser import (
    get_match_schedule_games,
    get_games_by_match,
    get_games_by_tournament,
    get_mvp_games,
    get_remakes,
    MatchScheduleGame,
)

# TournamentResults - Tournament Placements and Prizes
from meeps.parsers.tournament_results_parser import (
    get_tournament_results,
    get_team_tournament_history,
    get_tournament_placements,
    get_tournament_winners,
    get_prize_earnings,
    TournamentResult,
)

# Tenures - Player Team History
from meeps.parsers.tenures_parser import (
    get_tenures,
    get_player_tenures,
    get_team_tenures,
    get_current_roster_tenures,
    get_longest_tenures,
    Tenure,
)

# VODs - Game VOD Information
from meeps.parsers.vods_parser import (
    get_vods,
    get_vod_by_game_id,
    get_vods_by_match,
    get_team_vods,
    get_tournament_vods,
    GameVod,
)

# Patches - Patch Metadata and History
from meeps.parsers.patches_parser import (
    get_patches,
    get_patch_by_version,
    get_patches_in_date_range,
    get_latest_patch,
    get_patches_by_major_version,
    Patch,
)

# ChampionStats - Tournament and Player Champion Statistics
from meeps.parsers.champion_stats_parser import (
    get_champion_tournament_stats,
    get_champion_stats_by_name,
    get_most_picked_champions,
    get_most_banned_champions,
    get_highest_winrate_champions,
    get_player_champion_stats,
    get_player_champion_pool,
    get_player_signature_champions,
    ChampionTournamentStats,
    PlayerChampionStats,
)
