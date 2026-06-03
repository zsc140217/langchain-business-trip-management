"""
Performance and Security Integration Tests

Tests system performance under load and validates security measures.
"""

import pytest
import time
import concurrent.futures
from ..cache import CacheManager
from ..security import RateLimiter, SQLSanitizer, XSSProtection, TripRequest
from ..monitoring import MetricsCollector


class TestPerformance:
    """Performance tests for production infrastructure."""

    def test_cache_performance(self):
        """Test cache performance with high volume."""
        cache_mgr = CacheManager()
        start_time = time.time()

        # Simulate 1000 cache operations
        for i in range(1000):
            key = f"key_{i % 100}"  # 100 unique keys, high reuse
            cache_mgr.prompt_cache.set(key, f"value_{i}")
            cache_mgr.prompt_cache.get(key)

        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 5.0  # Less than 5 seconds

        stats = cache_mgr.get_stats()
        # Should have high hit rate due to key reuse
        assert stats["prompt_cache"]["hit_rate"] > 0

    def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        collector = MetricsCollector()

        def simulate_request(request_id: int):
            start = time.time()
            time.sleep(0.01)  # Simulate work
            latency = time.time() - start
            collector.record_request(latency, success=True)
            return request_id

        # Simulate 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_request, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 50
        assert collector.performance.total_requests == 50

    def test_rate_limiter_under_load(self):
        """Test rate limiter under high load."""
        limiter = RateLimiter(requests_per_minute=100, burst_size=10)

        allowed_count = 0
        denied_count = 0

        # Simulate 200 rapid requests from same user
        for i in range(200):
            if limiter.is_allowed("test_user"):
                allowed_count += 1
            else:
                denied_count += 1

        # Should have some allowed and some denied
        assert allowed_count > 0
        assert denied_count > 0
        assert allowed_count <= 100  # Respects rate limit


class TestSecurity:
    """Security validation tests."""

    def test_sql_injection_patterns(self):
        """Test various SQL injection patterns."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM passwords--",
            "'; DELETE FROM trips WHERE '1'='1",
            "1'; EXEC sp_MSForEachTable 'DROP TABLE ?'; --",
        ]

        for malicious_input in malicious_inputs:
            assert SQLSanitizer.is_safe(malicious_input) is False

    def test_xss_patterns(self):
        """Test various XSS patterns."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "<svg onload=alert('XSS')>",
        ]

        for malicious_input in malicious_inputs:
            assert XSSProtection.is_safe(malicious_input) is False

    def test_input_sanitization(self):
        """Test input sanitization effectiveness."""
        dangerous_input = "<script>alert('XSS')</script>Hello World"
        sanitized = XSSProtection.sanitize_html(dangerous_input)

        # Should remove script tags but keep content
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized

    def test_valid_inputs_pass(self):
        """Test that valid inputs pass security checks."""
        valid_inputs = [
            "Beijing",
            "Business trip to Shanghai",
            "Meeting with client in Shenzhen",
            "Conference attendance in Hangzhou",
        ]

        for valid_input in valid_inputs:
            assert SQLSanitizer.is_safe(valid_input) is True
            assert XSSProtection.is_safe(valid_input) is True

    def test_boundary_conditions(self):
        """Test boundary conditions for validation."""
        # Test minimum length
        with pytest.raises(Exception):
            TripRequest(
                destination="",  # Empty
                start_date="2026-07-01",
                end_date="2026-07-05",
                purpose="Meeting"
            )

        # Test maximum length (destination)
        long_destination = "A" * 101
        with pytest.raises(Exception):
            TripRequest(
                destination=long_destination,
                start_date="2026-07-01",
                end_date="2026-07-05",
                purpose="Meeting"
            )


class TestCostOptimization:
    """Test cost optimization through caching."""

    def test_cache_cost_savings(self):
        """Test that caching provides cost savings."""
        cache_mgr = CacheManager()

        # Simulate 100 requests with high reuse (10 unique queries)
        for i in range(100):
            query = f"query_{i % 10}"

            # Check cache first
            cached = cache_mgr.retrieval_cache.get(query)
            if not cached:
                # Simulate expensive operation
                result = {"documents": [f"doc_{i}"]}
                cache_mgr.retrieval_cache.set(query, result)

        stats = cache_mgr.get_stats()

        # Should have high hit rate (90% of requests cached)
        retrieval_stats = stats["retrieval_cache"]
        hit_rate = retrieval_stats["hit_rate"]

        assert hit_rate > 50  # At least 50% cache hit rate

    def test_embedding_cache_efficiency(self):
        """Test embedding cache efficiency."""
        cache_mgr = CacheManager()

        # Simulate embedding the same documents multiple times
        documents = ["doc1", "doc2", "doc3"]
        embeddings = {
            "doc1": [0.1, 0.2, 0.3],
            "doc2": [0.4, 0.5, 0.6],
            "doc3": [0.7, 0.8, 0.9]
        }

        # First pass: cache misses
        for doc in documents:
            cached = cache_mgr.embedding_cache.get(doc)
            if not cached:
                cache_mgr.embedding_cache.set(doc, embeddings[doc])

        # Second pass: cache hits
        for doc in documents:
            cached = cache_mgr.embedding_cache.get(doc)
            assert cached == embeddings[doc]

        stats = cache_mgr.get_stats()
        embedding_stats = stats["embedding_cache"]

        # Should have 50% hit rate (second pass all hits)
        assert embedding_stats["hit_rate"] >= 50


class TestMonitoringAccuracy:
    """Test monitoring accuracy and reliability."""

    def test_metrics_accuracy(self):
        """Test that metrics accurately reflect operations."""
        collector = MetricsCollector()

        # Record known metrics
        collector.record_request(0.5, success=True)
        collector.record_request(1.0, success=True)
        collector.record_request(0.3, success=False)

        summary = collector.get_summary()
        perf = summary["performance"]

        # Verify accuracy
        assert perf["total_requests"] == 3
        assert perf["successful_requests"] == 2
        assert perf["failed_requests"] == 1
        assert perf["success_rate"] == pytest.approx(66.67, rel=0.01)

    def test_cost_tracking_accuracy(self):
        """Test cost tracking accuracy."""
        collector = MetricsCollector()

        # Record known costs
        collector.record_api_call("embedding", 0.001, cached=False)
        collector.record_api_call("llm", 0.010, cached=False)
        collector.record_api_call("llm", 0.010, cached=True)  # Cache hit

        summary = collector.get_summary()
        cost = summary["cost"]

        # Verify cost calculation
        assert cost["total_cost_usd"] == 0.011  # Only non-cached calls
        assert cost["cache_savings_usd"] == 0.010  # Cached call savings
        assert cost["savings_rate"] == pytest.approx(47.62, rel=0.1)

    def test_agent_metrics_tracking(self):
        """Test agent-specific metrics tracking."""
        collector = MetricsCollector()

        # Record agent invocations
        collector.record_agent_invocation("PolicyAdvisor", 0.5, True, 0.005)
        collector.record_agent_invocation("PolicyAdvisor", 0.8, True, 0.007)
        collector.record_agent_invocation("TripPlanner", 1.2, False, 0.010)

        summary = collector.get_summary()
        agents = summary["agents"]

        # Verify agent tracking
        assert "PolicyAdvisor" in agents
        assert "TripPlanner" in agents
        assert agents["PolicyAdvisor"]["invocations"] == 2
        assert agents["PolicyAdvisor"]["successes"] == 2
        assert agents["TripPlanner"]["failures"] == 1


class TestResilience:
    """Test system resilience and error handling."""

    def test_cache_fallback(self):
        """Test cache fallback when Redis unavailable."""
        # Create retrieval cache without Redis
        cache_mgr = CacheManager()

        # Should work with in-memory fallback
        cache_mgr.retrieval_cache.set("key1", {"data": "value1"})
        result = cache_mgr.retrieval_cache.get("key1")

        assert result == {"data": "value1"}

    def test_monitoring_under_failure(self):
        """Test monitoring continues to work during failures."""
        collector = MetricsCollector()

        # Record successful requests
        collector.record_request(0.5, success=True)

        # Record failures
        collector.record_request(1.0, success=False)
        collector.record_request(1.5, success=False)

        # Monitoring should still work
        summary = collector.get_summary()
        assert summary["performance"]["total_requests"] == 3
        assert summary["performance"]["failed_requests"] == 2

    def test_rate_limiter_recovery(self):
        """Test rate limiter recovery after blocking."""
        limiter = RateLimiter(requests_per_minute=5, burst_size=3)

        # Hit rate limit
        for i in range(6):
            limiter.is_allowed("test_user")

        # Should be blocked
        assert limiter.is_allowed("test_user") is False

        # Wait for window to reset
        time.sleep(2)

        # Should be able to make requests again
        assert limiter.is_allowed("test_user") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
