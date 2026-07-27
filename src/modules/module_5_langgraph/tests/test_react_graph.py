"""
ReAct图测试
验证T1.2：条件分支 + 循环
"""
import pytest
from ..state import create_initial_state
from ..graphs.react_graph import create_react_graph, run_react_graph


class TestReActGraph:
    """ReAct图测试类"""
    
    def test_graph_creation(self):
        """测试图创建"""
        graph = create_react_graph()
        assert graph is not None
        print("[OK] ReAct图创建成功")
    
    def test_basic_flow(self):
        """测试基础流程（无工具调用）"""
        query = "什么是差旅政策？"
        
        graph = create_react_graph()
        initial_state = create_initial_state(query, max_iterations=3)
        result = graph.invoke(initial_state)
        
        # 验证结果
        assert "answer" in result
        assert result["answer"] is not None
        assert result["iteration"] >= 0
        
        print(f"[OK] 基础流程测试通过")
        print(f"   迭代次数：{result['iteration']}")
    
    def test_max_iterations_limit(self):
        """测试最大迭代次数限制"""
        query = "测试查询"
        max_iter = 2
        
        graph = create_react_graph()
        initial_state = create_initial_state(query, max_iterations=max_iter)
        result = graph.invoke(initial_state)
        
        # 验证不超过最大迭代次数
        assert result["iteration"] <= max_iter
        
        print(f"[OK] 最大迭代限制测试通过")
        print(f"   最大迭代：{max_iter}，实际：{result['iteration']}")
    
    def test_multi_city_comparison(self):
        """测试多城市对比（T1.2要求）"""
        query = "对比北京和上海的住宿标准"
        
        graph = create_react_graph()
        initial_state = create_initial_state(query, max_iterations=3)
        result = graph.invoke(initial_state)
        
        # 验证有答案
        assert "answer" in result
        assert result["answer"] is not None
        
        print(f"[OK] 多城市对比测试通过")
        print(f"   查询：{query}")
        print(f"   迭代：{result['iteration']}")
    
    def test_state_flow(self):
        """测试状态流转"""
        query = "深圳差旅标准"
        
        graph = create_react_graph()
        initial_state = create_initial_state(query, max_iterations=3)
        result = graph.invoke(initial_state)
        
        # 验证状态字段
        assert "query" in result
        assert "documents" in result
        assert "answer" in result
        assert "iteration" in result
        assert "tool_calls" in result
        
        # 验证查询未被修改
        assert result["query"] == query
        
        print("[OK] 状态流转测试通过")
    
    def test_conditional_edges(self):
        """测试条件边逻辑"""
        from ..utils.conditions import should_continue
        
        # 测试1：无tool_calls
        state_no_tools = create_initial_state("测试", max_iterations=3)
        state_no_tools["tool_calls"] = []
        assert should_continue(state_no_tools) == "end"
        
        # 测试2：有tool_calls
        state_with_tools = create_initial_state("测试", max_iterations=3)
        state_with_tools["tool_calls"] = [{"name": "test", "args": {}}]
        assert should_continue(state_with_tools) == "tools"
        
        # 测试3：达到最大迭代
        state_max_iter = create_initial_state("测试", max_iterations=2)
        state_max_iter["iteration"] = 2
        state_max_iter["tool_calls"] = [{"name": "test", "args": {}}]
        assert should_continue(state_max_iter) == "end"
        
        print("[OK] 条件边逻辑测试通过")


def test_run_react_graph_helper():
    """测试便捷运行函数"""
    result = run_react_graph("广州住宿标准", max_iterations=2)
    
    assert result is not None
    assert "answer" in result
    
    print("[OK] 便捷函数测试通过")


if __name__ == "__main__":
    """直接运行测试"""
    print("运行ReAct图测试...\n")
    print("=" * 60)
    
    test = TestReActGraph()
    
    try:
        print("\n1. 测试图创建")
        test.test_graph_creation()
        
        print("\n2. 测试基础流程")
        test.test_basic_flow()
        
        print("\n3. 测试最大迭代限制")
        test.test_max_iterations_limit()
        
        print("\n4. 测试多城市对比")
        test.test_multi_city_comparison()
        
        print("\n5. 测试状态流转")
        test.test_state_flow()
        
        print("\n6. 测试条件边逻辑")
        test.test_conditional_edges()
        
        print("\n7. 测试便捷函数")
        test_run_react_graph_helper()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败：{e}")
        import traceback
        traceback.print_exc()
