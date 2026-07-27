"""
Comprehensive Test Suite for Tool Ecosystem Engineering Features
Tests configuration loading, health checking, and registry integration
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_config_loader():
    """Test configuration loader"""
    print("\n" + "="*60)
    print("Testing Configuration Loader")
    print("="*60)

    from src.tools.config_loader import get_config_loader

    try:
        loader = get_config_loader()
        config = loader.load()

        # Test 1: Config loaded
        assert config is not None
        print("[PASS] Configuration loaded successfully")

        # Test 2: Get tool config
        weather_config = loader.get_tool_config('query_weather')
        assert weather_config is not None
        assert weather_config['cache_ttl'] == 1800
        print("[PASS] Tool configuration retrieved")

        # Test 3: Get all enabled tools
        enabled_tools = loader.get_all_enabled_tools()
        assert len(enabled_tools) == 8
        print(f"[PASS] Found {len(enabled_tools)} enabled tools")

        # Test 4: Validate config
        loader.validate_config()
        print("[PASS] Configuration validation passed")

        return True

    except Exception as e:
        print(f"[FAIL] Configuration loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_check():
    """Test health check system"""
    print("\n" + "="*60)
    print("Testing Health Check System")
    print("="*60)

    from src.tools.health_check import ToolHealthChecker, HealthStatus

    try:
        checker = ToolHealthChecker(
            check_interval=10,
            failure_threshold=3,
            success_threshold=2
        )

        # Test 1: Register tool
        checker.register_tool('test_healthy', lambda: True)
        checker.register_tool('test_unhealthy', lambda: False)
        print("[PASS] Tools registered for health checking")

        # Test 2: Check healthy tool
        result = checker.check_tool_health('test_healthy')
        assert result.status in [HealthStatus.DEGRADED, HealthStatus.HEALTHY]
        print(f"[PASS] Healthy tool check: {result.status.value}")

        # Test 3: Check unhealthy tool
        result = checker.check_tool_health('test_unhealthy')
        assert result.status in [HealthStatus.DEGRADED, HealthStatus.DOWN]
        print(f"[PASS] Unhealthy tool check: {result.status.value}")

        # Test 4: Check all tools
        results = checker.check_all_tools()
        assert len(results) == 2
        print(f"[PASS] Checked all {len(results)} tools")

        return True

    except Exception as e:
        print(f"[FAIL] Health check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_tool_integration():
    """Test BaseTool integration with config"""
    print("\n" + "="*60)
    print("Testing BaseTool Configuration Integration")
    print("="*60)

    try:
        from src.tools.base_tool import BaseTool
        from pydantic import BaseModel, Field

        # Create a test tool
        class TestToolInput(BaseModel):
            param: str = Field(description="Test parameter")

        class TestTool(BaseTool):
            name: str = "query_weather"  # Use existing config
            description: str = "Test tool"
            args_schema: type[BaseModel] = TestToolInput

            def _run(self, param: str) -> str:
                return f"Result: {param}"

        # Instantiate tool (should load config)
        tool = TestTool()

        # Test 1: Config loaded
        assert tool.cache_ttl_seconds == 1800  # From config
        print(f"[PASS] Tool loaded config: cache_ttl={tool.cache_ttl_seconds}")

        # Test 2: Health check
        is_healthy = tool.health_check()
        assert is_healthy is True
        print("[PASS] Tool health check passed")

        # Test 3: Get stats
        stats = tool.get_stats()
        assert 'name' in stats
        assert stats['cache_ttl_seconds'] == 1800
        print(f"[PASS] Tool stats retrieved: {stats['name']}")

        return True

    except Exception as e:
        print(f"[FAIL] BaseTool integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_registry_integration():
    """Test ToolRegistry integration with health check"""
    print("\n" + "="*60)
    print("Testing ToolRegistry Health Check Integration")
    print("="*60)

    try:
        from src.tools.registry import get_tool_registry

        registry = get_tool_registry()

        # Test 1: Initialize tools
        registry.initialize_all()
        tools = registry.list_tools()
        print(f"[PASS] Initialized {len(tools)} tools")

        # Test 2: Get stats
        stats = registry.get_stats()
        assert len(stats) > 0
        print(f"[PASS] Got stats for {len(stats)} tools")

        # Test 3: Enable health check
        registry.enable_health_check()
        print("[PASS] Health check enabled")

        # Test 4: Get health status
        import time
        time.sleep(1)  # Give health check time to run
        health_status = registry.get_health_status()
        print(f"[PASS] Health status retrieved for {len(health_status)} tools")

        # Test 5: Disable health check
        registry.disable_health_check()
        print("[PASS] Health check disabled")

        return True

    except Exception as e:
        print(f"[FAIL] Registry integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all engineering feature tests"""
    print("\n" + "="*70)
    print("  Tool Ecosystem Engineering Features - Comprehensive Test Suite")
    print("="*70)

    results = []

    # Run tests
    results.append(("Configuration Loader", test_config_loader()))
    results.append(("Health Check System", test_health_check()))
    results.append(("BaseTool Integration", test_base_tool_integration()))
    results.append(("Registry Integration", test_registry_integration()))

    # Summary
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {test_name}")

    print("\n" + "-"*70)
    print(f"  Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
