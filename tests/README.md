# Unit Tests for Workshop Watcher

## What Are These Tests?

These tests automatically verify that your code works correctly. They check:
- ✅ Functions return the right values
- ✅ Edge cases are handled properly
- ✅ Invalid inputs are rejected
- ✅ Database operations work correctly

## Zero External Dependencies! 🎉

All tests use Python's built-in `unittest` module - **no pip install required!**

## Running Tests

### Run All Tests

```bash
# From the project root directory
python -m unittest discover tests -v
```

### Run Specific Test Files

```bash
python -m unittest tests.test_helpers -v      # Test helper functions
python -m unittest tests.test_validators -v   # Test validators
python -m unittest tests.test_db -v           # Test database functions
```

### Run Quick Demo (No Dependencies)

```bash
python tests/simple_test_demo.py
```

## Understanding Test Output

### ✅ Passing Test
```
tests/test_helpers.py::TestChunkList::test_basic_chunking PASSED
```
This means the test ran successfully!

### ❌ Failing Test
```
tests/test_helpers.py::TestChunkList::test_basic_chunking FAILED
AssertionError: assert [[1, 2], [3, 4]] == [[1, 2], [3]]
```
This shows what went wrong - the function returned the wrong value.

## Test Organization

### test_helpers.py
Tests for `utils/helpers.py`:
- `get_current_timestamp()` - Returns valid Unix timestamp
- `chunk_list()` - Splits lists correctly
- `create_empty_mod_record()` - Creates valid empty records

### test_validators.py
Tests for `utils/validators.py`:
- `validate_steam_api_key()` - Validates Steam API keys
- `validate_discord_webhook()` - Validates Discord webhooks
- `validate_workshop_id()` - Validates workshop IDs
- `validate_role_id()` - Validates Discord role IDs

### test_db.py
Tests for `db/db.py`:
- `connect_db()` - Database connection and schema
- `upsert_mod()` - Insert and update mods
- `get_last_update_time()` - Retrieve update times
- `get_mod_by_id()` - Retrieve full mod data
- `get_cached_steam_users()` - Retrieve cached users

## How Tests Work

### Example: Simple Test

```python
def test_chunk_list():
    # 1. Set up test data
    items = [1, 2, 3, 4, 5]
    
    # 2. Run the function
    result = list(chunk_list(items, 2))
    
    # 3. Check if it's correct
    assert result == [[1, 2], [3, 4], [5]]
    # ✅ Test passes if True
    # ❌ Test fails if False
```

### Example: Database Test with Fixture

```python
@pytest.fixture
def temp_db(tmp_path):
    """Creates a temporary database for testing."""
    db_path = tmp_path / "test.db"
    conn = connect_db(str(db_path))
    yield conn  # Test runs here
    conn.close()  # Cleanup

def test_insert_mod(temp_db):
    """Test uses the temporary database."""
    mod_data = {"id": 123, "title": "Test"}
    upsert_mod(temp_db, mod_data)
    
    result = get_mod_by_id(temp_db, 123)
    assert result["title"] == "Test"
```

**Fixtures** are reusable test components that set up and clean up test data.

## Writing Your Own Tests

### 1. Name Pattern
- File: `test_<module>.py`
- Class: `TestFunctionName`
- Function: `test_what_it_checks`

### 2. Basic Structure
```python
def test_something():
    # Arrange - set up test data
    input_data = [1, 2, 3]
    
    # Act - call the function
    result = my_function(input_data)
    
    # Assert - check result
    assert result == expected_value
```

### 3. Test Multiple Cases
```python
class TestMyFunction:
    def test_normal_case(self):
        assert my_function(5) == 10
    
    def test_edge_case_zero(self):
        assert my_function(0) == 0
    
    def test_edge_case_negative(self):
        assert my_function(-5) == -10
```

## Common Assertions

```python
# Equality
assert result == expected

# Truth/False
assert condition is True
assert condition is False

# None
assert value is None
assert value is not None

# Type checking
assert isinstance(result, int)
assert isinstance(result, dict)

# Membership
assert item in list_of_items
assert "key" in dictionary

# Comparisons
assert x > 5
assert x <= 10
```

## Running Tests in CI/CD

Add to your GitHub Actions workflow:
```yaml
- name: Run tests
  run: |
    pip install pytest
    pytest tests/ -v
```

## Test Coverage

To see which code is tested:
```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing
```

This shows:
- Which lines are tested ✅
- Which lines are NOT tested ❌
- Overall coverage percentage

## Benefits of Tests

1. **Catch Bugs Early** - Find problems before deploying
2. **Safe Refactoring** - Change code confidently
3. **Documentation** - Tests show how code should be used
4. **Confidence** - Know your code works

## Next Steps

1. Run the existing tests: `pytest tests/ -v`
2. Add tests as you add features
3. Aim for 70%+ code coverage
4. Run tests before committing code

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
Install pytest: `pip install pytest`

### "No tests ran"
Make sure:
- Files are named `test_*.py`
- Functions are named `test_*`
- You're in the project root directory

### "Import errors"
Add parent directory to path in test file:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```
