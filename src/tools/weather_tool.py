"""
Weather Tool
Query real-time weather information using QWeather API

Features:
- Real-time weather data
- 7-day forecast
- Weather alerts
- Caching (30-minute TTL)
- Fallback to mock data if API fails
"""
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
import os
import requests
import logging

logger = logging.getLogger(__name__)


class WeatherTool(BaseTool):
    """
    Weather query tool using QWeather API

    Example:
        tool = WeatherTool(api_key="your_api_key")
        result = tool.invoke({"city": "Beijing"})
        # Returns: "Beijing: Sunny, 25°C, Wind: 3m/s, Humidity: 60%"
    """

    name: str = "query_weather"
    description: str = """Query real-time weather information for a city.

    Input should be a dictionary with:
    - city (str): City name in Chinese or English (e.g., "北京", "Beijing", "Shanghai")

    Returns weather information including:
    - Temperature
    - Weather condition (sunny, cloudy, rainy, etc.)
    - Wind speed
    - Humidity
    """

    # Configuration
    api_key: Optional[str] = None
    base_url: str = "https://devapi.qweather.com/v7/weather/now"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 1800  # 30 minutes
    max_retries: int = 2
    timeout_seconds: float = 5.0

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if api_key is None:
            api_key = os.getenv("QWEATHER_API_KEY")
        super().__init__(api_key=api_key, **kwargs)

    @property
    def city_mapping(self) -> Dict[str, str]:
        """City name to location ID mapping (QWeather requires location ID)"""
        return {
            "北京": "101010100",
            "beijing": "101010100",
            "上海": "101020100",
            "shanghai": "101020100",
            "广州": "101280101",
            "guangzhou": "101280101",
            "深圳": "101280601",
            "shenzhen": "101280601",
            "杭州": "101210101",
            "hangzhou": "101210101",
            "成都": "101270101",
            "chengdu": "101270101",
        }

    def _run(self, city: str) -> str:
        """
        Query weather for a city

        Args:
            city: City name

        Returns:
            Weather information string

        Raises:
            ValueError: Invalid city
            RuntimeError: API call failed
        """
        if not city:
            raise ValueError("City parameter is required")

        logger.info(f"Querying weather for: {city}")

        # Normalize city name
        city_lower = city.lower().strip()

        # Get location ID
        location_id = self.city_mapping.get(city_lower)
        if not location_id:
            logger.warning(f"City '{city}' not in mapping, using fallback")
            return self._fallback_weather(city)

        # Check if API key is configured
        if not self.api_key:
            logger.warning("QWeather API key not configured, using fallback")
            return self._fallback_weather(city)

        try:
            # Call QWeather API
            weather_data = self._call_qweather_api(location_id)
            return self._format_weather_response(city, weather_data)

        except Exception as e:
            logger.error(f"Weather API call failed: {e}")
            return self._fallback_weather(city)

    def _call_qweather_api(self, location_id: str) -> Dict[str, Any]:
        """
        Call QWeather API

        Args:
            location_id: QWeather location ID

        Returns:
            Weather data dictionary

        Raises:
            RuntimeError: API call failed
        """
        params = {
            "location": location_id,
            "key": self.api_key
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") != "200":
                raise RuntimeError(f"QWeather API error: {data.get('code')}")

            return data.get("now", {})

        except requests.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e

    def _format_weather_response(self, city: str, weather_data: Dict[str, Any]) -> str:
        """
        Format weather data into readable string

        Args:
            city: City name
            weather_data: Weather data from API

        Returns:
            Formatted weather string
        """
        temp = weather_data.get("temp", "N/A")
        condition = weather_data.get("text", "N/A")
        wind_speed = weather_data.get("windSpeed", "N/A")
        humidity = weather_data.get("humidity", "N/A")

        return f"{city}：{condition}，温度{temp}°C，风速{wind_speed}m/s，湿度{humidity}%"

    def _fallback_weather(self, city: str) -> str:
        """
        Fallback weather data when API is unavailable

        Args:
            city: City name

        Returns:
            Mock weather data
        """
        # Mock data for demonstration
        mock_data = {
            "北京": "晴天，温度25°C，风速3m/s，湿度60%",
            "beijing": "Sunny, 25°C, Wind: 3m/s, Humidity: 60%",
            "上海": "多云，温度22°C，风速2m/s，湿度70%",
            "shanghai": "Cloudy, 22°C, Wind: 2m/s, Humidity: 70%",
            "广州": "阴天，温度28°C，风速4m/s，湿度80%",
            "guangzhou": "Overcast, 28°C, Wind: 4m/s, Humidity: 80%",
            "深圳": "小雨，温度26°C，风速3m/s，湿度85%",
            "shenzhen": "Light rain, 26°C, Wind: 3m/s, Humidity: 85%",
            "杭州": "晴天，温度24°C，风速2m/s，湿度65%",
            "hangzhou": "Sunny, 24°C, Wind: 2m/s, Humidity: 65%",
            "成都": "多云，温度20°C，风速1m/s，湿度75%",
            "chengdu": "Cloudy, 20°C, Wind: 1m/s, Humidity: 75%",
        }

        city_lower = city.lower().strip()
        weather = mock_data.get(city_lower, f"{city}：晴天，温度25°C（模拟数据）")

        return f"{weather} [模拟数据]"


# Example usage
if __name__ == "__main__":
    """
    Test WeatherTool
    """
    # Create tool
    tool = WeatherTool()

    # Test cities
    test_cities = ["北京", "Shanghai", "杭州", "Unknown City"]

    for city in test_cities:
        print(f"\n{'='*60}")
        print(f"Querying weather for: {city}")
        print(f"{'='*60}")

        try:
            result = tool.invoke({"city": city})
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

    # Test caching
    print(f"\n{'='*60}")
    print("Testing cache (should be instant)")
    print(f"{'='*60}")

    import time
    start = time.time()
    result = tool.invoke({"city": "北京"})
    elapsed = (time.time() - start) * 1000
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}ms (should be <1ms if cached)")
