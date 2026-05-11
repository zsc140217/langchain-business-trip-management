"""
天气查询工具
使用和风天气API查询天气信息

对应Spring AI的：
@Bean
public FunctionCallback weatherTool() {
    return FunctionCallback.builder()
        .function("queryWeather", (String city) -> {...})
        .description("查询天气")
        .build();
}
"""
from langchain.tools import tool
import requests
import os


@tool
def query_weather(city: str) -> str:
    """
    查询指定城市的天气信息

    这是LangChain的Tool（工具）概念

    什么是Tool？
    - 让LLM能调用外部功能（API、数据库、计算等）
    - LLM根据用户问题决定是否调用工具
    - 工具返回结果后，LLM继续生成回答

    @tool装饰器的作用：
    - 把普通函数变成LangChain工具
    - 自动从函数签名提取参数信息
    - 自动从docstring提取工具描述

    对比Spring AI：
    - Spring AI用FunctionCallback.builder()
    - LangChain用@tool装饰器
    - LangChain更简洁，Spring AI更类型安全

    工作流程：
    1. 用户问："北京天气怎么样？"
    2. LLM识别需要调用query_weather工具
    3. LLM提取参数：city="北京"
    4. 调用工具，获取天气信息
    5. LLM根据天气信息生成回答

    Args:
        city: 城市名称，如"北京"、"上海"

    Returns:
        天气信息字符串
    """
    api_key = os.getenv("QWEATHER_API_KEY")

    # 如果没有配置API Key，返回模拟数据
    if not api_key:
        return f"{city}的天气信息：晴天，25°C（模拟数据，请配置QWEATHER_API_KEY获取真实数据）"

    # 调用和风天气API
    try:
        # 1. 获取城市ID
        # 和风天气需要先通过城市名获取location_id
        location_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}"
        location_response = requests.get(location_url, timeout=5)
        location_data = location_response.json()

        if location_data["code"] != "200":
            return f"无法找到城市：{city}"

        location_id = location_data["location"][0]["id"]

        # 2. 获取实时天气
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()

        if weather_data["code"] != "200":
            return f"无法获取{city}的天气信息"

        # 3. 格式化天气信息
        now = weather_data["now"]
        return (
            f"{city}天气：{now['text']}，"
            f"温度{now['temp']}°C，"
            f"体感温度{now['feelsLike']}°C，"
            f"风向{now['windDir']}，"
            f"风力{now['windScale']}级"
        )

    except requests.Timeout:
        return f"查询{city}天气超时，请稍后重试"
    except Exception as e:
        return f"查询{city}天气时出错：{str(e)}"


@tool
def compare_weather(city1: str, city2: str) -> str:
    """
    对比两个城市的天气

    这是一个组合工具的例子
    - 内部调用query_weather两次
    - 展示了工具可以调用其他工具

    Args:
        city1: 第一个城市
        city2: 第二个城市

    Returns:
        对比结果
    """
    # 注意：这里要用.invoke()而不是直接调用
    # 因为@tool装饰后，函数变成了Tool对象
    weather1 = query_weather.invoke({"city": city1})
    weather2 = query_weather.invoke({"city": city2})

    return f"天气对比：\n{weather1}\n{weather2}"


# 获取所有工具的列表（用于Agent）
def get_weather_tools():
    """
    获取天气相关的所有工具

    在创建Agent时需要传入工具列表

    Returns:
        工具列表
    """
    return [query_weather, compare_weather]


# 测试代码
if __name__ == "__main__":
    """
    测试天气工具
    """
    print("测试天气工具模块...\n")

    # 测试单城市查询
    print("1️⃣ 测试单城市查询")
    result1 = query_weather.invoke({"city": "北京"})
    print(f"结果：{result1}\n")

    # 测试多城市对比
    print("2️⃣ 测试多城市对比")
    result2 = compare_weather.invoke({"city1": "北京", "city2": "上海"})
    print(f"结果：{result2}\n")

    # 查看工具信息
    print("3️⃣ 工具信息")
    print(f"工具名称：{query_weather.name}")
    print(f"工具描述：{query_weather.description}")
    print(f"工具参数：{query_weather.args}")

    print("\n✅ 天气工具测试完成！")
    print("\n💡 提示：")
    print("- 如果看到'模拟数据'，说明未配置QWEATHER_API_KEY")
    print("- 配置后可获取真实天气数据")
    print("- 申请地址：https://dev.qweather.com/")
