#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路由调试脚本 - 追踪天气查询的完整路由过程
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.llm import get_llm
from src.agents.qa_engine import QAEngine
from src.agents.approval_engine import ApprovalEngine
from src.memory.memory_service import MemoryService

def test_route():
    """测试天气查询的路由过程"""
    print("=" * 60)
    print("开始路由调试")
    print("=" * 60)

    # 初始化组件
    llm = get_llm()
    memory_service = MemoryService()
    qa_engine = QAEngine(llm=llm, memory_service=memory_service)
    approval_engine = ApprovalEngine(llm=llm)

    # 创建编排器
    orchestrator = OrchestratorAgent(
        llm=llm,
        qa_engine=qa_engine,
        approval_engine=approval_engine,
        memory_service=memory_service
    )

    # 测试查询
    test_query = "北京天气"

    print(f"\n测试查询: {test_query}")
    print("-" * 60)

    # 检查快路径规则
    print(f"\n[第1层检查] 快路径规则:")
    for rule_type, keywords in orchestrator.fast_rules.items():
        matched = [kw for kw in keywords if kw in test_query]
        if matched:
            print(f"  ✅ {rule_type}: 匹配到 {matched}")
        else:
            print(f"  ❌ {rule_type}: 无匹配")

    # 检查审批关键词
    print(f"\n[审批关键词检查]:")
    approval_matched = [kw for kw in orchestrator.approval_keywords if kw in test_query]
    if approval_matched:
        print(f"  ⚠️  匹配到审批关键词: {approval_matched}")
    else:
        print(f"  ✅ 未匹配审批关键词")

    # 执行路由
    print(f"\n[执行路由]:")
    try:
        result = orchestrator.route(test_query, user_id="debug_user")
        print(f"\n最终结果: {result[:200]}...")
    except Exception as e:
        print(f"\n❌ 路由失败: {e}")
        import traceback
        traceback.print_exc()

    # 统计信息
    print(f"\n[统计信息]:")
    print(f"  快路径命中: {orchestrator.stats['fast_path']}")
    print(f"  Q&A域路由: {orchestrator.stats['qa_domain']}")
    print(f"  审批域路由: {orchestrator.stats['approval_domain']}")

    print("\n" + "=" * 60)
    print("调试结束")
    print("=" * 60)

if __name__ == "__main__":
    test_route()
