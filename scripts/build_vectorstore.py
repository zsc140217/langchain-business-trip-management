"""
构建向量数据库
从data/knowledge_base目录加载文档并创建FAISS向量存储
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 加载环境变量
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from rag.loader import load_documents

# 路径配置
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "knowledge_base"
VECTORSTORE_PATH = PROJECT_ROOT / "src" / "data" / "vectorstore"


def build_vectorstore():
    """构建向量数据库"""
    print("=" * 60)
    print("构建向量数据库")
    print("=" * 60)
    print(f"知识库路径: {KNOWLEDGE_BASE_PATH}")
    print(f"输出路径: {VECTORSTORE_PATH}")
    print("")

    # 1. 加载文档（使用更新后的loader，支持Markdown）
    print("Phase 1: 加载文档")
    print("-" * 60)

    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"[X] 错误: 知识库路径不存在: {KNOWLEDGE_BASE_PATH}")
        return

    documents = load_documents(str(KNOWLEDGE_BASE_PATH))

    if not documents:
        print("[X] 错误: 没有找到任何文档！")
        return

    print("")

    # 2. 创建Embedding
    print("Phase 2: 创建Embedding模型")
    print("-" * 60)
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        print("[X] 错误: 缺少 DASHSCOPE_API_KEY 环境变量")
        return

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key=api_key
    )
    print("[OK] Embedding模型创建成功")
    print("")

    # 3. 构建向量存储
    print("Phase 3: 构建FAISS向量存储")
    print("-" * 60)
    vectorstore = FAISS.from_documents(documents, embeddings)
    print(f"[OK] 向量存储构建完成 ({len(documents)} 个文档块)")
    print("")

    # 4. 保存到磁盘
    print("Phase 4: 保存到磁盘")
    print("-" * 60)
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_PATH))
    print(f"[OK] 向量存储已保存: {VECTORSTORE_PATH}")
    print("")

    print("=" * 60)
    print("[OK] 向量数据库构建完成")
    print("=" * 60)
    print(f"文档块数: {len(documents)}")
    print(f"Embedding模型: text-embedding-v2")
    print(f"向量存储: FAISS")
    print("")


if __name__ == "__main__":
    try:
        build_vectorstore()
    except Exception as e:
        print(f"\n[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
