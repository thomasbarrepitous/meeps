"""Cache utilities for reducing API rate limit pressure.

This module provides a simple interface to enable HTTP-level caching
using requests-cache. Caching is transparent to all API calls.

Example:
    import meeps as mp

    # Enable caching with default settings (1 hour TTL, SQLite backend)
    mp.enable_cache()

    # First call hits the API
    standings = mp.get_tournament_standings("LCK/2024 Season/Summer Season")

    # Second call returns cached data instantly
    standings = mp.get_tournament_standings("LCK/2024 Season/Summer Season")

    # Clear cache when needed
    mp.clear_cache()

    # Disable caching
    mp.disable_cache()
"""

from typing import Optional, Union
from pathlib import Path

_cache_session = None


def enable_cache(
    cache_name: str = "meeps_cache",
    backend: str = "sqlite",
    expire_after: Union[int, float, None] = 3600,
    cache_dir: Optional[Union[str, Path]] = None,
    **kwargs,
) -> None:
    """Enable HTTP-level caching for all API requests.

    Uses requests-cache to transparently cache HTTP responses.
    Requires requests-cache to be installed: pip install requests-cache

    Args:
        cache_name: Name of the cache file (without extension).
        backend: Cache backend. Options: 'sqlite' (default), 'memory',
            'filesystem', 'redis', 'mongodb'. SQLite is recommended
            for persistence across sessions.
        expire_after: Time in seconds before cached responses expire.
            None means cache never expires. Default is 3600 (1 hour).
        cache_dir: Directory to store the cache file. Defaults to
            current working directory.
        **kwargs: Additional arguments passed to requests_cache.install_cache().

    Raises:
        ImportError: If requests-cache is not installed.

    Example:
        import meeps as mp

        # Basic usage - 1 hour cache
        mp.enable_cache()

        # Custom TTL - 24 hours
        mp.enable_cache(expire_after=86400)

        # In-memory cache (not persistent)
        mp.enable_cache(backend='memory')

        # Custom cache location
        mp.enable_cache(cache_dir='/path/to/cache')

        # No expiration (manual clear only)
        mp.enable_cache(expire_after=None)
    """
    global _cache_session

    try:
        import requests_cache
    except ImportError:
        raise ImportError(
            "requests-cache is required for caching. "
            "Install it with: pip install requests-cache"
        )

    # Build cache path if directory specified
    if cache_dir is not None:
        cache_path = Path(cache_dir) / cache_name
        cache_name = str(cache_path)

    # Install cache globally
    requests_cache.install_cache(
        cache_name=cache_name,
        backend=backend,
        expire_after=expire_after,
        **kwargs,
    )

    _cache_session = requests_cache.get_cache()


def disable_cache() -> None:
    """Disable caching and restore normal HTTP behavior.

    After calling this, all API requests will hit the network.
    The cache file is preserved and can be re-enabled later.

    Example:
        import meeps as mp

        mp.enable_cache()
        # ... cached requests ...

        mp.disable_cache()
        # ... normal requests ...
    """
    global _cache_session

    try:
        import requests_cache

        requests_cache.uninstall_cache()
        _cache_session = None
    except ImportError:
        pass  # requests-cache not installed, nothing to disable


def clear_cache() -> None:
    """Clear all cached responses.

    Removes all cached data but keeps caching enabled.
    Useful when you need fresh data.

    Example:
        import meeps as mp

        mp.enable_cache()
        standings = mp.get_tournament_standings("LCK/2024 Season/Summer Season")

        # Force fresh data
        mp.clear_cache()
        standings = mp.get_tournament_standings("LCK/2024 Season/Summer Season")
    """
    global _cache_session

    try:
        import requests_cache

        cache = requests_cache.get_cache()
        if cache is not None:
            cache.clear()
    except ImportError:
        pass  # requests-cache not installed, nothing to clear


def get_cache_info() -> Optional[dict]:
    """Get information about the current cache state.

    Returns:
        Dictionary with cache statistics, or None if caching is disabled.
        Keys include: 'size' (number of cached responses), 'backend',
        'expire_after'.

    Example:
        import meeps as mp

        mp.enable_cache()
        mp.get_tournaments("Korea")
        mp.get_tournaments("Korea")

        info = mp.get_cache_info()
        print(f"Cached responses: {info['size']}")
    """
    try:
        import requests_cache

        cache = requests_cache.get_cache()
        if cache is None:
            return None

        # Get expire_after from cache settings
        expire_after = None
        if hasattr(cache, "_settings") and hasattr(cache._settings, "expire_after"):
            expire_after = cache._settings.expire_after

        return {
            "size": len(cache.responses) if hasattr(cache, "responses") else 0,
            "backend": type(cache).__name__,
            "expire_after": expire_after,
        }
    except ImportError:
        return None


def is_cache_enabled() -> bool:
    """Check if caching is currently enabled.

    Returns:
        True if caching is enabled, False otherwise.
    """
    try:
        import requests_cache

        return requests_cache.get_cache() is not None
    except ImportError:
        return False
