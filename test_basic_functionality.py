"""
基础功能测试 - 验证重构后的项目可以运行
"""
import os
import sys

# 设置 API Key
os.environ["DASHSCOPE_API_KEY"] = "sk-8fd736225586468eb7f4de705be7e76c"

# 添加 src 到路径
sys.path.insert(0, 'src')

print("=" * 70)
print("差旅管理系统 - 基础功能测试")
print("=" * 70)

# 测试 Module 1: Simple RAG
print("\n【测试 1】Module 1: Simple RAG")
try:
    from modules.module_1_simple_rag import load_documents_from_text, create_faiss_vectorstore
    
    # 准备测试文档
    test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚
    """
    
    docs = load_documents_from_text(test_text, chunk_size=200)
    print(f"  ✅ 文档加载成功，切分为 {len(docs)} 个块")
    
    vectorstore = create_faiss_vectorstore(docs)
    print(f"  ✅ 向量存储创建成功")
    
except Exception as e:
    print(f"  ❌ 失败: {e}")

# 测试 Module 2: Advanced RAG
print("\n【测试 2】Module 2: Advanced RAG")
try:
    from modules.module_2_advanced_rag.chain import create_advanced_rag_chain
    print("  ✅ Advanced RAG 模块导入成功")
except Exception as e:
    print(f"  ❌ 失败: {e}")

# 测试 Module 3: ReAct Agent
print("\n【测试 3】Module 3: ReAct Agent")
try:
    from modules.module_3_react_agent import create_react_agent_with_tools
    print("  ✅ ReAct Agent 模块导入成功")
except Exception as e:
    print(f"  ❌ 失败: {e}")

# 测试 Module 6: Memory System
print("\n【测试 4】Module 6: Memory System")
try:
    from modules.module_6_memory import BufferMemory
    memory = BufferMemory(max_turns=5)
    memory.add_user_message("你好")
    memory.add_ai_message("您好，有什么可以帮您？")
    messages = memory.get_messages()
    print(f"  ✅ Memory 系统工作正常，存储了 {len(messages)} 条消息")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
