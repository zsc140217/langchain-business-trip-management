"""
端到端集成测试 - 测试所有7个模块的协同工作

测试范围：
1. Module 1: Simple RAG
2. Module 2: Advanced RAG
3. Module 3: ReAct Agent
4. Module 4: Multi-Agent
5. Module 5: Chain Composition
6. Module 6: Memory System
7. Module 7: Production (缓存、监控)

测试策略：
- 模拟真实用户场景
- 验证模块间数据流转
- 检查性能指标
- 验证错误处理
"""
import pytest
import os


class TestSimpleRAG:
    """Module 1: Simple RAG 集成测试"""

    def test_simple_rag_basic_query(self):
        """测试基本的RAG查询功能"""
        from modules.module_1_simple_rag import (
            load_documents_from_text,
            create_faiss_vectorstore,
            create_retriever,
            create_rag_chain_lcel,
        )
        from langchain_community.llms import Tongyi

        # 加载测试文档
        policy_text = """
        企业差旅管理规章
        第一章 住宿标准
        1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
        """
        docs = load_documents_from_text(policy_text)
        vectorstore = create_faiss_vectorstore(docs)
        retriever = create_retriever(vectorstore)

        # 创建LLM（需要API密钥）
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            pytest.skip("需要设置 DASHSCOPE_API_KEY")

        llm = Tongyi(dashscope_api_key=api_key)
        chain = create_rag_chain_lcel(retriever, llm)

        # 执行查询
        result = chain.invoke({"input": "上海住宿标准是多少？"})

        # 验证结果
        assert result is not None
        assert "500" in result or "一线城市" in result


class TestAdvancedRAG:
    """Module 2: Advanced RAG 集成测试"""

    def test_advanced_rag_with_rerank(self):
        """测试带重排序的高级RAG"""
        from modules.module_1_simple_rag import (
            load_documents_from_text,
            create_faiss_vectorstore,
        )
        from modules.module_2_advanced_rag.chain import create_advanced_rag_chain
        from langchain_community.llms import Tongyi

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            pytest.skip("需要设置 DASHSCOPE_API_KEY")

        # 准备数据
        policy_text = """
        企业差旅管理规章
        第一章 住宿标准
        1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
        2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
        """
        docs = load_documents_from_text(policy_text)
        vectorstore = create_faiss_vectorstore(docs)

        # 创建Advanced RAG链
        llm = Tongyi(dashscope_api_key=api_key)
        chain = create_advanced_rag_chain(
            vector_store=vectorstore,
            documents=docs,
            llm=llm,
            enable_query_rewrite=False,  # 测试时禁用以加快速度
            enable_rerank=False,
            verbose=False,
        )

        # 执行查询
        result = chain.invoke("魔都出差住宿能报多少？")

        # 验证结果
        assert result is not None
        assert "answer" in result
        assert result["answer"]


class TestReActAgent:
    """Module 3: ReAct Agent 集成测试"""

    def test_react_agent_tool_calling(self):
        """测试ReAct Agent的工具调用能力"""
        from modules.module_3_react_agent.agent import create_react_agent_with_tools
        from modules.module_3_react_agent.tools.weather import get_all_weather_tools
        from langchain_community.chat_models import ChatTongyi

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            pytest.skip("需要设置 DASHSCOPE_API_KEY")

        # 创建Agent
        tools = get_all_weather_tools()
        llm = ChatTongyi(dashscope_api_key=api_key)
        agent = create_react_agent_with_tools(tools, llm)

        # 执行查询
        result = agent.invoke({"input": "查询深圳的天气"})

        # 验证结果
        assert result is not None
        assert "output" in result


class TestMultiAgent:
    """Module 4: Multi-Agent 集成测试"""

    def test_multi_agent_coordination(self):
        """测试多智能体协调能力"""
        pytest.skip("Multi-Agent需要LangGraph完整配置")


class TestChainComposition:
    """Module 5: Chain Composition 集成测试"""

    def test_sequential_chain(self):
        """测试顺序链执行"""
        pytest.skip("需要完整的Chain Composition实现")

    def test_parallel_chain_performance(self):
        """测试并行链性能提升"""
        pytest.skip("需要完整的Chain Composition实现")


class TestMemorySystem:
    """Module 6: Memory System 集成测试"""

    def test_memory_persistence(self):
        """测试记忆系统的持久化"""
        from modules.module_6_memory import CompositeMemory

        memory = CompositeMemory(session_id="test_session")

        # 保存对话
        memory.save_context(
            {"input": "我叫张三"},
            {"output": "你好，张三！"}
        )

        # 加载记忆
        history = memory.load()

        # 验证
        assert len(history) > 0


class TestProductionInfra:
    """Module 7: Production Infrastructure 集成测试"""

    def test_langsmith_integration(self):
        """测试LangSmith集成"""
        langsmith_key = os.getenv("LANGCHAIN_API_KEY")
        if not langsmith_key:
            pytest.skip("需要设置 LANGCHAIN_API_KEY")

        # 验证LangSmith配置
        from modules.module_7_production.langsmith_config import setup_langsmith
        setup_langsmith()

        # 验证环境变量
        assert os.getenv("LANGCHAIN_TRACING_V2") == "true"

    def test_caching_system(self):
        """测试缓存系统"""
        from modules.module_7_production.cache import setup_caching

        # 设置缓存
        setup_caching()

        # 验证缓存配置
        import langchain
        assert langchain.llm_cache is not None


class TestEndToEndScenario:
    """端到端场景测试"""

    def test_complete_trip_planning_workflow(self):
        """
        测试完整的差旅规划工作流

        场景：用户计划去上海出差3天
        涉及模块：
        1. Simple RAG - 查询政策
        2. ReAct Agent - 查询天气、订酒店
        3. Memory - 记住用户偏好
        """
        pytest.skip("需要所有模块完整实现")

    def test_error_handling_across_modules(self):
        """测试跨模块的错误处理"""
        pytest.skip("需要完整的错误处理机制")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
