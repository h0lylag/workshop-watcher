"""
Tests for utility helper functions.

Run with: pytest tests/test_helpers.py -v
"""
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import get_current_timestamp, chunk_list, create_empty_mod_record


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp()."""
    
    def test_returns_integer(self):
        """Should return an integer timestamp."""
        result = get_current_timestamp()
        assert isinstance(result, int)
    
    def test_returns_reasonable_value(self):
        """Should return a timestamp after 2020."""
        result = get_current_timestamp()
        # 1577836800 = January 1, 2020
        assert result > 1577836800
    
    def test_returns_current_time(self):
        """Should return approximately current time."""
        before = int(time.time())
        result = get_current_timestamp()
        after = int(time.time())
        
        # Should be within a few seconds
        assert before <= result <= after + 1


class TestChunkList:
    """Tests for chunk_list()."""
    
    def test_basic_chunking(self):
        """Should split list into chunks of specified size."""
        items = [1, 2, 3, 4, 5]
        result = list(chunk_list(items, 2))
        
        assert result == [[1, 2], [3, 4], [5]]
    
    def test_even_chunks(self):
        """Should handle lists that divide evenly."""
        items = [1, 2, 3, 4]
        result = list(chunk_list(items, 2))
        
        assert result == [[1, 2], [3, 4]]
    
    def test_empty_list(self):
        """Should handle empty list."""
        result = list(chunk_list([], 2))
        assert result == []
    
    def test_chunk_size_larger_than_list(self):
        """Should return single chunk if size is larger than list."""
        items = [1, 2, 3]
        result = list(chunk_list(items, 10))
        
        assert result == [[1, 2, 3]]
    
    def test_chunk_size_one(self):
        """Should create individual chunks for size 1."""
        items = [1, 2, 3]
        result = list(chunk_list(items, 1))
        
        assert result == [[1], [2], [3]]


class TestCreateEmptyModRecord:
    """Tests for create_empty_mod_record()."""
    
    def test_has_required_id(self):
        """Should include the mod ID."""
        result = create_empty_mod_record(12345)
        assert result["id"] == 12345
    
    def test_has_last_checked_timestamp(self):
        """Should include last_checked timestamp."""
        result = create_empty_mod_record(123)
        assert "last_checked" in result
        assert isinstance(result["last_checked"], int)
    
    def test_other_fields_are_none(self):
        """Should set all other fields to None."""
        result = create_empty_mod_record(123)
        
        # These should all be None
        assert result["title"] is None
        assert result["author_id"] is None
        assert result["author_name"] is None
        assert result["file_size"] is None
        assert result["time_created"] is None
        assert result["time_updated"] is None
    
    def test_timestamp_is_recent(self):
        """Should set last_checked to current time."""
        before = int(time.time())
        result = create_empty_mod_record(123)
        after = int(time.time())
        
        assert before <= result["last_checked"] <= after + 1


# You can run these tests with:
# pytest tests/test_helpers.py -v
#
# Expected output:
# tests/test_helpers.py::TestGetCurrentTimestamp::test_returns_integer PASSED
# tests/test_helpers.py::TestGetCurrentTimestamp::test_returns_reasonable_value PASSED
# tests/test_helpers.py::TestChunkList::test_basic_chunking PASSED
# ... etc
