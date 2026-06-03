"""
Module 1: Simple RAG - Quick Test
快速测试脚本（无emoji，适配Windows）
"""
import os
import sys

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from loader import load_documents_from_text
from retriever import create_faiss_vectorstore, create_retriever
from chain import create_rag_chain_lcel


def test_module_1():
    """测试Module 1的核心功能"""
    print("="*60)
    print("Module 1: Simple RAG - 快速测试")
    print("="*60 + "\n")

    # 测试数据
    policy_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离>=500公里：飞机经济舱

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
4. 总计：130元/天
    """

    try:
        # 1. 加载文档
        print("[1/4] 加载文档...")
        docs = load_documents_from_text(policy_text, chunk_size=300, chunk_overlap=50)
        print(f"      文档块数: {len(docs)}")

        # 2. 创建向量存储
        print("\n[2/4] 创建向量存储...")
        vectorstore = create_faiss_vectorstore(docs)
        print("      向量存储创建成功")

        # 3. 创建检索器
        print("\n[3/4] 创建检索器...")
        retriever = create_retriever(vectorstore, k=3)
        print("      检索器创建成功")

        # 4. 创建RAG链
        print("\n[4/4] 创建RAG链...")
        rag_chain = create_rag_chain_lcel(retriever)
        print("      RAG链创建成功")

        # 测试问答
        print("\n" + "="*60)
        print("测试问答")
        print("="*60)

        questions = [
            "去上海出差，酒店最多能报销多少钱？",
            "从北京到广州出差应该坐什么交通工具？",
            "出差期间每天的餐补是多少？"
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n问题 {i}: {question}")
            answer = rag_chain.invoke(question)
            print(f"回答: {answer}")

        print("\n" + "="*60)
        print("测试通过！Module 1实现成功！")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n请检查:")
        print("1. 环境变量DASHSCOPE_API_KEY是否已设置")
        print("2. API Key是否有效且有余额")
        print("3. 是否已安装所有依赖")
        return False


if __name__ == "__main__":
    success = test_module_1()
    sys.exit(0 if success else 1)
