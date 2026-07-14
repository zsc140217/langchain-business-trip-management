"""
分析VECTOR召回失败原因，并对比FUSION效果

目标：
1. 运行VECTOR评估，找出召回失败的查询
2. 分析失败原因（领域术语、多跳推理、长尾查询等）
3. 运行FUSION评估，对比效果
4. 生成详细的失败案例分析报告
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import DirectoryLoader, TextLoader

from src.rag.fusion_retriever import FusionRetriever


def analyze_failure_reasons(query_data: Dict, retrieved_docs: List[str]) -> str:
    """
    分析召回失败的可能原因

    返回失败原因分类：
    - domain_term: 领域术语匹配失败
    - multi_hop: 多跳推理查询
    - entity_recognition: 实体识别问题
    - long_tail: 长尾查询
    - no_relevant_doc: 知识库中无相关文档
    """
    query = query_data['query']
    expected_chunks = query_data['expected_chunks']

    # 检查是否是多跳推理（包含计算、多个条件）
    if any(keyword in query for keyword in ['预计', '总共', '多少次', '费用', '计算']):
        return "multi_hop"

    # 检查是否是长尾查询（季节+地点、特殊条件组合）
    if any(keyword in query for keyword in ['月', '淡旺季', '7-9月', '6-9月']) and any(keyword in query for keyword in ['出差', '标准']):
        return "long_tail"

    # 检查是否是实体识别问题（地名可能分词错误）
    if any(place in query for place in ['甘孜州', '张家口', '西藏']):
        return "entity_recognition"

    # 检查是否是领域术语问题
    domain_terms = ['高管', '住宿标准', '伙食补助', '公杂费', '差旅费', '审批', '报销']
    if any(term in query for term in domain_terms):
        # 检查检索结果中是否包含这些术语
        retrieved_text = ' '.join(retrieved_docs).lower()
        if not any(term.lower() in retrieved_text for term in domain_terms if term in query):
            return "domain_term"

    # 检查知识库是否有相关文档
    if not retrieved_docs or all(len(doc.strip()) < 10 for doc in retrieved_docs):
        return "no_relevant_doc"

    return "other"


def check_recall(retrieved_docs: List[str], expected_chunks: List[str]) -> bool:
    """检查是否召回"""
    if not expected_chunks:
        return len(retrieved_docs) == 0

    if not retrieved_docs:
        return False

    retrieved_text = ' '.join(retrieved_docs).lower()
    for chunk in expected_chunks:
        if chunk.lower() in retrieved_text:
            return True
    return False


def evaluate_method(vectorstore, test_queries: List[Dict], method: str) -> List[Dict]:
    """
    评估单个方法

    Args:
        vectorstore: 向量库
        test_queries: 测试查询
        method: 'vector' 或 'fusion'

    Returns:
        评估结果列表
    """
    print(f"\n{'='*80}")
    print(f"评估方法: {method.upper()}")
    print(f"{'='*80}\n")

    # 初始化检索器
    if method == 'fusion':
        # 加载文档用于BM25索引
        knowledge_base_path = project_root / 'data' / 'knowledge_base'
        try:
            loader = DirectoryLoader(
                str(knowledge_base_path),
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'}
            )
            documents = loader.load()
            bm25_retriever = BM25Retriever.from_documents(documents, k=5)
            print(f"   BM25检索器已创建（{len(documents)}个文档）")
            retrievers = [
                vectorstore.as_retriever(search_kwargs={"k": 5}),  # 向量检索（语义相似度）
                bm25_retriever,                                    # BM25关键词检索（精确匹配）
            ]
        except Exception as e:
            print(f"   警告：BM25初始化失败（{e}），仅使用向量检索")
            retrievers = [vectorstore.as_retriever(search_kwargs={"k": 5})]
        
        retriever = FusionRetriever(retrievers)

    results = []

    for i, query_data in enumerate(test_queries, 1):
        query = query_data['query']
        expected_chunks = query_data['expected_chunks']

        # 只评估需要检索的查询（跳过闲聊和工具调用）
        if query_data['retrieval_type'] == 'NONE':
            print(f"[{i:2d}/50] SKIP (闲聊/工具): {query}")
            continue

        print(f"[{i:2d}/50] {query[:50]}...", end=' ')

        # 检索
        if method == 'vector':
            docs = vectorstore.similarity_search(query, k=5)
        else:  # fusion
            docs = retriever.get_relevant_documents(query)[:5]

        retrieved_docs = [doc.page_content for doc in docs]

        # 检查召回
        recall_at_5 = check_recall(retrieved_docs, expected_chunks)

        result = {
            'id': query_data['id'],
            'query': query,
            'expected_chunks': expected_chunks,
            'retrieved_docs': [doc[:200] for doc in retrieved_docs],  # 截断保存
            'recall_at_5': recall_at_5,
            'difficulty': query_data['difficulty'],
            'category': query_data['category'],
            'retrieval_type': query_data['retrieval_type']
        }

        # 如果失败，分析原因
        if not recall_at_5:
            result['failure_reason'] = analyze_failure_reasons(query_data, retrieved_docs)
            print(f"[FAIL] ({result['failure_reason']})")
        else:
            result['failure_reason'] = None
            print("[OK]")

        results.append(result)

    return results


def compare_methods(vector_results: List[Dict], fusion_results: List[Dict]):
    """对比两种方法的效果"""
    print(f"\n{'='*80}")
    print("对比分析")
    print(f"{'='*80}\n")

    # 计算召回率
    vector_recall = sum(r['recall_at_5'] for r in vector_results) / len(vector_results) * 100
    fusion_recall = sum(r['recall_at_5'] for r in fusion_results) / len(fusion_results) * 100

    print(f"VECTOR召回率: {vector_recall:.1f}%")
    print(f"FUSION召回率: {fusion_recall:.1f}%")
    print(f"提升幅度: {fusion_recall - vector_recall:+.1f}% ({(fusion_recall/vector_recall - 1)*100:+.1f}%)")

    # 统计VECTOR失败原因
    print(f"\n{'='*80}")
    print("VECTOR失败原因分布")
    print(f"{'='*80}\n")

    failure_stats = defaultdict(int)
    failed_queries = [r for r in vector_results if not r['recall_at_5']]

    for result in failed_queries:
        failure_stats[result['failure_reason']] += 1

    total_failures = len(failed_queries)
    print(f"总失败数: {total_failures}/{len(vector_results)} ({total_failures/len(vector_results)*100:.1f}%)\n")

    reason_names = {
        'domain_term': '领域术语匹配失败',
        'multi_hop': '多跳推理查询',
        'entity_recognition': '实体识别问题',
        'long_tail': '长尾查询',
        'no_relevant_doc': '知识库无相关文档',
        'other': '其他原因'
    }

    for reason, count in sorted(failure_stats.items(), key=lambda x: x[1], reverse=True):
        percent = count / total_failures * 100
        reason_name = reason_names.get(reason, reason)
        print(f"  {reason_name:20s}: {count:2d} ({percent:5.1f}%)")

    # 找出FUSION改进的查询
    print(f"\n{'='*80}")
    print("FUSION改进的查询（VECTOR失败 → FUSION成功）")
    print(f"{'='*80}\n")

    improved_queries = []
    for v_result, f_result in zip(vector_results, fusion_results):
        if not v_result['recall_at_5'] and f_result['recall_at_5']:
            improved_queries.append({
                'id': v_result['id'],
                'query': v_result['query'],
                'failure_reason': v_result['failure_reason']
            })

    if improved_queries:
        print(f"改进数量: {len(improved_queries)}/{total_failures} ({len(improved_queries)/total_failures*100:.1f}%)\n")
        for item in improved_queries:
            print(f"  [{item['id']:2d}] {item['query']}")
            print(f"       原因: {reason_names.get(item['failure_reason'], item['failure_reason'])}\n")
    else:
        print("无改进（FUSION与VECTOR效果相同）\n")

    # 按难度统计
    print(f"\n{'='*80}")
    print("按难度分组召回率对比")
    print(f"{'='*80}\n")

    for difficulty in ['EASY', 'MEDIUM', 'HARD']:
        v_difficulty = [r for r in vector_results if r['difficulty'] == difficulty]
        f_difficulty = [r for r in fusion_results if r['difficulty'] == difficulty]

        if v_difficulty:
            v_recall_diff = sum(r['recall_at_5'] for r in v_difficulty) / len(v_difficulty) * 100
            f_recall_diff = sum(r['recall_at_5'] for r in f_difficulty) / len(f_difficulty) * 100

            print(f"{difficulty:8s}: VECTOR {v_recall_diff:5.1f}%  →  FUSION {f_recall_diff:5.1f}%  (Δ {f_recall_diff - v_recall_diff:+.1f}%)")


def main():
    """主函数"""
    # 设置stdout编码为utf-8
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*80)
    print("RAG召回失败原因分析 & VECTOR vs FUSION对比")
    print("="*80)

    # 加载测试查询
    test_queries_path = project_root / 'data' / 'test_queries.json'
    print(f"\n加载测试查询: {test_queries_path}")
    with open(test_queries_path, 'r', encoding='utf-8') as f:
        test_queries = json.load(f)
    print(f"[OK] 加载了 {len(test_queries)} 个测试查询")

    # 加载向量库
    print(f"\n加载向量库...")
    embeddings = DashScopeEmbeddings(model='text-embedding-v2')
    vectorstore_path = project_root / 'src' / 'data' / 'vectorstore'
    vectorstore = FAISS.load_local(
        str(vectorstore_path),
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"[OK] 向量库加载完成，共 {vectorstore.index.ntotal} 个向量")

    # 评估VECTOR方法
    vector_results = evaluate_method(vectorstore, test_queries, 'vector')

    # 评估FUSION方法
    fusion_results = evaluate_method(vectorstore, test_queries, 'fusion')

    # 对比分析
    compare_methods(vector_results, fusion_results)

    # 保存详细结果
    output_path = project_root / 'tests' / 'evaluation' / 'recall_analysis.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'vector': vector_results,
            'fusion': fusion_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print(f"[OK] 详细结果已保存: {output_path}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
