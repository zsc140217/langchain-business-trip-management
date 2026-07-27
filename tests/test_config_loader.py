"""
Test Tool Configuration Loader
Tests configuration loading and validation
"""
import pytest
import yaml
from pathlib import Path
from src.tools.config_loader import ToolConfigLoader, get_config_loader


class TestConfigLoader:
    """Test configuration loader"""

    def test_load_config(self):
        """Test loading configuration from YAML"""
        loader = get_config_loader()
        config = loader.load()

        assert config is not None
        assert 'tools' in config
        assert 'timeouts' in config
        assert 'health_check' in config
        print("[PASS] Configuration loaded successfully")

    def test_get_tool_config(self):
        """Test getting tool-specific configuration"""
        loader = get_config_loader()

        # Test weather tool config
        weather_config = loader.get_tool_config('query_weather')
        assert weather_config is not None
        assert weather_config['enabled'] is True
        assert weather_config['cache_ttl'] == 1800
        assert weather_config['max_retries'] == 3
        assert weather_config['timeout'] == 30
        print("[PASS] Tool configuration retrieved correctly")

    def test_get_tool_timeout(self):
        """Test getting tool timeout settings"""
        loader = get_config_loader()

        # Test weather tool timeout
        timeout = loader.get_tool_timeout('query_weather')
        assert 'call' in timeout
        assert 'total' in timeout
        assert timeout['call'] == 10
        assert timeout['total'] == 30
        print("[PASS] Tool timeout settings retrieved correctly")

    def test_get_global_timeout(self):
        """Test getting global timeout"""
        loader = get_config_loader()
        timeout = loader.get_global_timeout()
        assert timeout == 30
        print("[PASS] Global timeout retrieved correctly")

    def test_get_health_check_config(self):
        """Test getting health check configuration"""
        loader = get_config_loader()
        health_config = loader.get_health_check_config()

        assert health_config['enabled'] is True
        assert health_config['interval'] == 60
        assert health_config['failure_threshold'] == 3
        assert health_config['success_threshold'] == 2
        print("[PASS] Health check config retrieved correctly")

    def test_is_tool_enabled(self):
        """Test checking if tool is enabled"""
        loader = get_config_loader()

        assert loader.is_tool_enabled('query_weather') is True
        assert loader.is_tool_enabled('search_flights') is True
        assert loader.is_tool_enabled('nonexistent_tool') is False
        print("[PASS] Tool enabled status checked correctly")

    def test_get_all_enabled_tools(self):
        """Test getting all enabled tools"""
        loader = get_config_loader()
        enabled_tools = loader.get_all_enabled_tools()

        assert len(enabled_tools) == 8  # Should have 8 enabled tools
        assert 'query_weather' in enabled_tools
        assert 'search_flights' in enabled_tools
        assert 'search_hotels' in enabled_tools
        print("[PASS] All enabled tools retrieved correctly")

    def test_validate_config(self):
        """Test configuration validation"""
        loader = get_config_loader()

        try:
            is_valid = loader.validate_config()
            assert is_valid is True
            print("[PASS] Configuration validation passed")
        except ValueError as e:
            pytest.fail(f"Configuration validation failed: {e}")

    def test_get_channel_config(self):
        """Test getting channel configuration"""
        loader = get_config_loader()

        # Test MCP channel
        mcp_config = loader.get_channel_config('mcp')
        assert mcp_config is not None
        assert mcp_config['enabled'] is True
        assert 'server_script' in mcp_config

        # Test local channel
        local_config = loader.get_channel_config('local')
        assert local_config is not None
        assert local_config['enabled'] is True
        print("[PASS] Channel configuration retrieved correctly")


def run_all_tests():
    """Run all configuration loader tests"""
    print("\n" + "="*60)
    print("Running Configuration Loader Tests")
    print("="*60 + "\n")

    test_suite = TestConfigLoader()

    tests = [
        ("Load Config", test_suite.test_load_config),
        ("Get Tool Config", test_suite.test_get_tool_config),
        ("Get Tool Timeout", test_suite.test_get_tool_timeout),
        ("Get Global Timeout", test_suite.test_get_global_timeout),
        ("Get Health Check Config", test_suite.test_get_health_check_config),
        ("Is Tool Enabled", test_suite.test_is_tool_enabled),
        ("Get All Enabled Tools", test_suite.test_get_all_enabled_tools),
        ("Validate Config", test_suite.test_validate_config),
        ("Get Channel Config", test_suite.test_get_channel_config),
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
            failed += 1

    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
