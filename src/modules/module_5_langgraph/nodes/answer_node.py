"""
回答生成节点
基于检索到的文档生成答案
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState
from src.models.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.exceptions import LangChainException

# 配置
MAX_CONTEXT_DOCS = 3
DEFAULT_LLM_TEMPERATURE = 0.3

logger = logging.getLogger(__name__)


def answer_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    回答生成节点：基于检索文档生成答案

    这是RAG的"Generation"部分

    Args:
        state: 当前状态

    Returns:
        包含answer字段的字典
    """
    # 验证必需字段
    if "query" not in state:
        logger.error("State missing required field: 'query'")
        return {"answer": "系统错误：缺少查询信息。"}

    query = state["query"]
    documents = state.get("documents", [])

    # 验证查询有效性
    if not isinstance(query, str) or not query.strip():
        logger.warning("Invalid query in answer_node")
        return {"answer": "查询信息无效，请重新输入。"}

    logger.info(f"💬 回答生成节点：基于 {len(documents)} 个文档生成答案")

    # 如果没有文档，直接回复
    if not documents:
        return {
            "answer": "抱歉，我没有找到相关的差旅政策信息。请提供更多上下文或联系管理员。"
        }

    # 构建上下文
    context = "\n\n".join([
        f"文档{i+1}:\n{doc.page_content}"
        for i, doc in enumerate(documents[:MAX_CONTEXT_DOCS])
    ])

    # 构建Prompt
    system_prompt = """你是一个企业差旅政策助手。
你的任务是根据提供的政策文档，准确回答用户关于差旅标准的问题。

回答要求：
1. 基于文档内容回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 回答要简洁明了，突出关键数字和标准
4. 使用友好的语气
"""

    user_prompt = f"""参考文档：
{context}

用户问题：{query}

请根据上述文档回答用户问题。"""

    try:
        # 调用LLM
        llm = get_llm(temperature=DEFAULT_LLM_TEMPERATURE)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        answer = response.content

        logger.info(f"[OK] 答案生成完成（{len(answer)} 字符）")

        return {"answer": answer}

    except ValueError as e:
        # 配置错误（缺少API key等）
        logger.error(f"Configuration error in answer_node: {e}")
        return {"answer": "系统配置错误，请联系管理员。"}

    except LangChainException as e:
        # LangChain特定错误（API失败、速率限制等）
        logger.error(f"LLM API error in answer_node: {e}")
        return {"answer": "抱歉，AI服务暂时不可用，请稍后重试。"}

    except Exception as e:
        # 未预期的错误
        logger.exception(f"Unexpected error in answer_node: {e}")
        return {"answer": "抱歉，处理您的请求时发生错误。"}


# 测试代码
if __name__ == "__main__":
    """测试回答生成节点"""
    from ..state import create_initial_state
    from langchain_core.documents import Document
    
    print("测试回答生成节点...\n")
    
    # 创建测试状态（包含模拟文档）
    state = create_initial_state("上海出差住宿标准是多少？")
    state["documents"] = [
        Document(page_content="一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚")
    ]
    
    # 调用节点
    result = answer_node(state)
    
    print(f"\n生成的答案：")
    print(result["answer"])
    
    print("\n[OK] 回答生成节点测试完成！")
