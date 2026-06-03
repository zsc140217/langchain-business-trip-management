"""
Three-Layer Caching Strategy

Implements a comprehensive caching system to reduce costs and improve performance:
1. Prompt Cache (InMemoryCache): Cache LLM prompts and responses
2. Embedding Cache (CacheBackedEmbeddings): Cache vector embeddings
3. Retrieval Cache (Redis): Cache document retrieval results

Expected Cost Savings: 60%+ on repeated queries
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from langchain.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_core.embeddings import Embeddings
from langchain.storage import InMemoryStore

logger = logging.getLogger(__name__)


class CacheStats:
    """Track cache hit/miss statistics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_queries = 0
        self.cost_savings_estimate = 0.0

    def record_hit(self, cost_saved: float = 0.0):
        """Record a cache hit."""
        self.hits += 1
        self.total_queries += 1
        self.cost_savings_estimate += cost_saved

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
        self.total_queries += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_queries == 0:
            return 0.0
        return self.hits / self.total_queries

    def get_stats(self) -> Dict[str, Any]:
        """Get all cache statistics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_queries": self.total_queries,
            "hit_rate": self.get_hit_rate(),
            "cost_savings_estimate": self.cost_savings_estimate
        }


class BaseCache(ABC):
    """Base class for all cache implementations."""

    def __init__(self, ttl: Optional[int] = None):
        """
        Initialize cache.

        Args:
            ttl: Time-to-live in seconds (None = no expiration)
        """
        self.ttl = ttl
        self.stats = CacheStats()

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()


class PromptCache(BaseCache):
    """
    Layer 1: In-memory cache for LLM prompts and responses.

    Uses LangChain's InMemoryCache for fast prompt caching.
    Reduces API calls for identical prompts.
    """

    def __init__(self, ttl: Optional[int] = 3600):
        """
        Initialize prompt cache.

        Args:
            ttl: Cache TTL in seconds (default: 1 hour)
        """
        super().__init__(ttl)
        self._cache = {}
        self._timestamps = {}
        self._setup_langchain_cache()

    def _setup_langchain_cache(self):
        """Configure LangChain's global LLM cache."""
        try:
            set_llm_cache(InMemoryCache())
            logger.info("LangChain InMemoryCache configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure LangChain cache: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get cached prompt response."""
        # Check if key exists and not expired
        if key in self._cache:
            if self.ttl is None or self._is_valid(key):
                self.stats.record_hit(cost_saved=0.001)  # Estimate: $0.001 per cached call
                return self._cache[key]
            else:
                # Expired, remove it
                self.delete(key)

        self.stats.record_miss()
        return None

    def set(self, key: str, value: Any) -> None:
        """Cache a prompt response."""
        self._cache[key] = value
        self._timestamps[key] = datetime.utcnow()

    def delete(self, key: str) -> None:
        """Delete a cached entry."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Prompt cache cleared")

    def _is_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._timestamps:
            return False

        timestamp = self._timestamps[key]
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self.ttl


class EmbeddingCache(BaseCache):
    """
    Layer 2: Cache for vector embeddings.

    Uses CacheBackedEmbeddings pattern to avoid recomputing embeddings
    for the same text. Significant cost savings for large documents.
    """

    def __init__(self, ttl: Optional[int] = 86400):  # 24 hours default
        """
        Initialize embedding cache.

        Args:
            ttl: Cache TTL in seconds (default: 24 hours)
        """
        super().__init__(ttl)
        self._store = InMemoryStore()
        self._timestamps = {}

    def get(self, key: str) -> Optional[List[float]]:
        """Get cached embedding."""
        try:
            value = self._store.mget([key])[0]
            if value is not None and (self.ttl is None or self._is_valid(key)):
                self.stats.record_hit(cost_saved=0.0001)  # Estimate: $0.0001 per embedding
                return value
            elif value is not None:
                # Expired
                self.delete(key)
        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")

        self.stats.record_miss()
        return None

    def set(self, key: str, value: List[float]) -> None:
        """Cache an embedding."""
        try:
            self._store.mset([(key, value)])
            self._timestamps[key] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error setting cached embedding: {e}")

    def delete(self, key: str) -> None:
        """Delete a cached embedding."""
        try:
            self._store.mdelete([key])
            self._timestamps.pop(key, None)
        except Exception as e:
            logger.error(f"Error deleting cached embedding: {e}")

    def clear(self) -> None:
        """Clear all cached embeddings."""
        # InMemoryStore doesn't have a clear method, recreate it
        self._store = InMemoryStore()
        self._timestamps.clear()
        logger.info("Embedding cache cleared")

    def _is_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._timestamps:
            return False

        timestamp = self._timestamps[key]
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self.ttl

    def get_cached_embeddings(self, embeddings: Embeddings, namespace: str = "default") -> Embeddings:
        """
        Wrap embeddings with caching layer.

        Args:
            embeddings: Base embeddings instance
            namespace: Cache namespace for organization

        Returns:
            CacheBackedEmbeddings instance
        """
        try:
            from langchain.embeddings import CacheBackedEmbeddings

            cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
                underlying_embeddings=embeddings,
                document_embedding_cache=self._store,
                namespace=namespace
            )
            logger.info(f"CacheBackedEmbeddings created with namespace: {namespace}")
            return cached_embeddings
        except Exception as e:
            logger.error(f"Failed to create CacheBackedEmbeddings: {e}")
            return embeddings


class RetrievalCache(BaseCache):
    """
    Layer 3: Redis cache for document retrieval results.

    Caches retrieved documents to avoid repeated vector searches.
    Falls back to in-memory if Redis is unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None, ttl: Optional[int] = 1800):
        """
        Initialize retrieval cache.

        Args:
            redis_url: Redis connection URL (None = use in-memory fallback)
            ttl: Cache TTL in seconds (default: 30 minutes)
        """
        super().__init__(ttl)
        self.redis_url = redis_url
        self._redis_client = None
        self._memory_fallback = {}
        self._timestamps = {}

        if redis_url:
            self._init_redis()
        else:
            logger.warning("Redis URL not provided, using in-memory fallback")

    def _init_redis(self):
        """Initialize Redis client."""
        try:
            import redis
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except ImportError:
            logger.warning("redis package not installed, using in-memory fallback")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}, using in-memory fallback")
            self._redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get cached retrieval results."""
        if self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value:
                    self.stats.record_hit(cost_saved=0.002)  # Estimate: $0.002 per search
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                # Fall through to memory fallback

        # In-memory fallback
        if key in self._memory_fallback:
            if self.ttl is None or self._is_valid(key):
                self.stats.record_hit(cost_saved=0.002)
                return self._memory_fallback[key]
            else:
                self.delete(key)

        self.stats.record_miss()
        return None

    def set(self, key: str, value: Any) -> None:
        """Cache retrieval results."""
        serialized = json.dumps(value)

        if self._redis_client:
            try:
                if self.ttl:
                    self._redis_client.setex(key, self.ttl, serialized)
                else:
                    self._redis_client.set(key, serialized)
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                # Fall through to memory fallback

        # In-memory fallback
        self._memory_fallback[key] = value
        self._timestamps[key] = datetime.utcnow()

    def delete(self, key: str) -> None:
        """Delete cached entry."""
        if self._redis_client:
            try:
                self._redis_client.delete(key)
                return
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        # In-memory fallback
        self._memory_fallback.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        if self._redis_client:
            try:
                self._redis_client.flushdb()
                logger.info("Redis cache cleared")
                return
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        # In-memory fallback
        self._memory_fallback.clear()
        self._timestamps.clear()
        logger.info("In-memory retrieval cache cleared")

    def _is_valid(self, key: str) -> bool:
        """Check if in-memory cache entry is still valid."""
        if key not in self._timestamps:
            return False

        timestamp = self._timestamps[key]
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self.ttl


class CacheManager:
    """
    Unified cache manager for all three layers.

    Provides a single interface to manage and monitor all caching layers.
    """

    def __init__(
        self,
        prompt_cache_ttl: int = 3600,
        embedding_cache_ttl: int = 86400,
        retrieval_cache_ttl: int = 1800,
        redis_url: Optional[str] = None
    ):
        """
        Initialize cache manager.

        Args:
            prompt_cache_ttl: TTL for prompt cache (seconds)
            embedding_cache_ttl: TTL for embedding cache (seconds)
            retrieval_cache_ttl: TTL for retrieval cache (seconds)
            redis_url: Redis connection URL (optional)
        """
        self.prompt_cache = PromptCache(ttl=prompt_cache_ttl)
        self.embedding_cache = EmbeddingCache(ttl=embedding_cache_ttl)
        self.retrieval_cache = RetrievalCache(redis_url=redis_url, ttl=retrieval_cache_ttl)

        logger.info("CacheManager initialized with all three layers")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all cache layers."""
        return {
            "prompt_cache": self.prompt_cache.stats.get_stats(),
            "embedding_cache": self.embedding_cache.stats.get_stats(),
            "retrieval_cache": self.retrieval_cache.stats.get_stats(),
            "total_cost_savings": (
                self.prompt_cache.stats.cost_savings_estimate +
                self.embedding_cache.stats.cost_savings_estimate +
                self.retrieval_cache.stats.cost_savings_estimate
            )
        }

    def clear_all(self) -> None:
        """Clear all cache layers."""
        self.prompt_cache.clear()
        self.embedding_cache.clear()
        self.retrieval_cache.clear()
        logger.info("All cache layers cleared")

    def get_cached_embeddings(
        self,
        embeddings: Embeddings,
        namespace: str = "default"
    ) -> Embeddings:
        """
        Get cached embeddings wrapper.

        Args:
            embeddings: Base embeddings instance
            namespace: Cache namespace

        Returns:
            CacheBackedEmbeddings instance
        """
        return self.embedding_cache.get_cached_embeddings(embeddings, namespace)


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager

    if _cache_manager is None:
        redis_url = None  # Set from environment if needed
        _cache_manager = CacheManager(redis_url=redis_url)

    return _cache_manager


def initialize_cache(
    prompt_ttl: int = 3600,
    embedding_ttl: int = 86400,
    retrieval_ttl: int = 1800,
    redis_url: Optional[str] = None
) -> CacheManager:
    """
    Initialize global cache manager.

    Args:
        prompt_ttl: TTL for prompt cache (seconds)
        embedding_ttl: TTL for embedding cache (seconds)
        retrieval_ttl: TTL for retrieval cache (seconds)
        redis_url: Redis connection URL

    Returns:
        Configured CacheManager instance
    """
    global _cache_manager

    _cache_manager = CacheManager(
        prompt_cache_ttl=prompt_ttl,
        embedding_cache_ttl=embedding_ttl,
        retrieval_cache_ttl=retrieval_ttl,
        redis_url=redis_url
    )

    return _cache_manager


# Example usage
if __name__ == "__main__":
    # Initialize cache manager
    cache_mgr = initialize_cache()

    # Get statistics
    stats = cache_mgr.get_stats()
    print("Cache Statistics:", json.dumps(stats, indent=2))

    # Clear all caches
    cache_mgr.clear_all()
