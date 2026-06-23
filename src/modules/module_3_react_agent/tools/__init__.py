"""
ReAct Agent Tools

Collection of tools for the ReAct agent including weather, flight, and hotel search.
"""
from .weather import query_weather, get_weather_forecast
from .flight import search_flights, get_flight_price
from .hotel import search_hotels, get_hotel_details

__version__ = "0.1.0"


def get_all_tools():
    """获取所有可用工具"""
    return [
        query_weather,
        get_weather_forecast,
        search_flights,
        get_flight_price,
        search_hotels,
        get_hotel_details,
    ]
