"""
Self-RAG（自适应检索增强生成）模块

根据查询类型智能决策是否需要检索知识库：
- FACTUAL查询：执行RAG检索
- CHITCHAT查询：直接用LLM回答
"""
from typing import Optional, List
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from src.rag.query_classifier import QueryClassifier
from src.rag.chain import create_rag_chain
from src.models.llm import get_llm


class SelfRAG:
    """
    自适应RAG系统

    工作流程：
    1. 使用QueryClassifier分类查询
    2. 如果是CHITCHAT，直接用LLM回答
    3. 如果是FACTUAL，执行RAG检索并回答
    """

    def __init__(self, retriever, llm=None, classifier=None):
        """
        初始化Self-RAG系统

        Args:
            retriever: 检索器实例，用于RAG检索
            llm: 语言模型实例，如果为None则自动创建
            classifier: 查询分类器实例，如果为None则自动创建
        """
        self.retriever = retriever
        self.llm = llm if llm else get_llm(temperature=0.7)
        self.classifier = classifier if classifier else QueryClassifier()

        # 为CHITCHAT查询准备的系统提示
        self.chitchat_system_prompt = """你是一个友好的企业差旅助手。

对于闲聊和通用问题，请友好、简洁地回答。
如果用户询问你的功能，告诉他们你可以帮助查询企业差旅政策、住宿标准、报销流程等信息。
保持专业但亲切的语气。"""

    def query(self, user_query: str) -> dict:
        """
        处理用户查询

        Args:
            user_query: 用户查询字符串

        Returns:
            dict: 包含以下字段的结果
                - answer: 回答内容
                - retrieved: 是否执行了检索（bool）
                - sources: 来源文档列表（如果执行了检索）
                - classification: 分类信息

        Raises:
            ValueError: 如果查询为空或None
        """
        # 输入验证
        if not user_query or (isinstance(user_query, str) and not user_query.strip()):
            raise ValueError("查询不能为空")

        user_query = user_query.strip()

        # 1. 分类查询
        classification = self.classifier.classify(user_query)

        # 2. 根据分类决策是否检索
        if classification["type"] == "CHITCHAT":
            # 闲聊查询：直接用LLM回答
            answer = self._answer_chitchat(user_query)
            return {
                "answer": answer,
                "retrieved": False,
                "sources": [],
                "classification": classification
            }
        else:
            # 事实性查询：执行RAG检索
            answer, sources = self._answer_with_rag(user_query)
            return {
                "answer": answer,
                "retrieved": True,
                "sources": sources,
                "classification": classification
            }

    def _answer_chitchat(self, query: str) -> str:
        """
        直接用LLM回答闲聊查询

        Args:
            query: 用户查询

        Returns:
            str: 回答内容
        """
        messages = [
            SystemMessage(content=self.chitchat_system_prompt),
            HumanMessage(content=query)
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            # LLM调用失败，返回友好错误消息
            return f"抱歉，我暂时无法回答。请稍后再试。"

    def _answer_with_rag(self, query: str) -> tuple[str, List[Document]]:
        """
        使用RAG检索并回答

        Args:
            query: 用户查询

        Returns:
            tuple: (回答内容, 来源文档列表)
        """
        try:
            # 创建RAG链
            rag_chain = create_rag_chain(self.llm, self.retriever)

            # 执行RAG查询
            result = rag_chain.invoke({"query": query})

            # 提取答案和来源文档
            answer = result.get("result", "")
            sources = result.get("source_documents", [])

            return answer, sources
        except Exception as e:
            # RAG检索失败，降级为直接LLM回答
            fallback_answer = self._answer_chitchat(query)
            fallback_answer += f"\n\n（注意：检索系统暂时不可用，此回答未参考企业政策文档）"
            return fallback_answer, []


# 使用示例
if __name__ == "__main__":
    """测试Self-RAG系统"""
    print("测试Self-RAG系统...\n")

    from src.rag.loader import load_documents_from_text
    from src.rag.retriever import create_vectorstore, get_retriever

    # 准备测试文档
    test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离≥500公里：飞机经济舱
    """

    try:
        # 1. 准备RAG组件
        print("初始化RAG组件...")
        docs = load_documents_from_text(test_text, chunk_size=200)
        vectorstore = create_vectorstore(docs)
        retriever = get_retriever(vectorstore, k=3)

        # 2. 创建Self-RAG实例
        self_rag = SelfRAG(retriever=retriever)

        # 3. 测试不同类型的查询
        test_queries = [
            ("你好", "CHITCHAT"),
            ("去上海出差住宿能报多少钱", "FACTUAL"),
            ("今天天气怎么样", "CHITCHAT"),
            ("北京出差住宿标准", "FACTUAL")
        ]

        for query, expected_type in test_queries:
            print(f"\n{'='*60}")
            print(f"查询：{query}")
            print(f"预期类型：{expected_type}")

            result = self_rag.query(query)

            print(f"实际类型：{result['classification']['type']}")
            print(f"是否检索：{result['retrieved']}")
            print(f"回答：{result['answer'][:100]}...")
            if result['sources']:
                print(f"来源文档数：{len(result['sources'])}")

        print("\n✅ Self-RAG测试成功！")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
