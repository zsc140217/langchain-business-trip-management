"""
酒店查询工具（模拟API）
模拟携程、去哪儿等酒店预订平台的API

工具描述优化：
1. 详细说明酒店查询的功能和适用场景
2. 清楚定义参数（城市、价格范围、星级）
3. 说明返回的酒店信息结构
4. 添加筛选和排序逻辑
"""
from langchain.tools import tool
from typing import Optional, List, Dict
import random


# 模拟酒店数据库
MOCK_HOTELS = {
    "北京": [
        {"name": "北京希尔顿酒店", "star": 5, "price": 800, "rating": 4.7, "address": "朝阳区东三环北路", "facilities": ["WiFi", "健身房", "游泳池", "商务中心"]},
        {"name": "北京万豪酒店", "star": 5, "price": 750, "rating": 4.6, "address": "朝阳区建国路", "facilities": ["WiFi", "健身房", "餐厅", "会议室"]},
        {"name": "北京诺富特酒店", "star": 4, "price": 450, "rating": 4.3, "address": "海淀区知春路", "facilities": ["WiFi", "健身房", "餐厅"]},
        {"name": "北京如家酒店", "star": 3, "price": 280, "rating": 4.2, "address": "西城区金融街", "families": ["WiFi", "早餐"]},
        {"name": "北京汉庭酒店", "star": 3, "price": 250, "rating": 4.0, "address": "东城区王府井", "facilities": ["WiFi"]},
    ],
    "上海": [
        {"name": "上海浦东香格里拉酒店", "star": 5, "price": 1200, "rating": 4.8, "address": "浦东新区陆家嘴", "facilities": ["WiFi", "健身房", "游泳池", "SPA", "商务中心"]},
        {"name": "上海锦江饭店", "star": 5, "price": 900, "rating": 4.5, "address": "黄浦区茂名南路", "facilities": ["WiFi", "健身房", "餐厅", "会议室"]},
        {"name": "上海亚朵酒店", "star": 4, "price": 500, "rating": 4.4, "address": "徐汇区漕溪北路", "facilities": ["WiFi", "健身房", "图书馆"]},
        {"name": "上海桔子酒店", "star": 3, "price": 320, "rating": 4.1, "address": "静安区南京西路", "facilities": ["WiFi", "早餐"]},
    ],
    "深圳": [
        {"name": "深圳瑞吉酒店", "star": 5, "price": 1500, "rating": 4.9, "address": "福田区深南大道", "facilities": ["WiFi", "健身房", "游泳池", "SPA", "米其林餐厅"]},
        {"name": "深圳威斯汀酒店", "star": 5, "price": 880, "rating": 4.6, "address": "南山区科技园", "facilities": ["WiFi", "健身房", "游泳池", "商务中心"]},
        {"name": "深圳维也纳酒店", "star": 3, "price": 350, "rating": 4.2, "address": "罗湖区东门", "facilities": ["WiFi", "早餐"]},
    ],
    "杭州": [
        {"name": "杭州西湖国宾馆", "star": 5, "price": 1000, "rating": 4.8, "address": "西湖区杨公堤", "facilities": ["WiFi", "健身房", "游泳池", "西湖景观"]},
        {"name": "杭州凯悦酒店", "star": 5, "price": 780, "rating": 4.5, "address": "江干区钱江新城", "facilities": ["WiFi", "健身房", "餐厅", "会议室"]},
        {"name": "杭州全季酒店", "star": 3, "price": 380, "rating": 4.3, "address": "下城区武林广场", "facilities": ["WiFi", "早餐"]},
    ],
}


@tool
def search_hotels(city: str, min_price: Optional[int] = None, max_price: Optional[int] = None, min_star: Optional[int] = None) -> str:
    """搜索指定城市的酒店，支持按价格和星级筛选。

    适用场景：
    - 用户需要在出差城市预订住宿
    - 根据预算筛选合适的酒店
    - 对比不同星级酒店的价格和设施
    - 查找符合公司差旅标准的酒店

    参数说明：
    - city: 城市名称（如"北京"、"上海"）
    - min_price: 最低价格（元/晚），可选，不填则无下限
    - max_price: 最高价格（元/晚），可选，不填则无上限
    - min_star: 最低星级（1-5星），可选，不填则不限星级

    返回信息：
    - 酒店名称和星级
    - 价格（元/晚）
    - 用户评分
    - 地址位置
    - 酒店设施（WiFi、健身房、游泳池等）
    - 按评分从高到低排序

    筛选规则：
    - 同时满足价格和星级条件的酒店
    - 优先展示高评分酒店
    - 最多返回10家酒店

    注意事项：
    - 这是模拟数据，实际使用需要对接真实酒店API
    - 价格为平日价格，节假日可能上浮
    - 建议提前预订以确保有房

    示例：
    - search_hotels("北京") -> 返回北京所有酒店
    - search_hotels("上海", max_price=800) -> 返回上海800元以下的酒店
    - search_hotels("深圳", min_star=4) -> 返回深圳4星级及以上酒店
    - search_hotels("杭州", min_price=300, max_price=600, min_star=3) -> 价格和星级组合筛选

    Args:
        city: 城市名称
        min_price: 最低价格，可选
        max_price: 最高价格，可选
        min_star: 最低星级，可选

    Returns:
        格式化的酒店列表字符串
    """
    # 查询城市的酒店
    hotels = MOCK_HOTELS.get(city, [])

    if not hotels:
        return (
            f"❌ 抱歉，暂无{city}的酒店信息\n"
            f"建议：\n"
            f"1. 检查城市名称是否正确\n"
            f"2. 查询邻近城市的酒店\n"
            f"3. 联系客服获取更多信息"
        )

    # 应用筛选条件
    filtered_hotels = hotels.copy()

    # 价格筛选
    if min_price is not None:
        filtered_hotels = [h for h in filtered_hotels if h["price"] >= min_price]
    if max_price is not None:
        filtered_hotels = [h for h in filtered_hotels if h["price"] <= max_price]

    # 星级筛选
    if min_star is not None:
        filtered_hotels = [h for h in filtered_hotels if h["star"] >= min_star]

    if not filtered_hotels:
        filters = []
        if min_price: filters.append(f"最低价格¥{min_price}")
        if max_price: filters.append(f"最高价格¥{max_price}")
        if min_star: filters.append(f"最低{min_star}星级")
        filter_str = "、".join(filters)

        return (
            f"❌ 抱歉，{city}没有符合条件的酒店\n"
            f"筛选条件：{filter_str}\n\n"
            f"建议：\n"
            f"1. 放宽价格范围\n"
            f"2. 降低星级要求\n"
            f"3. 查看其他区域的酒店"
        )

    # 按评分排序（从高到低）
    sorted_hotels = sorted(filtered_hotels, key=lambda x: x["rating"], reverse=True)

    # 格式化输出
    filters = []
    if min_price: filters.append(f"最低¥{min_price}")
    if max_price: filters.append(f"最高¥{max_price}")
    if min_star: filters.append(f"{min_star}星级以上")
    filter_info = f" ({', '.join(filters)})" if filters else ""

    result_lines = [
        f"🏨 {city}酒店查询结果{filter_info}",
        f"🔢 共找到 {len(sorted_hotels)} 家酒店\n"
    ]

    for idx, hotel in enumerate(sorted_hotels, 1):
        star_display = "⭐" * hotel["star"]
        facilities = "、".join(hotel.get("facilities", ["WiFi"]))

        result_lines.append(
            f"【酒店{idx}】\n"
            f"  🏨 {hotel['name']}\n"
            f"  {star_display} ({hotel['star']}星级)\n"
            f"  💰 ¥{hotel['price']}/晚\n"
            f"  ⭐ 评分：{hotel['rating']}/5.0\n"
            f"  📍 {hotel['address']}\n"
            f"  ✨ 设施：{facilities}\n"
        )

    result_lines.append("ℹ️  (模拟数据，实际价格和房态以酒店官网为准)")

    return "\n".join(result_lines)


@tool
def get_hotel_details(city: str, hotel_name: str) -> str:
    """查询指定酒店的详细信息。

    适用场景：
    - 用户想了解某家酒店的详细情况
    - 查看酒店的具体设施和服务
    - 确认酒店位置和交通便利性
    - 查看用户评价和推荐理由

    参数说明：
    - city: 酒店所在城市
    - hotel_name: 酒店名称（必须完整匹配）

    返回信息：
    - 酒店基本信息（名称、星级、价格）
    - 详细地址和交通指南
    - 完整设施列表
    - 用户评分和评价摘要
    - 房型和服务说明
    - 预订建议

    注意事项：
    - 酒店名称需要完整匹配
    - 如果名称不确定，可以先用search_hotels查询
    - 价格为参考价，实际价格可能随季节变化

    示例：
    - get_hotel_details("北京", "北京希尔顿酒店") -> 返回该酒店详细信息
    - get_hotel_details("上海", "上海浦东香格里拉酒店") -> 返回详细信息

    Args:
        city: 城市名称
        hotel_name: 酒店名称

    Returns:
        格式化的酒店详细信息字符串
    """
    # 查询城市的酒店
    hotels = MOCK_HOTELS.get(city, [])

    if not hotels:
        return f"❌ 抱歉，暂无{city}的酒店信息"

    # 查找指定酒店
    hotel = None
    for h in hotels:
        if h["name"] == hotel_name or hotel_name in h["name"]:
            hotel = h
            break

    if not hotel:
        available_hotels = [h["name"] for h in hotels]
        return (
            f"❌ 在{city}找不到酒店：{hotel_name}\n\n"
            f"您可能想找的酒店：\n" +
            "\n".join([f"  • {name}" for name in available_hotels])
        )

    # 生成详细信息
    star_display = "⭐" * hotel["star"]
    facilities = hotel.get("facilities", ["WiFi"])

    # 模拟用户评价
    reviews = {
        5: ["服务一流", "设施完善", "地理位置优越", "物超所值"],
        4: ["服务不错", "房间舒适", "交通便利", "性价比高"],
        3: ["经济实惠", "干净卫生", "位置可以", "基础设施齐全"],
    }
    review_keywords = reviews.get(hotel["star"], ["干净卫生", "服务周到"])

    # 根据价格生成房型信息
    if hotel["price"] >= 800:
        room_types = "• 豪华大床房、豪华双床房、行政套房、总统套房"
        services = "• 24小时管家服务\n  • 行政酒廊\n  • 免费机场接送\n  • 免费早餐"
    elif hotel["price"] >= 400:
        room_types = "• 标准大床房、标准双床房、商务房"
        services = "• 24小时前台\n  • 行李寄存\n  • 商务中心\n  • 早餐（需付费）"
    else:
        room_types = "• 经济大床房、经济双床房"
        services = "• 24小时前台\n  • 行李寄存\n  • 简易早餐"

    # 生成交通指南
    if "浦东" in hotel["address"] or "陆家嘴" in hotel["address"]:
        transport = "🚇 地铁2号线陆家嘴站，步行5分钟\n  🚕 距离浦东机场30公里，约45分钟车程"
    elif "朝阳" in hotel["address"]:
        transport = "🚇 地铁1号线国贸站，步行8分钟\n  🚕 距离首都机场25公里，约40分钟车程"
    elif "福田" in hotel["address"]:
        transport = "🚇 地铁1号线会展中心站，步行3分钟\n  🚕 距离深圳机场30公里，约40分钟车程"
    else:
        transport = "🚇 地铁站步行10分钟内\n  🚕 距离市中心约5公里"

    return (
        f"🏨 酒店详细信息\n"
        f"{'=' * 50}\n\n"
        f"【基本信息】\n"
        f"  🏨 名称：{hotel['name']}\n"
        f"  {star_display} 星级：{hotel['star']}星级酒店\n"
        f"  💰 价格：¥{hotel['price']}/晚起\n"
        f"  ⭐ 评分：{hotel['rating']}/5.0\n\n"
        f"【位置交通】\n"
        f"  📍 地址：{hotel['address']}\n"
        f"  🚗 交通：\n  {transport}\n\n"
        f"【酒店设施】\n" +
        "\n".join([f"  ✓ {facility}" for facility in facilities]) + "\n\n"
        f"【房型信息】\n"
        f"  {room_types}\n\n"
        f"【服务项目】\n"
        f"  {services}\n\n"
        f"【宾客评价】\n" +
        "\n".join([f"  • {review}" for review in review_keywords[:3]]) + "\n\n"
        f"💡 预订建议：\n"
        f"  • 提前3-7天预订享受优惠价格\n"
        f"  • 会员可享受房间升级和积分优惠\n"
        f"  • 长住（7天以上）可申请折扣\n"
        f"  • 企业客户可联系申请协议价\n\n"
        f"ℹ️  (模拟数据，详细信息以酒店官网为准)"
    )


# 工具列表（用于Agent注册）
def get_all_hotel_tools():
    """获取所有酒店相关工具"""
    return [search_hotels, get_hotel_details]


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("测试酒店查询工具模块")
    print("=" * 60)

    # 测试1：搜索所有酒店
    print("\n【测试1】搜索北京所有酒店")
    print("-" * 60)
    result1 = search_hotels.invoke({"city": "北京"})
    print(result1)

    # 测试2：价格筛选
    print("\n【测试2】搜索上海800元以下的酒店")
    print("-" * 60)
    result2 = search_hotels.invoke({
        "city": "上海",
        "max_price": 800
    })
    print(result2)

    # 测试3：星级筛选
    print("\n【测试3】搜索深圳4星级及以上酒店")
    print("-" * 60)
    result3 = search_hotels.invoke({
        "city": "深圳",
        "min_star": 4
    })
    print(result3)

    # 测试4：组合筛选
    print("\n【测试4】搜索杭州300-800元的3星级以上酒店")
    print("-" * 60)
    result4 = search_hotels.invoke({
        "city": "杭州",
        "min_price": 300,
        "max_price": 800,
        "min_star": 3
    })
    print(result4)

    # 测试5：查询酒店详情
    print("\n【测试5】查询北京希尔顿酒店详情")
    print("-" * 60)
    result5 = get_hotel_details.invoke({
        "city": "北京",
        "hotel_name": "北京希尔顿酒店"
    })
    print(result5)

    # 测试6：查询不存在的酒店
    print("\n【测试6】查询不存在的酒店")
    print("-" * 60)
    result6 = get_hotel_details.invoke({
        "city": "北京",
        "hotel_name": "不存在的酒店"
    })
    print(result6)

    # 查看工具元数据
    print("\n【工具信息】")
    print("-" * 60)
    print(f"工具1：{search_hotels.name}")
    print(f"描述：{search_hotels.description[:50]}...")
    print(f"\n工具2：{get_hotel_details.name}")
    print(f"描述：{get_hotel_details.description[:50]}...")

    print("\n" + "=" * 60)
    print("✅ 酒店工具测试完成")
    print("=" * 60)
