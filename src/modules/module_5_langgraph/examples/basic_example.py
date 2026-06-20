"""
基础图示例
演示T1.1 StateGraph基础架构的使用
"""
from ..graphs.basic_graph import run_basic_graph


def demo_basic_rag():
    """演示基础RAG流程"""
    print("=" * 60)
    print("基础RAG图演示")
    print("=" * 60)
    
    # 测试查询
    queries = [
        "上海出差住宿标准是多少？",
        "北京出差交通费用怎么报销？",
        "深圳出差标准间价格上限"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n【示例 {i}】")
        print(f"查询：{query}\n")
        
        result = run_basic_graph(query)
        
        print("\n答案：")
        print("-" * 60)
        print(result.get("answer", "未生成答案"))
        print("-" * 60)
        
        print(f"\n检索到 {len(result.get('documents', []))} 个文档")
        
        if i < len(queries):
            print("\n" + "=" * 60 + "\n")
    
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    demo_basic_rag()
