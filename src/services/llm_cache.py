"""
LLM Response Cache for performance optimization.
"""

import asyncio
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LLMCache:
    """Cache for LLM responses to avoid redundant API calls."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the LLM cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task = None

    def _generate_key(self, prompt: str) -> str:
        """
        Generate a cache key from a prompt.

        Args:
            prompt: LLM prompt

        Returns:
            Hash key for the cache
        """
        # Use SHA256 hash of the prompt as the key
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    async def get(self, prompt: str) -> Optional[str]:
        """
        Get cached response for a prompt.

        Args:
            prompt: LLM prompt

        Returns:
            Cached response if exists and not expired, None otherwise
        """
        key = self._generate_key(prompt)

        if key not in self.cache:
            logger.debug(f"Cache miss for prompt hash: {key[:8]}...")
            return None

        entry = self.cache[key]
        expiry = entry['expiry']

        # Check if expired
        if datetime.now() > expiry:
            logger.debug(f"Cache entry expired for prompt hash: {key[:8]}...")
            del self.cache[key]
            return None

        logger.debug(f"Cache hit for prompt hash: {key[:8]}...")
        return entry['response']

    async def set(self, prompt: str, response: str) -> None:
        """
        Cache a response for a prompt.

        Args:
            prompt: LLM prompt
            response: LLM response
        """
        key = self._generate_key(prompt)
        expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)

        self.cache[key] = {
            'response': response,
            'expiry': expiry,
            'created_at': datetime.now()
        }

        logger.debug(f"Cached response for prompt hash: {key[:8]}... (TTL: {self.ttl_seconds}s)")

    async def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    async def cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry['expiry'] < now
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def start_cleanup_task(self, interval_seconds: int = 300):
        """
        Start periodic cleanup task.

        Args:
            interval_seconds: Interval between cleanup runs
        """
        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval_seconds)
                await self.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self):
        """Stop the periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()


# Global cache instance
_cache_instance = None


def get_llm_cache(ttl_seconds: int = 3600) -> LLMCache:
    """
    Get the global LLM cache instance.

    Args:
        ttl_seconds: TTL for new cache instance if creating

    Returns:
        LLMCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMCache(ttl_seconds=ttl_seconds)
    return _cache_instance
