# Claude Code Documentation

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

## Project Structure

```
meeps/
├── __init__.py                    # Main package exports
├── logger.py                      # Logging configuration
├── site/
│   └── leaguepedia.py            # Leaguepedia site connection
├── parsers/                       # Data extraction layer
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
    ├── test_team.py              # Team parser tests
    └── test_extensions.py        # Legacy test file (deprecated)
```

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
   # ✅ Correct
   from .conftest import TestConstants, assert_valid_dataclass_instance
   
   # ❌ Incorrect - causes ModuleNotFoundError
   from conftest import TestConstants, assert_valid_dataclass_instance
   ```

3. **Missing Test Dependencies**: Ensure pytest fixtures are properly imported:
   ```python
   # Required imports for test files
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

## Recent Fixes Applied

### Security & Reliability Improvements
1. **SQL Injection Prevention**: Escaped user inputs in query building (`game_parser.py:64-77`)
2. **Logger Fix**: Corrected logger name from `"leaguepedia_&arser"` to `"leaguepedia_parser"` (`logger.py:3`)
3. **Exception Handling**: Improved error handling with specific exception types and cycle detection (`team_parser.py:215-228`)
4. **Code Cleanup**: Removed test file `blabla.py`

### Extended Functionality Additions
1. **New Parser Modules**: Added comprehensive parsers for standings, champions, items, and roster changes
2. **Field Mapping Corrections**: Fixed field mappings for Cargo table schemas based on actual Leaguepedia API structure
3. **Enhanced Data Models**: Added computed properties and validation to dataclasses
4. **Comprehensive API Coverage**: Extended functionality to cover more Leaguepedia data tables

### Test Suite Improvements
1. **Test Restructuring**: Migrated from monolithic `test_extensions.py` to modular, focused test files
2. **Centralized Test Configuration**: Created `conftest.py` with shared fixtures and mock data factories
3. **Import Resolution**: Fixed relative import issues in pytest test files
4. **Test Categorization**: Implemented pytest markers (unit, integration, slow, api) for better test organization
5. **Mock Data Management**: Centralized mock data creation for consistency across tests
6. **Error Handling Tests**: Added comprehensive error handling and edge case coverage
7. **Integration Testing**: Created cross-module integration tests for real-world usage scenarios

### Development Best Practices
- Always use Poetry for dependency management
- Run tests before committing changes
- Follow the existing code style and patterns
- Add proper error handling for new API calls
- Use relative imports in test files (`from .conftest import`)
- Centralize mock data in conftest.py for reusability
- Implement proper test categorization with pytest markers
- Reset mocks between tests to ensure isolation

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
# Get all standings
standings = lp.get_standings()

# Get standings for specific tournament
tournament_standings = lp.get_tournament_standings("LCK/2024 Season/Summer Season")

# Get standings for specific team
team_standings = lp.get_team_standings("T1")

# Access computed properties
for standing in standings:
    print(f"{standing.team}: {standing.series_win_rate}% win rate")
    print(f"Total games: {standing.total_games_played}")
```

#### Champions Data
```python
# Get all champions
champions = lp.get_champions()

# Get specific champion
jinx = lp.get_champion_by_name("Jinx")

# Filter by attributes
marksmen = lp.get_champions_by_attributes("Marksman")
fighters = lp.get_champions_by_attributes("Fighter")

# Filter by resource type
mana_champs = lp.get_champions_by_resource("Mana")
flow_champs = lp.get_champions_by_resource("Flow")

# Get by range type
melee_champions = lp.get_melee_champions()
ranged_champions = lp.get_ranged_champions()

# Access champion properties
for champion in champions:
    print(f"{champion.name}: {'Ranged' if champion.is_ranged else 'Melee'}")
    print(f"Attributes: {champion.attributes_list}")
```

#### Items Data
```python
# Get all items
items = lp.get_items()

# Get specific item
infinity_edge = lp.get_item_by_name("Infinity Edge")

# Filter by item tier
legendary_items = lp.get_items_by_tier("Legendary")
mythic_items = lp.get_items_by_tier("Mythic")

# Filter by stats
ad_items = lp.get_ad_items()
ap_items = lp.get_ap_items()
tank_items = lp.get_tank_items()
health_items = lp.get_health_items()
mana_items = lp.get_mana_items()

# Search by custom stats
high_ad_items = lp.search_items_by_stat("ad", min_value=50)

# Access item properties
for item in ad_items:
    print(f"{item.name}: {item.ad} AD, {item.total_cost} gold")
    print(f"Provides AD: {item.provides_ad}")
```

#### Roster Changes Tracking
```python
# Get all roster changes
changes = lp.get_roster_changes()

# Get changes for specific team
t1_changes = lp.get_team_roster_changes("T1")

# Get changes for specific player
faker_changes = lp.get_player_roster_changes("Faker")

# Get recent changes (last 30 days)
recent_changes = lp.get_recent_roster_changes(days=30)

# Filter by action type
additions = lp.get_roster_additions()
removals = lp.get_roster_removals()
retirements = lp.get_retirements()

# Date range filtering
changes_2024 = lp.get_roster_changes(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Access change properties
for change in recent_changes:
    print(f"{change.date}: {change.team} {change.action} {change.player} ({change.role})")
    print(f"Retirement: {change.is_retirement}")
```

### Error Handling
```python
# Basic error handling
try:
    players = lp.get_active_players("NonexistentTeam")
except ValueError as e:
    print(f"Team not found: {e}")
except RuntimeError as e:
    print(f"API error: {e}")

# Extended functionality error handling
try:
    # All new parsers follow consistent error handling
    standings = lp.get_standings(overview_page="Invalid Tournament")
    champions = lp.get_champions(resource="InvalidResource")
    items = lp.get_items_by_tier("InvalidTier")
    changes = lp.get_roster_changes(team="NonexistentTeam")
except RuntimeError as e:
    print(f"API error: {e}")  # All modules wrap exceptions in RuntimeError
except Exception as e:
    print(f"Unexpected error: {e}")

# Handling empty results
results = lp.get_champion_by_name("NonexistentChampion")
if results is None:
    print("Champion not found")

results = lp.get_standings(team="NonexistentTeam")
if not results:  # Empty list
    print("No standings found")
```

## Testing Best Practices

### Test Structure
Follow the modular test structure:
- **conftest.py**: Shared fixtures, mock data factories, helper functions
- **test_[module].py**: Focused tests for each parser module
- **test_integration_*.py**: Cross-module integration tests

### Test Categories
Use pytest markers to categorize tests:
```python
@pytest.mark.unit
def test_dataclass_properties():
    # Fast unit tests for individual components
    pass

@pytest.mark.integration  
def test_api_integration():
    # Integration tests with mocked APIs
    pass

@pytest.mark.slow
def test_large_dataset():
    # Tests that may take longer to run
    pass

@pytest.mark.api
def test_real_api():
    # Tests that interact with external APIs
    pass
```

### Mock Data Management
Use centralized mock data from conftest.py:
```python
def test_function(self, mock_leaguepedia_query, standings_mock_data):
    mock_leaguepedia_query.return_value = standings_mock_data
    # Test implementation
```

### Running Tests
```bash
# Run all tests
poetry run python -m pytest tests/ -v

# Run specific test categories
poetry run python -m pytest tests/ -m unit -v
poetry run python -m pytest tests/ -m integration -v

# Run specific test file
poetry run python -m pytest tests/test_standings.py -v

# Run with coverage
poetry run python -m pytest tests/ --cov=meeps
```