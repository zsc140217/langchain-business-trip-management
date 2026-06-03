"""
航班查询工具（模拟API）
模拟携程、去哪儿等航班查询平台的API

工具描述优化：
1. 明确说明这是模拟数据
2. 清楚定义参数格式（城市名、日期格式）
3. 说明返回的航班信息结构
4. 添加排序和筛选规则
"""
from langchain.tools import tool
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import random


# 模拟航班数据库
MOCK_FLIGHTS = {
    ("北京", "上海"): [
        {"flight_no": "CA1501", "airline": "国航", "departure": "07:30", "arrival": "10:00", "duration": "2h30m", "price": 850, "seat_class": "经济舱"},
        {"flight_no": "MU5101", "airline": "东航", "departure": "09:15", "arrival": "11:45", "duration": "2h30m", "price": 780, "seat_class": "经济舱"},
        {"flight_no": "CZ3001", "airline": "南航", "departure": "13:20", "arrival": "15:50", "duration": "2h30m", "price": 920, "seat_class": "经济舱"},
        {"flight_no": "HU7601", "airline": "海航", "departure": "18:45", "arrival": "21:15", "duration": "2h30m", "price": 680, "seat_class": "经济舱"},
    ],
    ("上海", "北京"): [
        {"flight_no": "CA1502", "airline": "国航", "departure": "08:00", "arrival": "10:30", "duration": "2h30m", "price": 880, "seat_class": "经济舱"},
        {"flight_no": "MU5102", "airline": "东航", "departure": "12:30", "arrival": "15:00", "duration": "2h30m", "price": 820, "seat_class": "经济舱"},
        {"flight_no": "CZ3002", "airline": "南航", "departure": "16:10", "arrival": "18:40", "duration": "2h30m", "price": 950, "seat_class": "经济舱"},
    ],
    ("北京", "深圳"): [
        {"flight_no": "CA1301", "airline": "国航", "departure": "08:30", "arrival": "12:00", "duration": "3h30m", "price": 1200, "seat_class": "经济舱"},
        {"flight_no": "CZ3101", "airline": "南航", "departure": "14:20", "arrival": "17:50", "duration": "3h30m", "price": 1150, "seat_class": "经济舱"},
        {"flight_no": "HU7701", "airline": "海航", "departure": "19:00", "arrival": "22:30", "duration": "3h30m", "price": 980, "seat_class": "经济舱"},
    ],
    ("深圳", "北京"): [
        {"flight_no": "CA1302", "airline": "国航", "departure": "07:45", "arrival": "11:15", "duration": "3h30m", "price": 1250, "seat_class": "经济舱"},
        {"flight_no": "CZ3102", "airline": "南航", "departure": "13:15", "arrival": "16:45", "duration": "3h30m", "price": 1180, "seat_class": "经济舱"},
    ],
    ("北京", "杭州"): [
        {"flight_no": "CA1801", "airline": "国航", "departure": "09:00", "arrival": "11:20", "duration": "2h20m", "price": 750, "seat_class": "经济舱"},
        {"flight_no": "MU5201", "airline": "东航", "departure": "15:30", "arrival": "17:50", "duration": "2h20m", "price": 680, "seat_class": "经济舱"},
    ],
    ("上海", "深圳"): [
        {"flight_no": "MU5301", "airline": "东航", "departure": "10:30", "arrival": "13:10", "duration": "2h40m", "price": 980, "seat_class": "经济舱"},
        {"flight_no": "CZ3201", "airline": "南航", "departure": "16:45", "arrival": "19:25", "duration": "2h40m", "price": 920, "seat_class": "经济舱"},
    ],
}


@tool
def search_flights(departure_city: str, arrival_city: str, date: Optional[str] = None) -> str:
    """搜索指定日期从出发城市到目的地城市的所有可用航班。

    适用场景：
    - 用户需要查询两个城市之间的航班信息
    - 规划出差行程，选择合适的出发时间
    - 对比不同航空公司的价格和时刻

    参数说明：
    - departure_city: 出发城市名称（如"北京"、"上海"）
    - arrival_city: 到达城市名称（如"深圳"、"杭州"）
    - date: 出发日期，格式为YYYY-MM-DD（如"2024-06-15"），不填则为今天

    返回信息：
    - 航班号和航空公司
    - 起飞和到达时间
    - 飞行时长
    - 经济舱价格
    - 按价格从低到高排序

    注意事项：
    - 这是模拟数据，实际使用需要对接真实航班API
    - 价格仅供参考，不包含税费
    - 如果没有直飞航班，会提示"无可用航班"

    示例：
    - search_flights("北京", "上海") -> 返回今天北京到上海的所有航班
    - search_flights("上海", "深圳", "2024-06-15") -> 返回指定日期的航班

    Args:
        departure_city: 出发城市
        arrival_city: 到达城市
        date: 出发日期，可选

    Returns:
        格式化的航班列表字符串
    """
    # 处理日期
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 验证日期格式
    try:
        flight_date = datetime.strptime(date, "%Y-%m-%d")
        if flight_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return f"❌ 无法查询过去的日期：{date}"
    except ValueError:
        return f"❌ 日期格式错误，请使用YYYY-MM-DD格式（如2024-06-15）"

    # 查询航班
    route_key = (departure_city, arrival_city)
    flights = MOCK_FLIGHTS.get(route_key, [])

    if not flights:
        return (
            f"❌ 抱歉，暂无{departure_city}到{arrival_city}的直飞航班\n"
            f"建议：\n"
            f"1. 尝试查询其他日期\n"
            f"2. 考虑中转航班\n"
            f"3. 查询邻近城市的航班"
        )

    # 按价格排序
    sorted_flights = sorted(flights, key=lambda x: x["price"])

    # 格式化输出
    result_lines = [
        f"✈️  {departure_city} → {arrival_city} 航班查询结果",
        f"📅 日期：{date}",
        f"🔢 共找到 {len(sorted_flights)} 个航班\n"
    ]

    for idx, flight in enumerate(sorted_flights, 1):
        result_lines.append(
            f"【航班{idx}】\n"
            f"  ✈️  {flight['flight_no']} - {flight['airline']}\n"
            f"  🕐 {flight['departure']} → {flight['arrival']} ({flight['duration']})\n"
            f"  💰 ¥{flight['price']} ({flight['seat_class']})\n"
        )

    result_lines.append("ℹ️  (模拟数据，实际价格以航司官网为准)")

    return "\n".join(result_lines)


@tool
def get_flight_price(departure_city: str, arrival_city: str, flight_class: Optional[str] = "经济舱") -> str:
    """查询指定航线的价格区间和推荐航班。

    适用场景：
    - 用户想了解某条航线的大致价格
    - 预算规划，查看价格范围
    - 快速获取最便宜和最贵的航班信息

    参数说明：
    - departure_city: 出发城市名称
    - arrival_city: 到达城市名称
    - flight_class: 舱位等级，可选"经济舱"、"商务舱"、"头等舱"，默认"经济舱"

    返回信息：
    - 价格区间（最低价-最高价）
    - 最便宜的航班推荐
    - 平均价格
    - 价格趋势提示

    注意事项：
    - 价格会根据季节、节假日波动
    - 提前预订通常有更优惠的价格
    - 商务舱和头等舱价格约为经济舱的2-5倍

    示例：
    - get_flight_price("北京", "上海") -> 返回北京到上海经济舱的价格信息
    - get_flight_price("北京", "深圳", "商务舱") -> 返回商务舱价格

    Args:
        departure_city: 出发城市
        arrival_city: 到达城市
        flight_class: 舱位等级

    Returns:
        格式化的价格信息字符串
    """
    # 查询航班
    route_key = (departure_city, arrival_city)
    flights = MOCK_FLIGHTS.get(route_key, [])

    if not flights:
        return f"❌ 抱歉，暂无{departure_city}到{arrival_city}的航班信息"

    # 根据舱位调整价格
    class_multiplier = {
        "经济舱": 1.0,
        "商务舱": 2.5,
        "头等舱": 4.5,
    }
    multiplier = class_multiplier.get(flight_class, 1.0)

    # 计算价格统计
    prices = [f["price"] * multiplier for f in flights]
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)

    # 找到最便宜的航班
    cheapest_idx = prices.index(min_price)
    cheapest_flight = flights[cheapest_idx]

    # 价格趋势（模拟）
    today_weekday = datetime.now().weekday()
    if today_weekday in [4, 5, 6]:  # 周五、周六、周日
        trend = "📈 周末价格通常较高，建议工作日出行可节省10-20%"
    else:
        trend = "📊 工作日价格适中，提前7天预订可享受更多优惠"

    return (
        f"💰 {departure_city} → {arrival_city} 价格查询\n"
        f"🎫 舱位：{flight_class}\n\n"
        f"💵 价格区间：¥{int(min_price)} - ¥{int(max_price)}\n"
        f"📊 平均价格：¥{int(avg_price)}\n\n"
        f"🏆 最优推荐：\n"
        f"  ✈️  {cheapest_flight['flight_no']} - {cheapest_flight['airline']}\n"
        f"  🕐 {cheapest_flight['departure']} → {cheapest_flight['arrival']}\n"
        f"  💰 ¥{int(min_price)}\n\n"
        f"{trend}\n\n"
        f"💡 省钱技巧：\n"
        f"  • 提前7-14天预订通常更便宜\n"
        f"  • 避开节假日高峰期\n"
        f"  • 选择早班或晚班航班\n"
        f"  • 关注航司会员日促销\n\n"
        f"ℹ️  (模拟数据，实际价格以航司官网为准)"
    )


# 工具列表（用于Agent注册）
def get_all_flight_tools():
    """获取所有航班相关工具"""
    return [search_flights, get_flight_price]


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试航班查询工具模块")
    print("=" * 60)

    # 测试1：搜索航班
    print("\n【测试1】搜索北京到上海的航班")
    print("-" * 60)
    result1 = search_flights.invoke({
        "departure_city": "北京",
        "arrival_city": "上海"
    })
    print(result1)

    # 测试2：查询价格
    print("\n【测试2】查询北京到深圳的价格")
    print("-" * 60)
    result2 = get_flight_price.invoke({
        "departure_city": "北京",
        "arrival_city": "深圳"
    })
    print(result2)

    # 测试3：指定日期搜索
    print("\n【测试3】搜索指定日期的航班")
    print("-" * 60)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    result3 = search_flights.invoke({
        "departure_city": "上海",
        "arrival_city": "深圳",
        "date": tomorrow
    })
    print(result3)

    # 测试4：查询商务舱价格
    print("\n【测试4】查询商务舱价格")
    print("-" * 60)
    result4 = get_flight_price.invoke({
        "departure_city": "北京",
        "arrival_city": "上海",
        "flight_class": "商务舱"
    })
    print(result4)

    # 测试5：无可用航班
    print("\n【测试5】查询无可用航班的路线")
    print("-" * 60)
    result5 = search_flights.invoke({
        "departure_city": "北京",
        "arrival_city": "拉萨"
    })
    print(result5)

    # 查看工具元数据
    print("\n【工具信息】")
    print("-" * 60)
    print(f"工具1：{search_flights.name}")
    print(f"描述：{search_flights.description[:50]}...")
    print(f"\n工具2：{get_flight_price.name}")
    print(f"描述：{get_flight_price.description[:50]}...")

    print("\n" + "=" * 60)
    print("✅ 航班工具测试完成")
    print("=" * 60)
