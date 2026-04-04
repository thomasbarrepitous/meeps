# Claude Code Documentation

## Architecture Overview

### Data Flow
```
Leaguepedia API → Parsers → [Transmuters] → Data Models → User
```

### Module Responsibilities

| Layer | Purpose | Pattern |
|-------|---------|---------|
| `site/` | API connection, query execution | Singleton site instance |
| `parsers/` | Data extraction from Cargo tables | Returns typed dataclasses |
| `transmuters/` | Transform raw API data to `lol_dto` format | Field mapping dictionaries |
| `__init__.py` | Public API surface | Convenience wrappers |

### Data Model Patterns

The codebase uses two distinct patterns for data models:

1. **Internal Dataclasses** (`parsers/*.py`): Used by newer modules (standings, champions, items, roster_changes). Defined inline with computed properties.

2. **lol_dto Models** (`transmuters/*.py`): Used by game/tournament data. External package dependency with stricter schemas.

---

## Key Improvement Areas

### P0 - Security: SQL Injection Vulnerabilities

Four parsers use direct string concatenation instead of the `QueryBuilder` class, creating SQL injection vectors.

| File | Lines | Issue |
|------|-------|-------|
| `tournament_roster_parser.py` | 24-34 | Direct string concatenation for WHERE clause |
| `game_parser.py` | 101, 147, 165 | Unescaped f-strings in query conditions |
| `player_parser.py` | 279 | Direct string interpolation |
| `team_parser.py` | 70-76 | Direct concatenation in query building |

**Fix**: Migrate all queries to use `QueryBuilder.add_where()` which handles escaping.

```python
# Bad - vulnerable
where = f"Team = '{team_name}'"

# Good - uses QueryBuilder escaping
builder = QueryBuilder()
builder.add_where("Team", team_name)
```

---

### P1 - Public API Quality

#### Untyped Return Values
- `get_tournament_rosters()` returns `List[Dict]` instead of typed dataclass
- Users have no IDE autocomplete or type checking for roster data

#### Missing Enums for Valid Values
Users must guess valid string values for:
- Item tiers: "Starter", "Basic", "Epic", "Legendary", "Mythic"
- Champion resources: "Mana", "Energy", "Flow", "Fury", etc.
- Player roles: "Top", "Jungle", "Mid", "Bot", "Support"

**Fix**: Add enums in a new `meeps/enums.py`:
```python
class ItemTier(str, Enum):
    STARTER = "Starter"
    BASIC = "Basic"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    MYTHIC = "Mythic"
```

#### Undocumented **kwargs
Functions like `get_standings(**kwargs)` accept arbitrary parameters without documenting valid options. Users can't discover what filters are available without reading source code.

**Fix**: Replace `**kwargs` with explicit parameters or TypedDict.

---

### P2 - Data Model Consistency

#### Duplicate Fields in items_parser.py
The `Item` dataclass has both `ad` and `attack_damage` fields that represent the same stat. This creates confusion about which to use.

**Fix**: Remove `attack_damage`, keep `ad` for consistency with game terminology.

#### Mixed DateTime Handling
Some modules return naive datetimes, others return UTC-aware. This causes comparison bugs.

| Module | Behavior |
|--------|----------|
| `roster_changes_parser.py` | Naive datetime |
| `game_parser.py` | UTC-aware datetime |

**Fix**: Standardize on UTC-aware datetimes throughout.

#### Mixed Model Patterns
Game data uses external `lol_dto` package while newer parsers define inline dataclasses. Consider consolidating to one approach for consistency.

---

### P3 - Test Coverage Gaps

~23% of code lines lack test coverage. Priority modules:

| Module | Lines | Tests | Notes |
|--------|-------|-------|-------|
| `player_parser.py` | 349 | 0 | Core module, completely untested |
| `transmuters/*` | ~536 | 0 | All transformation logic untested |
| `query_builder.py` | 92 | 0 | Critical for SQL injection fixes |
| `tournament_roster_parser.py` | 45 | 0 | Returns untyped data |

---

## Technical Debt Checklist

### Security
- [x] `tournament_roster_parser.py:24-34` - Migrate to QueryBuilder
- [x] `game_parser.py:101` - Escape tournament parameter
- [x] `game_parser.py:147` - Escape game_id parameter
- [x] `game_parser.py:165` - Escape team parameter
- [x] `player_parser.py:279` - Escape player_name parameter
- [x] `team_parser.py:70-76` - Migrate to QueryBuilder

### API Quality
- [x] `tournament_roster_parser.py` - Return typed dataclass instead of Dict
- [x] Create `meeps/enums.py` with ItemTier, ChampionResource, Role enums
- [x] `standings_parser.py` - Replace **kwargs with explicit parameters
- [x] `champions_parser.py` - Replace **kwargs with explicit parameters
- [x] `items_parser.py` - Replace **kwargs with explicit parameters
- [x] `roster_changes_parser.py` - Replace **kwargs with explicit parameters
- [x] `game_parser.py` - Replace **kwargs with explicit parameters
- [x] `team_parser.py` - Replace **kwargs with explicit parameters
- [x] `contracts_parser.py` - Replace **kwargs with explicit parameters

### Data Models
- [x] `items_parser.py` - Remove duplicate `attack_damage` field
- [x] `roster_changes_parser.py` - Use UTC-aware datetimes
- [ ] Document which model pattern to use for new code

### Test Coverage
- [x] Add `test_player_parser.py`
- [x] Add `test_query_builder.py`
- [ ] Add `test_tournament_roster_parser.py`
- [ ] Add `tests/transmuters/` test directory
- [ ] Add `test_transmuters_game.py`
- [ ] Add `test_transmuters_picks_bans.py`

---

## Code Style Addendum

### SQL Query Construction
Always use `QueryBuilder` for constructing queries. Never use f-strings or string concatenation with user input.

```python
# Required pattern
from meeps.parsers.query_builder import QueryBuilder

builder = QueryBuilder()
builder.set_table("Players")
builder.add_field("Name")
builder.add_where("Team", team_name)  # Handles escaping
query = builder.build()
```

### DateTime Handling
Always use UTC-aware datetimes:

```python
from datetime import datetime, timezone

# Good
now = datetime.now(timezone.utc)

# Bad
now = datetime.now()
```

### Return Types
Always return typed dataclasses from parser functions, never raw dicts:

```python
# Good
def get_standings() -> List[Standing]:
    ...

# Bad
def get_tournament_rosters() -> List[Dict]:
    ...
```

---

## Development Commands

### Testing
```bash
# Install dependencies
poetry install

# Run all tests
poetry run python -m pytest tests/ -v

# Test specific modules
poetry run python -c "import meeps; print('Import successful')"
```

### Code Quality
```bash
# Format code with black
poetry run black meeps/

# Check code style
poetry run black --check meeps/
```

### Package Management
```bash
# Install new dependency
poetry add <package-name>

# Install development dependency
poetry add --group dev <package-name>

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree
```

---

## Project Structure

```
meeps/
├── __init__.py                    # Main package exports
├── logger.py                      # Logging configuration
├── site/
│   └── leaguepedia.py            # Leaguepedia site connection
├── parsers/                       # Data extraction layer
│   ├── query_builder.py          # SQL query construction (use for all queries)
│   ├── game_parser.py            # Game and tournament data
│   ├── team_parser.py            # Team data and assets
│   ├── player_parser.py          # Player information
│   ├── tournament_roster_parser.py # Tournament rosters
│   ├── standings_parser.py       # League standings and rankings
│   ├── champions_parser.py       # Champion information and stats
│   ├── items_parser.py           # Item data and properties
│   └── roster_changes_parser.py  # Team roster changes tracking
├── transmuters/                   # Data transformation layer
│   ├── field_names.py            # Field mapping constants
│   ├── game.py                   # Game data transformation
│   ├── game_players.py           # Player data transformation
│   ├── picks_bans.py             # Draft data transformation
│   └── tournament.py             # Tournament data transformation
└── tests/                         # Test suite
    ├── conftest.py               # Shared test configuration and fixtures
    ├── test_standings.py         # Standings functionality tests
    ├── test_champions.py         # Champions functionality tests
    ├── test_items.py             # Items functionality tests
    ├── test_roster_changes.py    # Roster changes functionality tests
    ├── test_integration_extensions.py # Cross-module integration tests
    ├── test_game.py              # Game parser tests
    └── test_team.py              # Team parser tests
```

---

## Common Issues & Solutions

### Import Errors
If you encounter `ModuleNotFoundError`, ensure you're using the Poetry environment:
```bash
poetry run python your_script.py
```

### Test Import Errors
Common test import issues and solutions:

1. **Package Name Mismatch**: Tests expect the package to be importable as `leaguepedia_parser`, but the actual package name is `meeps`. Update test imports accordingly.

2. **Relative Import Errors**: When restructuring test files, use relative imports for conftest.py:
   ```python
   # Correct
   from .conftest import TestConstants, assert_valid_dataclass_instance

   # Incorrect - causes ModuleNotFoundError
   from conftest import TestConstants, assert_valid_dataclass_instance
   ```

3. **Missing Test Dependencies**: Ensure pytest fixtures are properly imported:
   ```python
   import pytest
   from unittest.mock import Mock, patch
   from .conftest import TestConstants, TestDataFactory
   ```

### API Rate Limiting
The Leaguepedia API has rate limits. If you encounter issues:
1. Add delays between requests
2. Implement exponential backoff
3. Use the built-in pagination in `LeaguepediaSite.query()`

### Test Fixture and Mock Issues
When working with test mocks and fixtures:

1. **DateTime Mocking**: Use proper patching for datetime-dependent functions:
   ```python
   @patch('meeps.parsers.roster_changes_parser.datetime')
   def test_function(self, mock_datetime):
       mock_datetime.now.return_value = datetime(2023, 12, 15)
       mock_datetime.timedelta = timedelta  # Use real timedelta
   ```

2. **Mock Data Consistency**: Use centralized mock data from conftest.py:
   ```python
   def test_function(self, mock_leaguepedia_query, standings_mock_data):
       mock_leaguepedia_query.return_value = standings_mock_data
   ```

3. **Test Isolation**: Reset mocks between tests to avoid interference:
   ```python
   mock_leaguepedia_query.reset_mock()
   ```

---

## API Usage Examples

### Basic Usage
```python
import meeps as lp

# Get regions
regions = lp.get_regions()

# Get tournaments
tournaments = lp.get_tournaments("Korea", year=2020)

# Get games
games = lp.get_games("LCK/2020 Season/Spring Season")

# Get detailed game information
game_details = lp.get_game_details(games[0])

# Get team players
players = lp.get_active_players("T1")

# Get player information
player = lp.get_player_by_name("Faker")
```

### Extended Functionality

#### Standings and Rankings
```python
standings = lp.get_standings()
tournament_standings = lp.get_tournament_standings("LCK/2024 Season/Summer Season")
team_standings = lp.get_team_standings("T1")

for standing in standings:
    print(f"{standing.team}: {standing.series_win_rate}% win rate")
    print(f"Total games: {standing.total_games_played}")
```

#### Champions Data
```python
champions = lp.get_champions()
jinx = lp.get_champion_by_name("Jinx")
marksmen = lp.get_champions_by_attributes("Marksman")
mana_champs = lp.get_champions_by_resource("Mana")
melee_champions = lp.get_melee_champions()

for champion in champions:
    print(f"{champion.name}: {'Ranged' if champion.is_ranged else 'Melee'}")
```

#### Items Data
```python
items = lp.get_items()
infinity_edge = lp.get_item_by_name("Infinity Edge")
legendary_items = lp.get_items_by_tier("Legendary")
ad_items = lp.get_ad_items()
high_ad_items = lp.search_items_by_stat("ad", min_value=50)

for item in ad_items:
    print(f"{item.name}: {item.ad} AD, {item.total_cost} gold")
```

#### Roster Changes Tracking
```python
changes = lp.get_roster_changes()
t1_changes = lp.get_team_roster_changes("T1")
recent_changes = lp.get_recent_roster_changes(days=30)
additions = lp.get_roster_additions()

for change in recent_changes:
    print(f"{change.date}: {change.team} {change.action} {change.player}")
```

### Error Handling
```python
try:
    players = lp.get_active_players("NonexistentTeam")
except ValueError as e:
    print(f"Team not found: {e}")
except RuntimeError as e:
    print(f"API error: {e}")

# Handling empty results
results = lp.get_champion_by_name("NonexistentChampion")
if results is None:
    print("Champion not found")
```

---

## Testing Best Practices

### Test Structure
- **conftest.py**: Shared fixtures, mock data factories, helper functions
- **test_[module].py**: Focused tests for each parser module
- **test_integration_*.py**: Cross-module integration tests

### Test Categories
```python
@pytest.mark.unit
def test_dataclass_properties():
    pass

@pytest.mark.integration
def test_api_integration():
    pass

@pytest.mark.slow
def test_large_dataset():
    pass

@pytest.mark.api
def test_real_api():
    pass
```

### Running Tests

```bash
# Run fast tests only (default, recommended)
poetry run python -m pytest tests/ -v

# Run API integration tests (slow, requires network)
poetry run python -m pytest tests/ -m api -v

# Run ALL tests
poetry run python -m pytest tests/ -m "api or not api" -v

# Run with coverage
poetry run python -m pytest tests/ --cov=meeps -m "not api"
```

**Performance expectations:**
- Fast tests: ~210 tests, <10 seconds
- API tests: ~11 tests, 2-5 minutes
