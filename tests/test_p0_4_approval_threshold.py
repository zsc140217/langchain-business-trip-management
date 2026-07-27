"""
P0-4: 审批系统用户等级集成验证脚本
测试根据用户等级动态计算审批阈值
"""

import sys
import os
import io

# 修复Windows终端编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """测试1: 验证模块导入"""
    print("=" * 60)
    print("测试1: 验证模块导入")
    print("=" * 60)

    try:
        from src.agents.approval_engine import ApprovalEngine
        print("✅ ApprovalEngine 导入成功")

        from src.models.user import User
        print("✅ User 模型导入成功")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_approval_threshold_calculation():
    """测试2: 验证审批阈值计算"""
    print("\n" + "=" * 60)
    print("测试2: 验证审批阈值计算")
    print("=" * 60)

    try:
        from src.agents.approval_engine import ApprovalEngine

        # 创建模拟用户对象
        class MockUser:
            def __init__(self, is_executive):
                self.is_executive = is_executive

        # 创建 ApprovalEngine 实例（简化版）
        class MockLLM:
            pass

        class MockMemoryService:
            pass

        class MockFeishuClient:
            pass

        class MockApprovalGraph:
            pass

        engine = ApprovalEngine(
            llm=MockLLM(),
            memory_service=MockMemoryService(),
            feishu_client=MockFeishuClient(),
            approval_graph=MockApprovalGraph(),
            auto_approval_threshold=1000
        )

        # 测试场景1: 普通员工 - 成都 - 2天
        print("\n场景1: 普通员工出差成都2天")
        employee = MockUser(is_executive=False)
        threshold1 = engine.calculate_approval_threshold(
            user=employee,
            destination="成都",
            days=2
        )
        expected1 = 550 * 2 * 1.0  # 550元/天 × 2天 × 1.0（非一线城市）
        print(f"  计算阈值: ¥{threshold1}")
        print(f"  预期阈值: ¥{expected1}")
        assert threshold1 == expected1, f"阈值计算错误: {threshold1} != {expected1}"
        print("  ✅ 通过")

        # 测试场景2: 高管 - 成都 - 2天
        print("\n场景2: 高管出差成都2天")
        executive = MockUser(is_executive=True)
        threshold2 = engine.calculate_approval_threshold(
            user=executive,
            destination="成都",
            days=2
        )
        expected2 = 670 * 2 * 1.0  # 670元/天 × 2天 × 1.0
        print(f"  计算阈值: ¥{threshold2}")
        print(f"  预期阈值: ¥{expected2}")
        assert threshold2 == expected2, f"阈值计算错误: {threshold2} != {expected2}"
        print("  ✅ 通过")

        # 测试场景3: 普通员工 - 北京 - 3天（一线城市系数1.2）
        print("\n场景3: 普通员工出差北京3天")
        threshold3 = engine.calculate_approval_threshold(
            user=employee,
            destination="北京",
            days=3
        )
        expected3 = 550 * 3 * 1.2  # 550元/天 × 3天 × 1.2（一线城市）
        print(f"  计算阈值: ¥{threshold3}")
        print(f"  预期阈值: ¥{expected3}")
        assert threshold3 == expected3, f"阈值计算错误: {threshold3} != {expected3}"
        print("  ✅ 通过")

        # 测试场景4: 高管 - 上海 - 5天（一线城市系数1.2）
        print("\n场景4: 高管出差上海5天")
        threshold4 = engine.calculate_approval_threshold(
            user=executive,
            destination="上海",
            days=5
        )
        expected4 = 670 * 5 * 1.2  # 670元/天 × 5天 × 1.2
        print(f"  计算阈值: ¥{threshold4}")
        print(f"  预期阈值: ¥{expected4}")
        assert threshold4 == expected4, f"阈值计算错误: {threshold4} != {expected4}"
        print("  ✅ 通过")

        # 测试场景5: 无用户对象（使用默认阈值）
        print("\n场景5: 无用户对象（降级到默认阈值）")
        threshold5 = engine.calculate_approval_threshold(
            user=None,
            destination="杭州",
            days=3
        )
        expected5 = 1000  # 默认阈值
        print(f"  计算阈值: ¥{threshold5}")
        print(f"  预期阈值: ¥{expected5}")
        assert threshold5 == expected5, f"阈值计算错误: {threshold5} != {expected5}"
        print("  ✅ 通过")

        print("\n✅ 所有审批阈值计算测试通过")
        return True

    except AssertionError as e:
        print(f"\n❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_signature():
    """测试3: 验证execute方法签名（向后兼容性）"""
    print("\n" + "=" * 60)
    print("测试3: 验证execute方法签名")
    print("=" * 60)

    try:
        from src.agents.approval_engine import ApprovalEngine
        import inspect

        # 获取execute方法签名
        sig = inspect.signature(ApprovalEngine.execute)
        params = list(sig.parameters.keys())

        print(f"方法参数: {params}")

        # 验证必需参数
        required_params = ['self', 'query', 'user_id', 'conversation_id']
        for param in required_params:
            assert param in params, f"缺少必需参数: {param}"
            print(f"  ✅ 必需参数存在: {param}")

        # 验证可选参数
        assert 'user' in params, "缺少可选参数: user"
        print(f"  ✅ 可选参数存在: user")

        # 验证user参数有默认值（向后兼容）
        user_param = sig.parameters['user']
        assert user_param.default is not inspect.Parameter.empty, "user参数应该有默认值"
        print(f"  ✅ user参数有默认值: {user_param.default}")

        print("\n✅ execute方法签名验证通过（向后兼容）")
        return True

    except AssertionError as e:
        print(f"\n❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_city_multiplier():
    """测试4: 验证城市系数计算"""
    print("\n" + "=" * 60)
    print("测试4: 验证城市系数计算")
    print("=" * 60)

    try:
        from src.agents.approval_engine import ApprovalEngine

        # 创建简化实例
        class MockLLM:
            pass

        class MockMemoryService:
            pass

        class MockFeishuClient:
            pass

        class MockApprovalGraph:
            pass

        engine = ApprovalEngine(
            llm=MockLLM(),
            memory_service=MockMemoryService(),
            feishu_client=MockFeishuClient(),
            approval_graph=MockApprovalGraph()
        )

        # 测试一线城市
        tier1_cities = ["北京", "上海", "深圳"]
        for city in tier1_cities:
            multiplier = engine._get_city_multiplier(city)
            assert multiplier == 1.2, f"{city} 系数应该是1.2，实际是{multiplier}"
            print(f"  ✅ {city}: 系数 {multiplier}")

        # 测试非一线城市
        other_cities = ["成都", "杭州", "西安", "武汉"]
        for city in other_cities:
            multiplier = engine._get_city_multiplier(city)
            assert multiplier == 1.0, f"{city} 系数应该是1.0，实际是{multiplier}"
            print(f"  ✅ {city}: 系数 {multiplier}")

        # 测试None
        multiplier = engine._get_city_multiplier(None)
        assert multiplier == 1.0, f"None 系数应该是1.0，实际是{multiplier}"
        print(f"  ✅ None: 系数 {multiplier}")

        print("\n✅ 城市系数计算测试通过")
        return True

    except AssertionError as e:
        print(f"\n❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("P0-4: 审批系统用户等级集成验证")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("审批阈值计算", test_approval_threshold_calculation()))
    results.append(("execute方法签名", test_execute_signature()))
    results.append(("城市系数计算", test_city_multiplier()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20} {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print("\n" + "=" * 60)
    print(f"总计: {passed_count}/{total_count} 通过")
    print("=" * 60)

    if passed_count == total_count:
        print("\n🎉 所有测试通过！P0-4任务完成。")
        print("\n差旅标准总结:")
        print("┌────────────┬──────────────────────────┬───────────────────────────────┐")
        print("│    项目    │ 高管 (is_executive=TRUE) │ 普通员工 (is_executive=FALSE) │")
        print("├────────────┼──────────────────────────┼───────────────────────────────┤")
        print("│ 交通       │ 软席/高铁一等座          │ 硬席/高铁二等座               │")
        print("├────────────┼──────────────────────────┼───────────────────────────────┤")
        print("│ 成都住宿   │ ≤370元/天                │ ≤300元/天                     │")
        print("├────────────┼──────────────────────────┼───────────────────────────────┤")
        print("│ 省内伙食   │ 100元/天                 │ 100元/天                      │")
        print("├────────────┼──────────────────────────┼───────────────────────────────┤")
        print("│ 日均总限额 │ 670元/天                 │ 550元/天                      │")
        print("├────────────┼──────────────────────────┼───────────────────────────────┤")
        print("│ 一线城市   │ 670×1.2=804元/天         │ 550×1.2=660元/天              │")
        print("└────────────┴──────────────────────────┴───────────────────────────────┘")
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()
