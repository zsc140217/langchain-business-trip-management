"""
知识图谱构建 CLI 工具

从知识库文档构建知识图谱的命令行工具

用法：
    python scripts/build_graph.py --data-dir data/knowledge_base/
    python scripts/build_graph.py --rebuild  # 清空并重建
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")

from src.rag.graph_builder import GraphBuilder
from src.rag.loader import load_documents


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="从知识库文档构建知识图谱"
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/knowledge_base/",
        help="知识库文档目录（默认: data/knowledge_base/）"
    )

    parser.add_argument(
        "--neo4j-uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j 连接 URI（默认: bolt://localhost:7687）"
    )

    parser.add_argument(
        "--neo4j-user",
        type=str,
        default="neo4j",
        help="Neo4j 用户名（默认: neo4j）"
    )

    parser.add_argument(
        "--neo4j-password",
        type=str,
        default="neo4j123",
        help="Neo4j 密码（默认: neo4j123）"
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="清空现有图谱并重建"
    )

    return parser.parse_args()


def load_knowledge_base(data_dir: str) -> List[Dict]:
    """
    加载知识库文档

    Args:
        data_dir: 文档目录

    Returns:
        List[Dict]: 文档列表
    """
    print(f"\n加载知识库文档：{data_dir}")

    if not os.path.exists(data_dir):
        print(f"[错误] 目录不存在: {data_dir}")
        return []

    # 使用现有的文档加载器
    try:
        docs = load_documents(data_dir)
        print(f"[成功] 加载了 {len(docs)} 个文档")

        # 转换为字典格式
        documents = []
        for i, doc in enumerate(docs):
            documents.append({
                "id": f"doc_{i:03d}",
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return documents

    except Exception as e:
        print(f"[错误] 加载文档失败: {e}")
        return []


def main():
    """主函数"""
    args = parse_args()

    print("=" * 60)
    print("知识图谱构建工具")
    print("=" * 60)

    # 加载文档
    documents = load_knowledge_base(args.data_dir)
    if not documents:
        print("\n[错误] 未找到文档，退出")
        sys.exit(1)

    # 连接 Neo4j 并构建图谱
    try:
        with GraphBuilder(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password
        ) as builder:
            # 创建索引
            print("\n创建索引...")
            builder.create_indexes()

            # 是否重建
            if args.rebuild:
                print("\n清空现有图谱...")
                builder.clear_graph()

            # 构建图谱
            print("\n开始构建知识图谱...")
            builder.build_from_documents(documents)

            # 显示统计信息
            print("\n获取图谱统计...")
            stats = builder.get_statistics()

            print("\n" + "=" * 60)
            print("图谱构建完成！")
            print("=" * 60)
            print(f"文档数: {stats['documents']}")
            print(f"实体数: {stats['entities']}")
            print(f"关系数: {stats['relationships']}")
            print(f"\n实体类型分布:")
            for entity_type, count in stats['entity_types'].items():
                print(f"  - {entity_type}: {count}")
            print("=" * 60)

    except Exception as e:
        print(f"\n[错误] 构建图谱失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
