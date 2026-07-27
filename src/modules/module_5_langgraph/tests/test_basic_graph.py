"""
基础图测试
验证T1.1 StateGraph基础架构
"""
import pytest
from ..state import create_initial_state, TravelAgentState
from ..graphs.basic_graph import create_basic_graph, run_basic_graph


class TestBasicGraph:
    """基础图测试类"""
    
    def test_graph_creation(self):
        """测试图创建"""
        graph = create_basic_graph()
        assert graph is not None
        print("[OK] 图创建成功")
    
    def test_simple_query(self):
        """测试简单查询流程"""
        query = "上海出差住宿标准是多少？"
        
        # 创建初始状态
        initial_state = create_initial_state(query)
        
        # 创建并执行图
        graph = create_basic_graph()
        result = graph.invoke(initial_state)
        
        # 验证结果
        assert "answer" in result
        assert result["answer"] is not None
        assert len(result["answer"]) > 0
        
        print(f"[OK] 简单查询测试通过")
        print(f"   查询：{query}")
        print(f"   答案长度：{len(result['answer'])} 字符")
    
    def test_state_flow(self):
        """测试状态流转"""
        query = "北京出差交通标准"
        initial_state = create_initial_state(query)
        
        graph = create_basic_graph()
        result = graph.invoke(initial_state)
        
        # 验证状态字段存在
        assert "query" in result
        assert "documents" in result
        assert "answer" in result
        assert "iteration" in result
        
        # 验证query未被修改
        assert result["query"] == query
        
        # 验证documents是列表
        assert isinstance(result["documents"], list)
        
        print("[OK] 状态流转测试通过")
    
    def test_no_documents_scenario(self):
        """测试没有检索到文档的场景"""
        # 使用不太可能匹配的查询
        query = "火星出差标准是多少？"
        
        graph = create_basic_graph()
        initial_state = create_initial_state(query)
        result = graph.invoke(initial_state)
        
        # 应该仍然有答案（即使是"没有找到"）
        assert "answer" in result
        assert result["answer"] is not None
        
        print("[OK] 无文档场景测试通过")
    
    def test_multiple_queries(self):
        """测试多个不同查询"""
        queries = [
            "上海出差住宿标准",
            "北京交通费用标准",
            "差旅报销流程"
        ]
        
        graph = create_basic_graph()
        
        for query in queries:
            initial_state = create_initial_state(query)
            result = graph.invoke(initial_state)
            
            assert "answer" in result
            assert result["answer"] is not None
            
            print(f"[OK] 查询测试通过：{query}")


def test_run_basic_graph_helper():
    """测试便捷运行函数"""
    result = run_basic_graph("深圳出差住宿标准")
    
    assert result is not None
    assert "answer" in result
    
    print("[OK] 便捷函数测试通过")


if __name__ == "__main__":
    """直接运行测试"""
    print("运行基础图测试...\n")
    print("=" * 60)
    
    # 创建测试实例
    test = TestBasicGraph()
    
    try:
        print("\n1. 测试图创建")
        test.test_graph_creation()
        
        print("\n2. 测试简单查询")
        test.test_simple_query()
        
        print("\n3. 测试状态流转")
        test.test_state_flow()
        
        print("\n4. 测试无文档场景")
        test.test_no_documents_scenario()
        
        print("\n5. 测试多个查询")
        test.test_multiple_queries()
        
        print("\n6. 测试便捷函数")
        test_run_basic_graph_helper()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败：{e}")
        import traceback
        traceback.print_exc()
