"""
上下文累积器 - 跨层累积上下文信息

在三层路由架构中，累积每一层的处理结果：
- Layer 0: 工具调用结果
- Layer 1: RAG检索文档
- Layer 2: 综合分析使用累积的上下文

作者：Claude
创建时间：2026-06-28
"""
from typing import Dict, List, Any, Optional
from langchain_core.documents import Document


class ContextAccumulator:
    """
    上下文累积器

    跨三层路由累积上下文信息，供Layer 2综合分析使用。

    Attributes:
        query: 原始用户查询
        tool_results: Layer 0工具调用结果 {tool_name: {result, entities}}
        rag_documents: Layer 1 RAG检索文档
        layer_history: 各层执行历史记录
        metadata: 额外元数据

    注意：此类不是线程安全的。如需并发使用，请为每个请求创建独立实例。
    """

    def __init__(self):
        """初始化空的上下文累积器"""
        self.query: str = ""
        self.tool_results: Dict[str, Dict[str, Any]] = {}
        self.rag_documents: List[Document] = []
        self.layer_history: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def set_query(self, query: str):
        """
        设置原始查询

        Args:
            query: 用户查询文本
        """
        self.query = query
        self.layer_history.append(f"Query: {query[:50]}...")

    def add_tool_result(self, tool_name: str, result: Any, entities: Optional[Dict] = None):
        """
        添加Layer 0工具调用结果

        Args:
            tool_name: 工具名称（weather/flight/hotel/customer/route）
            result: 工具执行结果
            entities: 提取的实体参数（可选）
        """
        self.tool_results[tool_name] = {
            "result": result,
            "entities": entities or {}
        }
        self.layer_history.append(f"Layer 0: Tool '{tool_name}' executed")

    def add_rag_documents(self, documents: List[Document]):
        """
        添加Layer 1 RAG检索文档

        Args:
            documents: 检索到的文档列表
        """
        self.rag_documents = documents
        self.layer_history.append(f"Layer 1: Retrieved {len(documents)} documents")

    def has_tool_results(self) -> bool:
        """
        检查是否有工具调用结果

        Returns:
            True表示Layer 0执行了工具调用
        """
        return len(self.tool_results) > 0

    def has_rag_documents(self) -> bool:
        """
        检查是否有RAG文档

        Returns:
            True表示Layer 1检索到文档
        """
        return len(self.rag_documents) > 0

    def get_synthesis_context(self) -> str:
        """
        格式化所有上下文供Layer 2使用

        Returns:
            格式化的上下文字符串，包含查询、工具结果、RAG文档
        """
        context_parts = []

        # 原始查询
        context_parts.append(f"用户查询：{self.query}")

        # 工具调用结果
        if self.has_tool_results():
            context_parts.append("\n已执行的工具：")
            for tool_name, data in self.tool_results.items():
                context_parts.append(f"- {tool_name}:")
                context_parts.append(f"  实体: {data['entities']}")
                context_parts.append(f"  结果: {str(data['result'])[:200]}...")
        else:
            context_parts.append("\n未执行任何工具")

        # RAG检索文档
        if self.has_rag_documents():
            context_parts.append(f"\n检索到的文档（共{len(self.rag_documents)}个）：")
            for i, doc in enumerate(self.rag_documents[:5], 1):  # 最多显示5个
                context_parts.append(f"{i}. {doc.page_content[:150]}...")
                if doc.metadata:
                    context_parts.append(f"   来源: {doc.metadata.get('source', 'unknown')}")
        else:
            context_parts.append("\n未检索到相关文档")

        return "\n".join(context_parts)

    def get_tool_result(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定工具的结果

        Args:
            tool_name: 工具名称

        Returns:
            工具结果字典，如果不存在返回None
        """
        return self.tool_results.get(tool_name)

    def get_all_tool_results(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有工具结果

        Returns:
            所有工具结果字典
        """
        return self.tool_results.copy()

    def clear(self):
        """
        清空所有累积的上下文

        在处理新查询前调用此方法
        """
        self.query = ""
        self.tool_results.clear()
        self.rag_documents.clear()
        self.layer_history.clear()
        self.metadata.clear()

    def get_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要（用于日志和调试）

        Returns:
            上下文摘要字典
        """
        return {
            "query": self.query[:100] if self.query else None,
            "tools_executed": list(self.tool_results.keys()),
            "num_documents": len(self.rag_documents),
            "layers_visited": len(self.layer_history)
        }

    def __repr__(self) -> str:
        """字符串表示"""
        summary = self.get_summary()
        return (
            f"ContextAccumulator("
            f"query='{summary['query']}', "
            f"tools={summary['tools_executed']}, "
            f"docs={summary['num_documents']})"
        )


# 使用示例
if __name__ == "__main__":
    """演示ContextAccumulator的使用"""

    # 创建累积器
    ctx = ContextAccumulator()

    # 设置查询
    ctx.set_query("北京天气怎么样？顺便推荐酒店")

    # Layer 0: 添加工具结果
    ctx.add_tool_result(
        tool_name="weather",
        result="北京今日晴，温度18-25℃",
        entities={"city": "北京"}
    )

    # Layer 1: 添加RAG文档
    from langchain_core.documents import Document
    ctx.add_rag_documents([
        Document(
            page_content="一线城市（北京、上海）住宿标准：500元/晚",
            metadata={"source": "policy.txt"}
        ),
        Document(
            page_content="推荐协议酒店：如家、汉庭等连锁品牌",
            metadata={"source": "hotel_guide.txt"}
        )
    ])

    # 获取综合上下文
    print("=" * 70)
    print("综合上下文：")
    print("=" * 70)
    print(ctx.get_synthesis_context())

    print("\n" + "=" * 70)
    print("上下文摘要：")
    print("=" * 70)
    print(ctx.get_summary())

    print("\n" + "=" * 70)
    print("执行历史：")
    print("=" * 70)
    for record in ctx.layer_history:
        print(f"  - {record}")
