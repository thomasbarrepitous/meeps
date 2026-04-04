# Lessons Learned

Patterns and corrections captured during development to help future sessions.

---

## SQL Query Construction

**Always use `QueryBuilder`** for constructing queries. Never use f-strings or string concatenation.

```python
# Correct
from meeps.parsers.query_builder import QueryBuilder

builder = QueryBuilder()
builder.set_table("Players")
builder.add_field("Name")
builder.add_where("Team", team_name)  # Handles escaping
query = builder.build()

# Wrong - SQL injection risk
where = f"Team = '{team_name}'"
```

---

## DateTime Handling

**Always use UTC-aware datetimes.** Naive datetimes cause comparison bugs across modules.

```python
from datetime import datetime, timezone

# Correct
now = datetime.now(timezone.utc)

# Wrong
now = datetime.now()
```

---

## Public API Design

### Explicit Parameters Over **kwargs

**Replace `**kwargs` with explicit typed parameters.** Users can't discover valid options without reading source code.

```python
# Correct - discoverable, type-checked
def get_standings(
    tournament: Optional[str] = None,
    team: Optional[str] = None,
    limit: int = 100
) -> List[Standing]:

# Wrong - opaque to users
def get_standings(**kwargs) -> List[Standing]:
```

### Typed Returns Over Dicts

**Return typed dataclasses, not raw dicts.** Enables IDE autocomplete and type checking.

```python
# Correct
def get_tournament_rosters() -> List[TournamentRoster]:

# Wrong
def get_tournament_rosters() -> List[Dict]:
```

---

## Test Patterns

### Mocking Leaguepedia Queries

Use the shared `mock_leaguepedia_query` fixture from conftest.py:

```python
def test_function(self, mock_leaguepedia_query, standings_mock_data):
    mock_leaguepedia_query.return_value = standings_mock_data
    result = get_standings()
    assert len(result) > 0
```

### DateTime Mocking

When mocking datetime-dependent functions, preserve real timedelta:

```python
@patch('meeps.parsers.roster_changes_parser.datetime')
def test_function(self, mock_datetime):
    mock_datetime.now.return_value = datetime(2023, 12, 15, tzinfo=timezone.utc)
    mock_datetime.timedelta = timedelta  # Use real timedelta
```

### Test Imports

Use relative imports for conftest in test files:

```python
# Correct
from .conftest import TestConstants, assert_valid_dataclass_instance

# Wrong - causes ModuleNotFoundError
from conftest import TestConstants
```

---

## Documentation Consistency

### Keep CLAUDE.md Current

When completing checklist items, update both:
1. The status table (change ❌/⚠️ to ✅)
2. The checklist items (change `[ ]` to `[x]`)

### Tournament Naming

Tournaments use the `OverviewPage` format: `{League}/{Year} Season/{Split}`

Examples:
- `LCK/2024 Season/Summer Season`
- `Worlds/2024 Season/Main Event`

Use `get_tournaments(region, year)` to discover valid names.

---

## Model Patterns

The codebase uses two patterns:

1. **Internal Dataclasses** (`parsers/*.py`): For newer modules. Define inline with `@dataclass` and computed `@property` methods.

2. **lol_dto Models** (`transmuters/*.py`): For game/tournament data. External package with stricter schemas.

**For new code:** Prefer internal dataclasses unless integrating with existing lol_dto consumers.

---

## Common Pitfalls

1. **Field availability**: Not all API fields are always populated. Check for `None` before using optional fields like `birthdate`, `contract`, `damage_to_champions`.

2. **Rate limiting**: Use `limit` parameter and filter by tournament. Unbounded queries fetch years of data.

3. **Package name**: The package is `meeps`, not `leaguepedia_parser`. Update imports accordingly.
