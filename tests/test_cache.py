"""Tests for cache functionality."""

import pytest

import meeps as mp


class TestCacheExports:
    """Test that cache functions are properly exportable."""

    @pytest.mark.unit
    def test_cache_functions_exportable(self):
        """Test that all cache functions are available in the main module."""
        expected_functions = [
            "enable_cache",
            "disable_cache",
            "clear_cache",
            "get_cache_info",
            "is_cache_enabled",
        ]

        for func_name in expected_functions:
            assert hasattr(mp, func_name), f"Function {func_name} is not importable"


class TestCacheWithoutRequestsCache:
    """Test cache functions behave gracefully without requests-cache."""

    @pytest.mark.unit
    def test_is_cache_enabled_returns_false_without_lib(self):
        """Test is_cache_enabled returns False when no cache is configured."""
        # This works regardless of requests-cache being installed
        # as long as enable_cache() hasn't been called
        mp.disable_cache()  # Ensure cache is disabled
        assert mp.is_cache_enabled() is False

    @pytest.mark.unit
    def test_disable_cache_no_error_without_cache(self):
        """Test disable_cache doesn't error when cache not enabled."""
        mp.disable_cache()  # Should not raise

    @pytest.mark.unit
    def test_clear_cache_no_error_without_cache(self):
        """Test clear_cache doesn't error when cache not enabled."""
        mp.clear_cache()  # Should not raise


class TestCacheWithRequestsCache:
    """Test cache functions with requests-cache installed."""

    @pytest.fixture(autouse=True)
    def cleanup_cache(self):
        """Ensure cache is disabled after each test."""
        yield
        mp.disable_cache()

    @pytest.mark.unit
    def test_enable_cache_memory_backend(self):
        """Test enabling cache with memory backend."""
        mp.enable_cache(backend="memory", expire_after=60)

        assert mp.is_cache_enabled() is True

        info = mp.get_cache_info()
        assert info is not None
        assert info["expire_after"] == 60
        assert "Cache" in info["backend"]

    @pytest.mark.unit
    def test_enable_cache_default_settings(self):
        """Test enabling cache with default settings."""
        mp.enable_cache(backend="memory")

        assert mp.is_cache_enabled() is True

        info = mp.get_cache_info()
        assert info is not None
        assert info["expire_after"] == 3600  # Default 1 hour

    @pytest.mark.unit
    def test_disable_cache(self):
        """Test disabling cache."""
        mp.enable_cache(backend="memory")
        assert mp.is_cache_enabled() is True

        mp.disable_cache()
        assert mp.is_cache_enabled() is False

    @pytest.mark.unit
    def test_clear_cache(self):
        """Test clearing cache."""
        mp.enable_cache(backend="memory")
        mp.clear_cache()  # Should not raise

        info = mp.get_cache_info()
        assert info["size"] == 0

    @pytest.mark.unit
    def test_get_cache_info_when_disabled(self):
        """Test get_cache_info returns None when disabled."""
        mp.disable_cache()
        assert mp.get_cache_info() is None

    @pytest.mark.unit
    def test_cache_with_no_expiration(self):
        """Test cache with no expiration."""
        mp.enable_cache(backend="memory", expire_after=None)

        info = mp.get_cache_info()
        assert info["expire_after"] is None


if __name__ == "__main__":
    pytest.main([__file__])
