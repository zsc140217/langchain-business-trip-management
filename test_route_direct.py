#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试路由逻辑 - 绕过API层
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ.setdefault('DASHSCOPE_API_KEY', 'sk-xxx')  # 会被.env覆盖
os.environ.setdefault('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

from src.models.llm import get_llm
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.qa_engine import QAEngine
from src.agents.approval_engine import ApprovalEngine
from src.memory.memory_service import MemoryService
from src.tools.registry import get_all_tools

def test_direct_route():
    """直接测试路由"""
    print("="*60)
    print("直接路由测试")
    print("="*60)

    # 1. 初始化组件
    print("\n[1] 初始化LLM...")
    llm = get_llm()

    print("[2] 初始化工具...")
    tools = get_all_tools()
    print(f"    可用工具: {list(tools.keys())}")

    print("[3] 初始化Memory...")
    memory_service = MemoryService()

    print("[4] 初始化OrchestratorAgent...")
    orchestrator = OrchestratorAgent(
        llm=llm,
        tools=tools,
        qa_engine=None,  # 延迟初始化
        approval_engine=None,  # 只测试快路径，不需要
        memory_service=memory_service
    )

    # 2. 测试路由
    test_cases = [
        ("北京天气", "fast_path"),
        # ("我要报销800元", "approval_domain"),  # 跳过审批测试
    ]

    print("\n" + "="*60)
    print("开始测试")
    print("="*60)

    for query, expected_route in test_cases:
        print(f"\n测试: {query}")
        print(f"预期: {expected_route}")
        print("-"*60)

        try:
            answer, actual_route = orchestrator.route(query, user_id="test")
            print(f"实际: {actual_route}")
            print(f"答案: {answer[:100]}...")

            if actual_route == expected_route:
                print("✓ PASS")
            else:
                print("✗ FAIL")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_direct_route()
