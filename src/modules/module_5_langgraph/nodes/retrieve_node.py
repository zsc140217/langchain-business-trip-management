"""
检索节点
封装RAG检索逻辑为LangGraph节点
"""
from typing import Dict, Any
from pathlib import Path
import logging
from ..state import TravelAgentState
from src.rag.retriever import get_retriever, load_vectorstore

# 配置
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTORSTORE_PATH = PROJECT_ROOT / "data" / "vectorstore"
DEFAULT_RETRIEVAL_TOP_K = 5

logger = logging.getLogger(__name__)


def retrieve_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    检索节点：从向量存储中检索相关文档

    LangGraph节点的标准形式：
    - 输入：状态字典
    - 输出：要更新的字段字典（会合并到状态中）

    Args:
        state: 当前状态

    Returns:
        包含documents字段的字典
    """
    # 验证必需字段
    if "query" not in state:
        logger.error("State missing required field: 'query'")
        return {"documents": []}

    # 使用改写后的查询（如果存在），否则使用原始查询
    query = state.get("rewritten_query") or state["query"]

    # 验证查询有效性
    if not isinstance(query, str) or not query.strip():
        logger.warning("Invalid query (empty or non-string)")
        return {"documents": []}

    logger.info(f"[搜索] 检索节点：查询 = '{query}'")

    # 检查向量存储是否存在
    if not VECTORSTORE_PATH.exists():
        logger.warning(f"⚠️  向量存储不存在：{VECTORSTORE_PATH}")
        logger.info("   返回空文档列表")
        return {"documents": []}

    try:
        # 加载向量存储
        vectorstore = load_vectorstore(str(VECTORSTORE_PATH))

        # 创建检索器
        retriever = get_retriever(vectorstore, k=DEFAULT_RETRIEVAL_TOP_K)

        # 执行检索
        docs = retriever.invoke(query)

        logger.info(f"检索到 {len(docs)} 个文档")

        return {"documents": docs}

    except ValueError as e:
        logger.error(f"配置错误：{e}")
        return {"documents": []}
    except Exception as e:
        logger.exception(f"检索失败：{e}")
        return {"documents": []}


# 测试代码
if __name__ == "__main__":
    """测试检索节点"""
    from ..state import create_initial_state
    
    print("测试检索节点...\n")
    
    # 创建测试状态
    state = create_initial_state("上海出差住宿标准是多少？")
    
    # 调用节点
    result = retrieve_node(state)
    
    print(f"\n返回结果：")
    print(f"  文档数量：{len(result['documents'])}")
    
    if result['documents']:
        print(f"\n第一个文档内容预览：")
        print(result['documents'][0].page_content[:200])
    
    print("\n✅ 检索节点测试完成！")
