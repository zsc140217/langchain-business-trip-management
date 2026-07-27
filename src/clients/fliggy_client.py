"""
飞猪AI客户端封装
通过CLI命令调用飞猪AI API进行酒店和航班搜索
"""
import subprocess
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FliggyClient:
    """飞猪AI客户端"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化飞猪AI客户端

        Args:
            api_key: 飞猪AI API密钥，如果为None则从环境变量读取
        """
        self.api_key = api_key or os.getenv("FLYAI_API_KEY")
        self.call_count = 0
        self.max_calls = 5000  # 免费额度
        self._is_configured = False

        if self.api_key:
            self._configure_api_key()

    def _configure_api_key(self) -> bool:
        """配置飞猪AI的API密钥"""
        try:
            result = subprocess.run(
                ["flyai", "config", "set", "FLYAI_API_KEY", self.api_key],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self._is_configured = True
                logger.info("FlyAI API key configured successfully")
                return True
            else:
                logger.error(f"Failed to configure FlyAI API key: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.error("flyai CLI not found. Please install: npm install -g @clawhub/cli && clawhub install flyai")
            return False
        except Exception as e:
            logger.error(f"Error configuring FlyAI: {e}")
            return False

    def is_available(self) -> bool:
        """检查飞猪AI是否可用"""
        if not self.api_key:
            return False

        # 检查flyai命令是否存在
        try:
            result = subprocess.run(
                ["flyai", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def search_hotels(
        self,
        city: str,
        checkin: str,
        checkout: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_star: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索酒店

        Args:
            city: 城市名称（中文全称，如"北京"）
            checkin: 入住日期（格式：YYYY-MM-DD，必须是未来日期）
            checkout: 退房日期（格式：YYYY-MM-DD）
            min_price: 最低价格
            max_price: 最高价格
            min_star: 最低星级

        Returns:
            酒店列表
        """
        # 验证日期格式和未来日期
        try:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
            today = datetime.now()

            if checkin_date.date() < today.date():
                logger.warning(f"Checkin date {checkin} is in the past")
                return []

            if checkout_date <= checkin_date:
                logger.warning("Checkout date must be after checkin date")
                return []
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return []

        # 构建查询
        query = f"{city}的酒店，入住{checkin}，退房{checkout}"

        if min_price and max_price:
            query += f"，价格{min_price}-{max_price}元"
        elif min_price:
            query += f"，价格{min_price}元以上"
        elif max_price:
            query += f"，价格{max_price}元以下"

        if min_star:
            query += f"，{min_star}星级以上"

        logger.info(f"Searching hotels with query: {query}")

        result = self._execute_flyai_command(query)
        if result:
            return self._parse_hotel_results(result)
        return []

    def search_flights(
        self,
        origin: str,
        destination: str,
        date: str,
        flight_class: str = "经济舱"
    ) -> List[Dict[str, Any]]:
        """
        搜索航班

        Args:
            origin: 出发城市（中文全称）
            destination: 到达城市（中文全称）
            date: 出发日期（格式：YYYY-MM-DD，必须是未来日期）
            flight_class: 舱位（经济舱/商务舱/头等舱）

        Returns:
            航班列表
        """
        # 验证日期
        try:
            flight_date = datetime.strptime(date, "%Y-%m-%d")
            if flight_date.date() < datetime.now().date():
                logger.warning(f"Flight date {date} is in the past")
                return []
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return []

        query = f"从{origin}到{destination}的航班，{date}"
        if flight_class != "经济舱":
            query += f"，{flight_class}"

        logger.info(f"Searching flights with query: {query}")

        result = self._execute_flyai_command(query)
        if result:
            return self._parse_flight_results(result)
        return []

    def _execute_flyai_command(self, query: str, command: str = "keyword-search") -> Optional[str]:
        """执行flyai命令"""
        # 检查调用次数
        if self.call_count >= self.max_calls:
            logger.warning(f"FlyAI quota exceeded ({self.max_calls} calls)")
            return None

        try:
            result = subprocess.run(
                ["flyai", command, "--query", query],
                capture_output=True,
                text=True,
                timeout=30
            )

            # FlyAI CLI 有时会有退出码127但仍然返回数据
            if result.stdout:
                self.call_count += 1
                logger.info(f"FlyAI API call successful (count: {self.call_count}/{self.max_calls})")
                return result.stdout
            else:
                logger.error(f"FlyAI command failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("FlyAI request timeout")
            return None
        except FileNotFoundError:
            logger.error("flyai CLI not found")
            return None
        except Exception as e:
            logger.error(f"Error executing FlyAI command: {e}")
            return None

    def _parse_hotel_results(self, raw_result: str) -> List[Dict[str, Any]]:
        """
        解析酒店搜索结果

        飞猪API返回格式：
        {
          "data": {
            "itemList": [
              {
                "info": {
                  "title": "酒店名称",
                  "star": "2",
                  "price": null,
                  "rate": null,
                  "jumpUrl": "https://..."
                }
              }
            ]
          },
          "status": 0,
          "message": "success"
        }
        """
        hotels = []

        try:
            data = json.loads(raw_result)

            # 检查状态码
            if data.get("status") != 0:
                logger.warning(f"FlyAI API returned non-zero status: {data.get('message')}")
                return []

            # 提取itemList
            item_list = data.get("data", {}).get("itemList", [])

            for item in item_list:
                info = item.get("info", {})
                if info.get("title"):  # 确保有标题
                    hotels.append(info)

            logger.info(f"Parsed {len(hotels)} hotels from FlyAI response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw result: {raw_result[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing hotel results: {e}")
            return []

        # 标准化格式
        return [self._normalize_hotel(h) for h in hotels if h]

    def _parse_flight_results(self, raw_result: str) -> List[Dict[str, Any]]:
        """解析航班搜索结果（格式同酒店）"""
        flights = []

        try:
            data = json.loads(raw_result)

            # 检查状态码
            if data.get("status") != 0:
                logger.warning(f"FlyAI API returned non-zero status: {data.get('message')}")
                return []

            # 提取itemList
            item_list = data.get("data", {}).get("itemList", [])

            for item in item_list:
                info = item.get("info", {})
                if info.get("title"):  # 确保有标题
                    flights.append(info)

            logger.info(f"Parsed {len(flights)} flights from FlyAI response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw result: {raw_result[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing flight results: {e}")
            return []

        # 标准化格式
        return [self._normalize_flight(f) for f in flights if f]

    def _parse_hotel_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中解析酒店信息（简单实现）"""
        # TODO: 根据飞猪AI实际返回格式实现
        logger.debug(f"Raw hotel text: {text[:200]}...")
        return []

    def _parse_flight_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中解析航班信息（简单实现）"""
        # TODO: 根据飞猪AI实际返回格式实现
        logger.debug(f"Raw flight text: {text[:200]}...")
        return []

    def _normalize_hotel(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化酒店数据格式

        飞猪API字段: title, star, price, rate, jumpUrl, picUrl
        标准格式: name, star, price, rating, address, facilities, jumpUrl
        """
        # 尝试从price字段提取数字，如果为null则默认0
        price_value = 0
        if hotel.get("price"):
            try:
                price_value = int(float(hotel["price"]))
            except (ValueError, TypeError):
                price_value = 0

        # 评分可能为null
        rating_value = 0
        if hotel.get("rate"):
            try:
                rating_value = float(hotel["rate"])
            except (ValueError, TypeError):
                rating_value = 0

        # 星级转换为整数
        star_value = 0
        if hotel.get("star"):
            try:
                star_value = int(hotel["star"])
            except (ValueError, TypeError):
                star_value = 0

        return {
            "name": hotel.get("title", ""),
            "star": star_value,
            "price": price_value,
            "rating": rating_value,
            "address": hotel.get("address", ""),
            "facilities": hotel.get("facilities", hotel.get("tags", [])) or [],
            "jumpUrl": hotel.get("jumpUrl", ""),
            "picUrl": hotel.get("picUrl", "")
        }

    def _normalize_flight(self, flight: Dict[str, Any]) -> Dict[str, Any]:
        """标准化航班数据格式"""
        return {
            "flight_no": flight.get("flight_no", flight.get("flightNo", "")),
            "airline": flight.get("airline", flight.get("airlineName", "")),
            "departure": flight.get("departure", flight.get("departTime", "")),
            "arrival": flight.get("arrival", flight.get("arriveTime", "")),
            "duration": flight.get("duration", ""),
            "price": flight.get("price", flight.get("lowestPrice", 0)),
            "jumpUrl": flight.get("jumpUrl", flight.get("url", ""))  # 飞猪详情页链接
        }

    def get_quota_info(self) -> Dict[str, Any]:
        """获取配额使用情况"""
        return {
            "used": self.call_count,
            "total": self.max_calls,
            "remaining": self.max_calls - self.call_count,
            "percentage": (self.call_count / self.max_calls * 100) if self.max_calls > 0 else 0
        }
