"""
Weather Tool
Query real-time weather information using QWeather API (header-based auth)

Features:
- Real-time weather data
- 7-day forecast
- Weather alerts
- Caching (30-minute TTL)
- Fallback to mock data if API fails
"""
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from src.tools.qweather_client import get_qweather_client, QWeatherClient
import logging

logger = logging.getLogger(__name__)


class WeatherTool(BaseTool):
    """
    Weather query tool using QWeather API

    Example:
        tool = WeatherTool()
        result = tool.invoke({"city": "Beijing"})
    """

    name: str = "query_weather"
    description: str = """Query real-time weather information for a city.

    Input should be a dictionary with:
    - city (str): City name in Chinese or English (e.g., "??", "Beijing", "Shanghai")

    Returns weather information including:
    - Temperature
    - Weather condition (sunny, cloudy, rainy, etc.)
    - Wind speed
    - Humidity
    """

    cache_enabled: bool = True
    cache_ttl_seconds: int = 1800
    max_retries: int = 2
    timeout_seconds: float = 5.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def city_mapping(self) -> Dict[str, str]:
        """City name to location ID mapping (fallback when API unreachable)"""
        return {
            "??": "101010100",
            "beijing": "101010100",
            "??": "101020100",
            "shanghai": "101020100",
            "??": "101280101",
            "guangzhou": "101280101",
            "??": "101280601",
            "shenzhen": "101280601",
            "??": "101210101",
            "hangzhou": "101210101",
            "??": "101270101",
            "chengdu": "101270101",
        }

    def _run(self, city: str) -> str:
        if not city:
            raise ValueError("City parameter is required")

        logger.info(f"Querying weather for: {city}")

        client = get_qweather_client()

        if client.is_ready:
            try:
                now = client.weather_by_city(city)
                if now:
                    return (
                        f"{city}?{now['text']}?"
                        f"??{now['temp']}?C?"
                        f"??{now['feelsLike']}?C?"
                        f"??{now['windDir']}?"
                        f"??{now['windScale']}?"
                    )
            except Exception as e:
                logger.warning(f"QWeather API failed, falling back: {e}")

        return self._fallback_weather(city)

    def _fallback_weather(self, city: str) -> str:
        mock_data = {
            "??": "?????25?C???3m/s???60%",
            "beijing": "Sunny, 25?C, Wind: 3m/s, Humidity: 60%",
            "??": "?????22?C???2m/s???70%",
            "shanghai": "Cloudy, 22?C, Wind: 2m/s, Humidity: 70%",
            "??": "?????28?C???4m/s???80%",
            "guangzhou": "Overcast, 28?C, Wind: 4m/s, Humidity: 80%",
            "??": "?????26?C???3m/s???85%",
            "shenzhen": "Light rain, 26?C, Wind: 3m/s, Humidity: 85%",
            "??": "?????24?C???2m/s???65%",
            "hangzhou": "Sunny, 24?C, Wind: 2m/s, Humidity: 65%",
            "??": "?????20?C???1m/s???75%",
            "chengdu": "Cloudy, 20?C, Wind: 1m/s, Humidity: 75%",
        }
        city_lower = city.lower().strip()
        weather = mock_data.get(city_lower, f"{city}??????25?C??????")
        return f"{weather} [????]"


if __name__ == "__main__":
    tool = WeatherTool()
    for city in ["??", "Shanghai", "??", "Unknown City"]:
        print(f"\n{'='*60}")
        print(f"Querying weather for: {city}")
        try:
            result = tool.invoke({"city": city})
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
