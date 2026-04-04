# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-04

### Added
- Explicit typed parameters replacing `**kwargs` in all public APIs for better discoverability
- `test_query_builder.py` with 36 tests for SQL escaping and query construction
- `test_player_parser.py` with 40 tests for player data parsing
- Enums for valid parameter values: `ItemTier`, `ChampionResource`, `ChampionAttribute`, `Role`
- `__version__` attribute exported from package
- `py.typed` marker for type checker support
- PyPI release checklist in CLAUDE.md

### Fixed
- SQL injection vulnerabilities in all parsers (migrated to QueryBuilder)
- UTC datetime standardization across all modules
- Removed duplicate `attack_damage` field from Item dataclass

### Changed
- `get_tournament_rosters()` now returns typed `TournamentRoster` dataclass instead of `Dict`
- All parser functions now use explicit parameters instead of `**kwargs`

## [0.1.1] - 2024-12-01

### Added
- ScoreboardPlayers parser with match statistics and performance analytics
- Contracts parser for player contract tracking
- Standings parser for tournament rankings
- Champions parser with attribute and resource filtering
- Items parser with stat-based searching
- Roster changes parser for transfer tracking
- Player parser for comprehensive player information
- Tournament roster parser

### Changed
- Enhanced fork of original leaguepedia_parser with extended functionality

## [0.1.0] - Initial Fork

### Added
- Fork of [mrtolkien/leaguepedia_parser](https://github.com/mrtolkien/leaguepedia_parser)
- Basic game, tournament, team, and player queries
- Team asset retrieval (logos, thumbnails)
