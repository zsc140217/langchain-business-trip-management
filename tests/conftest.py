"""
Pytest Configuration and Fixtures
Provides shared fixtures for all tests

Features:
- Mock LLM for testing without API calls
- Test data fixtures
- Database setup/teardown
- Logging configuration
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# Mock LLM Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """
    Mock LLM for testing without API calls

    Returns responses based on input prompt patterns
    """
    mock = Mock()

    def predict_side_effect(prompt: str, **kwargs) -> str:
        """Return different responses based on prompt content"""
        if "weather" in prompt.lower():
            return "Beijing: Sunny, 25°C, Wind: 3m/s, Humidity: 60%"
        elif "hotel" in prompt.lower():
            return "Recommended hotels: Hilton Beijing, Marriott Beijing"
        elif "policy" in prompt.lower():
            return "Accommodation policy: Maximum 500 RMB per night for tier-1 cities"
        elif "task decomposition" in prompt.lower() or "subtask" in prompt.lower():
            return """[
  {
    "id": 0,
    "task_type": "QUERY_WEATHER",
    "description": "Query Beijing weather",
    "parameters": {"city": "Beijing"},
    "depends_on": [],
    "priority": 0
  },
  {
    "id": 1,
    "task_type": "QUERY_HOTEL",
    "description": "Recommend Beijing hotels",
    "parameters": {"city": "Beijing"},
    "depends_on": [],
    "priority": 0
  }
]"""
        elif "trip" in prompt.lower() or "itinerary" in prompt.lower():
            return """Trip Itinerary:
1. Weather: Beijing - Sunny, 25°C
2. Accommodation: Hilton Beijing (Corporate rate available)
3. Transportation: High-speed train available
4. Notes: Bring business cards for meetings"""
        else:
            return "Mock LLM response for: " + prompt[:50]

    mock.predict = Mock(side_effect=predict_side_effect)
    mock.invoke = Mock(side_effect=lambda x: MagicMock(content=predict_side_effect(x.content if hasattr(x, 'content') else str(x))))

    return mock


@pytest.fixture
def mock_chat_model():
    """Mock ChatModel compatible with LangChain"""
    mock = Mock()
    mock.predict = Mock(return_value="Mock response")
    mock.invoke = Mock(return_value=MagicMock(content="Mock response"))
    return mock


# ============================================================================
# Tool Fixtures
# ============================================================================

@pytest.fixture
def mock_weather_tool():
    """Mock weather tool"""
    mock = Mock()
    mock.name = "query_weather"
    mock.invoke = Mock(return_value="Beijing: Sunny, 25°C, Wind: 3m/s, Humidity: 60%")
    return mock


@pytest.fixture
def mock_hotel_tool():
    """Mock hotel tool"""
    mock = Mock()
    mock.name = "query_hotel"
    mock.invoke = Mock(return_value="Recommended hotels: Hilton Beijing, Marriott Beijing")
    return mock


@pytest.fixture
def mock_policy_tool():
    """Mock policy tool"""
    mock = Mock()
    mock.name = "query_policy"
    mock.invoke = Mock(return_value="Accommodation policy: Maximum 500 RMB per night")
    return mock


@pytest.fixture
def all_mock_tools(mock_weather_tool, mock_hotel_tool, mock_policy_tool):
    """All mock tools"""
    return [mock_weather_tool, mock_hotel_tool, mock_policy_tool]


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_trip_task() -> Dict[str, Any]:
    """Sample trip planning task"""
    return {
        "query": "Plan a business trip to Beijing: check weather, recommend hotel",
        "user_id": "test_user_001",
        "preferences": {
            "budget": "medium",
            "hotel_chain": "Hilton"
        }
    }


@pytest.fixture
def sample_policy_task() -> Dict[str, Any]:
    """Sample policy query task"""
    return {
        "query": "What is the accommodation policy for Beijing?",
        "user_id": "test_user_001",
        "context": {
            "user_level": "senior",
            "department": "sales"
        }
    }


@pytest.fixture
def sample_expense() -> Dict[str, Any]:
    """Sample expense record"""
    return {
        "amount": 450.00,
        "category": "accommodation",
        "city": "Beijing",
        "date": "2024-06-01",
        "description": "Hotel stay for client meeting"
    }


@pytest.fixture
def sample_subtasks() -> List[Dict[str, Any]]:
    """Sample subtasks for task decomposition"""
    return [
        {
            "id": 0,
            "task_type": "QUERY_WEATHER",
            "description": "Query Beijing weather",
            "parameters": {"city": "Beijing"},
            "depends_on": [],
            "priority": 0
        },
        {
            "id": 1,
            "task_type": "QUERY_HOTEL",
            "description": "Recommend Beijing hotels",
            "parameters": {"city": "Beijing"},
            "depends_on": [],
            "priority": 0
        },
        {
            "id": 2,
            "task_type": "QUERY_ROUTE",
            "description": "Plan route to customer",
            "parameters": {"origin": "hotel", "destination": "customer_office"},
            "depends_on": [1],
            "priority": 1
        }
    ]


# ============================================================================
# Test Database Fixtures
# ============================================================================

@pytest.fixture
def test_db_path(tmp_path):
    """Temporary database path for testing"""
    return tmp_path / "test_db.sqlite"


@pytest.fixture
def clean_test_env(monkeypatch):
    """Clean test environment without API keys"""
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEATHER_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration"""
    return {
        "temperature": 0.3,
        "top_k": 3,
        "use_reranker": False,
        "use_query_rewriting": False,
        "max_retries": 2,
        "timeout_seconds": 10.0
    }


# ============================================================================
# Logging Configuration
# ============================================================================

@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configure logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Only show warnings and errors in tests
        format='%(name)s - %(levelname)s - %(message)s'
    )
    yield
    # Cleanup after test
    logging.getLogger().handlers.clear()


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    for item in items:
        # Add marker based on test path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
