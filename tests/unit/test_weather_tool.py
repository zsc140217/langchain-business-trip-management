"""
Unit Tests for WeatherTool

Tests:
- Weather query for known cities
- Weather query for unknown cities
- API call handling
- Fallback mechanism
- Caching
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools.weather_tool import WeatherTool


class TestWeatherTool:
    """Test suite for WeatherTool"""

    def test_tool_initialization(self):
        """Test weather tool initialization"""
        tool = WeatherTool(api_key="test_key")

        assert tool.name == "query_weather"
        assert tool.api_key == "test_key"
        assert tool.cache_enabled is True
        assert tool.cache_ttl_seconds == 1800

    def test_tool_initialization_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            tool = WeatherTool()
            assert tool.api_key is None

    def test_query_known_city_fallback(self):
        """Test querying weather for known city (fallback mode)"""
        tool = WeatherTool()  # No API key, will use fallback

        result = tool.invoke({"city": "北京"})

        assert "北京" in result or "Beijing" in result
        assert "模拟数据" in result or "Mock" in result.lower()

    def test_query_unknown_city_fallback(self):
        """Test querying weather for unknown city (fallback mode)"""
        tool = WeatherTool()

        result = tool.invoke({"city": "Unknown City"})

        assert "Unknown City" in result
        assert "模拟数据" in result

    def test_missing_city_parameter(self):
        """Test error when city parameter is missing"""
        tool = WeatherTool()

        with pytest.raises(ValueError) as exc_info:
            tool.invoke({})

        assert "City parameter is required" in str(exc_info.value)

    def test_empty_city_parameter(self):
        """Test error when city parameter is empty"""
        tool = WeatherTool()

        with pytest.raises(ValueError):
            tool.invoke({"city": ""})

    @patch('requests.get')
    def test_api_call_success(self, mock_get):
        """Test successful API call"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": "200",
            "now": {
                "temp": "25",
                "text": "晴天",
                "windSpeed": "3",
                "humidity": "60"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        tool = WeatherTool(api_key="test_key")
        result = tool.invoke({"city": "北京"})

        assert "25" in result
        assert "晴天" in result
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_api_call_failure(self, mock_get):
        """Test API call failure fallback"""
        mock_get.side_effect = Exception("Network error")

        tool = WeatherTool(api_key="test_key")
        result = tool.invoke({"city": "北京"})

        # Should fallback to mock data
        assert "模拟数据" in result

    @patch('requests.get')
    def test_api_error_code(self, mock_get):
        """Test API returning error code"""
        mock_response = Mock()
        mock_response.json.return_value = {"code": "401", "error": "Invalid key"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        tool = WeatherTool(api_key="test_key")
        result = tool.invoke({"city": "北京"})

        # Should fallback to mock data
        assert "模拟数据" in result

    def test_city_normalization(self):
        """Test city name normalization"""
        tool = WeatherTool()

        result1 = tool.invoke({"city": "Beijing"})
        result2 = tool.invoke({"city": "BEIJING"})
        result3 = tool.invoke({"city": "  beijing  "})

        # All should return similar results (fallback data)
        assert "模拟数据" in result1
        assert "模拟数据" in result2
        assert "模拟数据" in result3

    def test_multiple_cities_fallback(self):
        """Test querying multiple cities with fallback"""
        tool = WeatherTool()

        cities = ["北京", "上海", "广州", "深圳", "杭州"]
        results = [tool.invoke({"city": city}) for city in cities]

        # All should return results
        assert len(results) == 5
        for result in results:
            assert "模拟数据" in result

    def test_caching_mechanism(self):
        """Test that caching works"""
        tool = WeatherTool()
        tool.cache_enabled = True

        # First call
        result1 = tool.invoke({"city": "北京"})

        # Second call should hit cache
        result2 = tool.invoke({"city": "北京"})

        assert result1 == result2

    def test_format_weather_response(self):
        """Test weather response formatting"""
        tool = WeatherTool()

        weather_data = {
            "temp": "25",
            "text": "晴天",
            "windSpeed": "3",
            "humidity": "60"
        }

        result = tool._format_weather_response("北京", weather_data)

        assert "北京" in result
        assert "25" in result
        assert "晴天" in result
        assert "3" in result
        assert "60" in result

    def test_fallback_weather_chinese_cities(self):
        """Test fallback data for Chinese city names"""
        tool = WeatherTool()

        chinese_cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]

        for city in chinese_cities:
            result = tool._fallback_weather(city)
            assert city in result
            assert "°C" in result

    def test_fallback_weather_english_cities(self):
        """Test fallback data for English city names"""
        tool = WeatherTool()

        english_cities = ["beijing", "shanghai", "guangzhou"]

        for city in english_cities:
            result = tool._fallback_weather(city)
            assert "°C" in result
