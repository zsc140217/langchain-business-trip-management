"""
测试飞猪AI集成
验证FliggyClient是否正常工作
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.fliggy_client import FliggyClient


def test_fliggy_client():
    """测试飞猪客户端基础功能"""
    print("=" * 60)
    print("飞猪AI集成测试")
    print("=" * 60)

    # 初始化客户端
    client = FliggyClient()
    print(f"\n✅ FliggyClient 初始化完成")
    print(f"API Key: {client.api_key[:20]}..." if client.api_key else "❌ 未找到API Key")

    # 检查可用性
    is_available = client.is_available()
    print(f"飞猪API可用性: {'✅ 可用' if is_available else '❌ 不可用'}")

    if not is_available:
        print("\n⚠️  飞猪AI CLI未安装或配置失败")
        print("请执行以下命令安装:")
        print("  npm install -g @clawhub/cli")
        print("  clawhub install flyai")
        return

    # 测试酒店搜索
    print("\n" + "-" * 60)
    print("测试1: 搜索北京酒店")
    print("-" * 60)

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    try:
        hotels = client.search_hotels(
            city="北京",
            checkin=tomorrow,
            checkout=day_after,
            min_star=4
        )

        if hotels:
            print(f"✅ 找到 {len(hotels)} 家酒店")
            for i, hotel in enumerate(hotels[:3], 1):
                print(f"\n{i}. {hotel['name']}")
                print(f"   价格: ¥{hotel['price']}/晚")
                print(f"   星级: {hotel['star']}星")
                print(f"   评分: {hotel['rating']}")
                if hotel.get('jumpUrl'):
                    print(f"   链接: {hotel['jumpUrl']}")
        else:
            print("⚠️  未找到酒店（可能返回格式需要调整）")

    except Exception as e:
        print(f"❌ 酒店搜索失败: {e}")

    # 测试航班搜索
    print("\n" + "-" * 60)
    print("测试2: 搜索北京到上海航班")
    print("-" * 60)

    try:
        flights = client.search_flights(
            origin="北京",
            destination="上海",
            date=tomorrow
        )

        if flights:
            print(f"✅ 找到 {len(flights)} 个航班")
            for i, flight in enumerate(flights[:3], 1):
                print(f"\n{i}. {flight['flight_no']} ({flight['airline']})")
                print(f"   时间: {flight['departure']} - {flight['arrival']}")
                print(f"   价格: ¥{flight['price']}")
                if flight.get('jumpUrl'):
                    print(f"   链接: {flight['jumpUrl']}")
        else:
            print("⚠️  未找到航班（可能返回格式需要调整）")

    except Exception as e:
        print(f"❌ 航班搜索失败: {e}")

    # 显示配额信息
    print("\n" + "-" * 60)
    print("配额使用情况")
    print("-" * 60)
    quota = client.get_quota_info()
    print(f"已使用: {quota['used']}/{quota['total']} 次")
    print(f"剩余: {quota['remaining']} 次")
    print(f"使用率: {quota['percentage']:.2f}%")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_fliggy_client()
