"""
??????? API ???

???
- ?? API Host ???
- ???? X-QW-Api-Key ??
- ???????????? Geo API
- ???? + ????

?????https://dev.qweather.com/docs/
"""

import os
import logging
from urllib.parse import quote
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ???? ? ?? location ID ??
CITY_MAP = {
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
    "南京": "101190101",
    "nanjing": "101190101",
    "武汉": "101200101",
    "wuhan": "101200101",
    "西安": "101110101",
    "xian": "101110101",
    "重庆": "101040100",
    "chongqing": "101040100",
    "苏州": "101190401",
    "suzhou": "101190401",
    "天津": "101030100",
    "tianjin": "101030100",
    "长沙": "101250101",
    "changsha": "101250101",
    "青岛": "101120201",
    "qingdao": "101120201",
    "大连": "101070201",
    "dalian": "101070201",
    "厦门": "101230201",
    "xiamen": "101230201",
    "昆明": "101290101",
    "kunming": "101290101",
    "沈阳": "101070101",
    "shenyang": "101070101",
    "济南": "101120101",
    "jinan": "101120101",
    "哈尔滨": "101050101",
    "haerbin": "101050101",
}


class QWeatherClient:
    """???? API ???"""

    def __init__(self, api_key: Optional[str] = None, api_host: Optional[str] = None):
        self.api_key = api_key or os.getenv("QWEATHER_API_KEY", "")
        self.api_host = api_host or os.getenv("QWEATHER_API_HOST", "")

        if not self.api_key:
            logger.warning("QWEATHER_API_KEY ???")
        if not self.api_host:
            logger.warning("QWEATHER_API_HOST ???")

    @property
    def _headers(self) -> dict:
        return {
            "X-QW-Api-Key": self.api_key,
            "Accept-Encoding": "gzip",
        }

    def _url(self, path: str) -> str:
        return f"https://{self.api_host}{path}"

    # ?? ???? ??

    def lookup_city(self, city: str) -> Optional[str]:
        """??????? location ID"""
        key = city.strip().lower()
        # ??????
        if key in CITY_MAP:
            return CITY_MAP[key]
        # ??? API ???Geo API?????????
        try:
            url = self._url(f"/geo/v2/city/lookup?location={city}&range=cn&number=1")
            resp = requests.get(url, headers=self._headers, timeout=5)
            data = resp.json()
            if data.get("code") == "200" and data.get("location"):
                return data["location"][0]["id"]
        except Exception:
            pass
        return None

    # ?? ???? ??

    def get_now(self, location_id: str) -> Optional[dict]:
        url = self._url(f"/v7/weather/now?location={location_id}")
        resp = requests.get(url, headers=self._headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "200":
            return None
        return data.get("now")

    # ?? ???? ??

    def get_forecast(self, location_id: str, days: int = 3) -> Optional[list]:
        days = max(1, min(days, 7))
        url = self._url(f"/v7/weather/{days}d?location={location_id}")
        resp = requests.get(url, headers=self._headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "200":
            return None
        return data.get("daily")

    # ?? ???? ??

    def weather_by_city(self, city: str) -> Optional[dict]:
        location_id = self.lookup_city(city)
        if not location_id:
            return None
        return self.get_now(location_id)

    def forecast_by_city(self, city: str, days: int = 3) -> Optional[list]:
        location_id = self.lookup_city(city)
        if not location_id:
            return None
        return self.get_forecast(location_id, days)

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key and self.api_host)


_client: Optional[QWeatherClient] = None


def get_qweather_client() -> QWeatherClient:
    global _client
    if _client is None:
        _client = QWeatherClient()
    return _client
