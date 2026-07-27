"""
Test Tool Health Check System
Tests health checking functionality
"""
import time
from src.tools.health_check import (
    ToolHealthChecker,
    HealthStatus,
    get_health_checker
)


class TestHealthCheck:
    """Test health check system"""

    def test_register_tool(self):
        """Test registering tools for health checking"""
        checker = ToolHealthChecker(check_interval=10)

        # Register a healthy tool
        def healthy_check():
            return True

        checker.register_tool('test_tool', healthy_check)

        # Verify registration
        status = checker.get_health_status('test_tool')
        assert status is not None
        assert status.tool_name == 'test_tool'
        assert status.status == HealthStatus.UNKNOWN  # Not checked yet
        print("[PASS] Tool registered successfully")

    def test_check_healthy_tool(self):
        """Test checking a healthy tool"""
        checker = ToolHealthChecker(
            check_interval=10,
            failure_threshold=3,
            success_threshold=2
        )

        # Register a healthy tool
        def healthy_check():
            return True

        checker.register_tool('healthy_tool', healthy_check)

        # Check health (need 2 successes to be marked healthy)
        result1 = checker.check_tool_health('healthy_tool')
        assert result1.status == HealthStatus.DEGRADED  # First success
        assert result1.consecutive_successes == 1

        result2 = checker.check_tool_health('healthy_tool')
        assert result2.status == HealthStatus.HEALTHY  # Second success
        assert result2.consecutive_successes == 2

        print("[PASS] Healthy tool check passed")

    def test_check_unhealthy_tool(self):
        """Test checking an unhealthy tool"""
        checker = ToolHealthChecker(
            check_interval=10,
            failure_threshold=3,
            success_threshold=2
        )

        # Register an unhealthy tool
        def unhealthy_check():
            return False

        checker.register_tool('unhealthy_tool', unhealthy_check)

        # Check health (need 3 failures to be marked down)
        result1 = checker.check_tool_health('unhealthy_tool')
        assert result1.status == HealthStatus.DEGRADED  # First failure
        assert result1.consecutive_failures == 1

        result2 = checker.check_tool_health('unhealthy_tool')
        assert result2.status == HealthStatus.DEGRADED  # Second failure
        assert result2.consecutive_failures == 2

        result3 = checker.check_tool_health('unhealthy_tool')
        assert result3.status == HealthStatus.DOWN  # Third failure
        assert result3.consecutive_failures == 3

        print("[PASS] Unhealthy tool check passed")

    def test_check_flaky_tool(self):
        """Test checking a flaky tool (alternating success/failure)"""
        checker = ToolHealthChecker(
            check_interval=10,
            failure_threshold=3,
            success_threshold=2
        )

        # Register a flaky tool
        self.flaky_counter = 0

        def flaky_check():
            self.flaky_counter += 1
            return self.flaky_counter % 2 == 0  # Alternating

        checker.register_tool('flaky_tool', flaky_check)

        # Check multiple times
        result1 = checker.check_tool_health('flaky_tool')  # Failure
        assert result1.status == HealthStatus.DEGRADED

        result2 = checker.check_tool_health('flaky_tool')  # Success
        assert result2.status == HealthStatus.DEGRADED

        print("[PASS] Flaky tool check passed")

    def test_check_tool_with_exception(self):
        """Test checking a tool that throws exception"""
        checker = ToolHealthChecker(
            check_interval=10,
            failure_threshold=2,
            success_threshold=2
        )

        # Register a tool that throws exception
        def exception_check():
            raise RuntimeError("Tool failed")

        checker.register_tool('exception_tool', exception_check)

        # Check health
        result1 = checker.check_tool_health('exception_tool')
        assert result1.status == HealthStatus.DEGRADED  # First failure
        assert result1.error == "Tool failed"

        result2 = checker.check_tool_health('exception_tool')
        assert result2.status == HealthStatus.DOWN  # Second failure (threshold=2)

        print("[PASS] Exception handling passed")

    def test_check_all_tools(self):
        """Test checking all registered tools"""
        checker = ToolHealthChecker(check_interval=10)

        # Register multiple tools
        checker.register_tool('tool1', lambda: True)
        checker.register_tool('tool2', lambda: True)
        checker.register_tool('tool3', lambda: False)

        # Check all tools
        results = checker.check_all_tools()

        assert len(results) == 3
        assert 'tool1' in results
        assert 'tool2' in results
        assert 'tool3' in results

        print("[PASS] Check all tools passed")

    def test_get_healthy_tools(self):
        """Test getting only healthy tools"""
        checker = ToolHealthChecker(
            check_interval=10,
            success_threshold=1  # Only need 1 success
        )

        # Register tools
        checker.register_tool('healthy1', lambda: True)
        checker.register_tool('healthy2', lambda: True)
        checker.register_tool('unhealthy', lambda: False)

        # Check all tools
        checker.check_all_tools()

        # Get healthy tools
        healthy_tools = checker.get_healthy_tools()
        assert len(healthy_tools) == 2
        assert 'healthy1' in healthy_tools
        assert 'healthy2' in healthy_tools
        assert 'unhealthy' not in healthy_tools

        print("[PASS] Get healthy tools passed")

    def test_get_unhealthy_tools(self):
        """Test getting only unhealthy tools"""
        checker = ToolHealthChecker(check_interval=10)

        # Register tools
        checker.register_tool('healthy', lambda: True)
        checker.register_tool('unhealthy1', lambda: False)
        checker.register_tool('unhealthy2', lambda: False)

        # Check all tools
        checker.check_all_tools()

        # Get unhealthy tools
        unhealthy_tools = checker.get_unhealthy_tools()
        assert len(unhealthy_tools) >= 2  # At least unhealthy1 and unhealthy2
        assert 'healthy' not in unhealthy_tools

        print("[PASS] Get unhealthy tools passed")

    def test_latency_measurement(self):
        """Test latency measurement"""
        checker = ToolHealthChecker(check_interval=10)

        # Register a tool with delay
        def slow_check():
            time.sleep(0.05)  # 50ms delay
            return True

        checker.register_tool('slow_tool', slow_check)

        # Check health
        result = checker.check_tool_health('slow_tool')
        assert result.latency_ms >= 50  # Should be at least 50ms
        assert result.latency_ms < 100  # Should be less than 100ms

        print(f"[PASS] Latency measurement passed (measured: {result.latency_ms:.2f}ms)")


def run_all_tests():
    """Run all health check tests"""
    print("\n" + "="*60)
    print("Running Health Check Tests")
    print("="*60 + "\n")

    test_suite = TestHealthCheck()

    tests = [
        ("Register Tool", test_suite.test_register_tool),
        ("Check Healthy Tool", test_suite.test_check_healthy_tool),
        ("Check Unhealthy Tool", test_suite.test_check_unhealthy_tool),
        ("Check Flaky Tool", test_suite.test_check_flaky_tool),
        ("Check Tool with Exception", test_suite.test_check_tool_with_exception),
        ("Check All Tools", test_suite.test_check_all_tools),
        ("Get Healthy Tools", test_suite.test_get_healthy_tools),
        ("Get Unhealthy Tools", test_suite.test_get_unhealthy_tools),
        ("Latency Measurement", test_suite.test_latency_measurement),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n[Test] {test_name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
