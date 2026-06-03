"""
天气查询工具
提供实时天气和天气预报功能

工具描述优化技巧：
1. 明确说明工具的用途和适用场景
2. 清楚定义参数格式和示例
3. 描述返回值的结构
4. 添加使用提示和注意事项
"""
from langchain.tools import tool
from typing import Optional
import requests
import os
from datetime import datetime, timedelta


@tool
def query_weather(city: str) -> str:
    """查询指定城市的实时天气信息。

    适用场景：
    - 用户询问某个城市当前的天气情况
    - 需要了解当前温度、天气状况、风力等信息
    - 出差前查看目的地当前天气

    参数说明：
    - city: 城市名称，支持中文（如"北京"）或拼音（如"beijing"）

    返回信息：
    - 天气状况（晴、阴、雨等）
    - 当前温度和体感温度
    - 风向和风力
    - 湿度信息

    示例：
    - query_weather("北京") -> 返回北京实时天气
    - query_weather("上海") -> 返回上海实时天气

    Args:
        city: 城市名称

    Returns:
        格式化的天气信息字符串
    """
    api_key = os.getenv("QWEATHER_API_KEY")

    # 如果没有配置API Key，返回模拟数据
    if not api_key:
        # 模拟真实的天气数据
        mock_data = {
            "北京": ("晴天", "25", "27", "东南风", "3", "45"),
            "上海": ("多云", "28", "30", "东风", "2", "60"),
            "深圳": ("阵雨", "30", "32", "南风", "4", "75"),
            "杭州": ("晴天", "26", "28", "西风", "2", "50"),
        }

        data = mock_data.get(city, ("晴天", "22", "24", "北风", "2", "50"))
        weather, temp, feels_like, wind_dir, wind_scale, humidity = data

        return (
            f"📍 {city}实时天气：\n"
            f"🌤️  天气：{weather}\n"
            f"🌡️  温度：{temp}°C\n"
            f"🤚 体感：{feels_like}°C\n"
            f"💨 风向：{wind_dir} {wind_scale}级\n"
            f"💧 湿度：{humidity}%\n"
            f"ℹ️  (模拟数据，配置QWEATHER_API_KEY获取真实数据)"
        )

    # 调用和风天气API获取真实数据
    try:
        # 1. 获取城市ID
        location_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}"
        location_response = requests.get(location_url, timeout=5)
        location_data = location_response.json()

        if location_data["code"] != "200":
            return f"❌ 无法找到城市：{city}，请检查城市名称是否正确"

        location_id = location_data["location"][0]["id"]

        # 2. 获取实时天气
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()

        if weather_data["code"] != "200":
            return f"❌ 无法获取{city}的天气信息"

        # 3. 格式化天气信息
        now = weather_data["now"]
        return (
            f"📍 {city}实时天气：\n"
            f"🌤️  天气：{now['text']}\n"
            f"🌡️  温度：{now['temp']}°C\n"
            f"🤚 体感：{now['feelsLike']}°C\n"
            f"💨 风向：{now['windDir']} {now['windScale']}级\n"
            f"💧 湿度：{now['humidity']}%\n"
            f"🕐 更新时间：{now['obsTime']}"
        )

    except requests.Timeout:
        return f"⏱️  查询{city}天气超时，请稍后重试"
    except Exception as e:
        return f"❌ 查询{city}天气时出错：{str(e)}"


@tool
def get_weather_forecast(city: str, days: Optional[int] = 3) -> str:
    """查询指定城市未来几天的天气预报。

    适用场景：
    - 用户需要规划未来几天的行程
    - 出差前查看目的地未来天气趋势
    - 决定是否需要带雨具或换季衣物

    参数说明：
    - city: 城市名称，支持中文（如"北京"）或拼音
    - days: 预报天数，默认3天，最多7天

    返回信息：
    - 每天的日期和星期
    - 白天和夜间天气状况
    - 最高温度和最低温度
    - 降水概率
    - 风力信息

    示例：
    - get_weather_forecast("北京") -> 返回北京未来3天天气
    - get_weather_forecast("上海", 7) -> 返回上海未来7天天气

    Args:
        city: 城市名称
        days: 预报天数，默认3天

    Returns:
        格式化的天气预报字符串
    """
    api_key = os.getenv("QWEATHER_API_KEY")

    # 限制天数范围
    days = max(1, min(days or 3, 7))

    # 如果没有配置API Key，返回模拟数据
    if not api_key:
        today = datetime.now()
        forecast_lines = [f"📅 {city}未来{days}天天气预报：\n"]

        mock_forecasts = [
            ("晴天", "28", "18", "10"),
            ("多云", "26", "17", "20"),
            ("阵雨", "24", "19", "60"),
            ("阴天", "25", "18", "30"),
            ("晴天", "27", "19", "10"),
            ("多云", "26", "18", "20"),
            ("晴天", "28", "19", "10"),
        ]

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.strftime("%m月%d日")
            weekday = weekdays[date.weekday()]
            weather, temp_max, temp_min, pop = mock_forecasts[i]

            forecast_lines.append(
                f"\n📆 {date_str} {weekday}\n"
                f"   🌤️  天气：{weather}\n"
                f"   🌡️  温度：{temp_min}°C ~ {temp_max}°C\n"
                f"   ☔ 降水：{pop}%"
            )

        forecast_lines.append("\nℹ️  (模拟数据，配置QWEATHER_API_KEY获取真实数据)")
        return "".join(forecast_lines)

    # 调用和风天气API获取真实数据
    try:
        # 1. 获取城市ID
        location_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}"
        location_response = requests.get(location_url, timeout=5)
        location_data = location_response.json()

        if location_data["code"] != "200":
            return f"❌ 无法找到城市：{city}"

        location_id = location_data["location"][0]["id"]

        # 2. 获取天气预报（7天）
        forecast_url = f"https://devapi.qweather.com/v7/weather/{days}d?location={location_id}&key={api_key}"
        forecast_response = requests.get(forecast_url, timeout=5)
        forecast_data = forecast_response.json()

        if forecast_data["code"] != "200":
            return f"❌ 无法获取{city}的天气预报"

        # 3. 格式化预报信息
        forecast_lines = [f"📅 {city}未来{days}天天气预报：\n"]

        for daily in forecast_data["daily"][:days]:
            date = datetime.strptime(daily["fxDate"], "%Y-%m-%d")
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            weekday = weekdays[date.weekday()]

            forecast_lines.append(
                f"\n📆 {date.strftime('%m月%d日')} {weekday}\n"
                f"   🌤️  白天：{daily['textDay']}  夜间：{daily['textNight']}\n"
                f"   🌡️  温度：{daily['tempMin']}°C ~ {daily['tempMax']}°C\n"
                f"   ☔ 降水：{daily.get('precip', '0')}mm\n"
                f"   💨 风力：{daily['windDirDay']} {daily['windScaleDay']}级"
            )

        return "".join(forecast_lines)

    except requests.Timeout:
        return f"⏱️  查询{city}天气预报超时，请稍后重试"
    except Exception as e:
        return f"❌ 查询{city}天气预报时出错：{str(e)}"


# 工具列表（用于Agent注册）
def get_all_weather_tools():
    """获取所有天气相关工具"""
    return [query_weather, get_weather_forecast]


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试天气查询工具模块")
    print("=" * 60)

    # 测试1：查询实时天气
    print("\n【测试1】查询北京实时天气")
    print("-" * 60)
    result1 = query_weather.invoke({"city": "北京"})
    print(result1)

    # 测试2：查询天气预报
    print("\n【测试2】查询上海未来3天天气预报")
    print("-" * 60)
    result2 = get_weather_forecast.invoke({"city": "上海", "days": 3})
    print(result2)

    # 测试3：查询7天预报
    print("\n【测试3】查询深圳未来7天天气预报")
    print("-" * 60)
    result3 = get_weather_forecast.invoke({"city": "深圳", "days": 7})
    print(result3)

    # 查看工具元数据
    print("\n【工具信息】")
    print("-" * 60)
    print(f"工具1名称：{query_weather.name}")
    print(f"工具1描述：{query_weather.description[:50]}...")
    print(f"工具2名称：{get_weather_forecast.name}")
    print(f"工具2描述：{get_weather_forecast.description[:50]}...")

    print("\n" + "=" * 60)
    print("✅ 天气工具测试完成")
    print("=" * 60)
