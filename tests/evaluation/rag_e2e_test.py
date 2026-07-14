"""
RAG端到端自动评估脚本

功能：
1. 测试4种检索配置（纯向量、纯图谱、融合检索、智能路由）
2. 计算评估指标（Recall@K、MRR、Accuracy@1、延迟、成本）
3. 生成HTML评估报告
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
import traceback

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from neo4j import GraphDatabase

from src.rag.fusion_retriever import FusionRetriever
from src.rag.graph_retriever import GraphRetriever
from src.agents.intelligent_router import IntelligentRouter


@dataclass
class EvaluationResult:
    """单个查询的评估结果"""
    query_id: int
    query: str
    query_type: str
    difficulty: str
    retrieval_type: str
    category: str

    # 检索结果
    retrieved_docs: List[str]
    retrieval_method: str

    # 评估指标
    recall_at_1: bool
    recall_at_3: bool
    recall_at_5: bool
    reciprocal_rank: float  # MRR分子

    # 性能指标
    latency_ms: float

    # 失败信息
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class RAGEvaluator:
    """RAG端到端评估器"""

    def __init__(self):
        print("初始化评估器...", flush=True)

        # 加载向量库
        print("[1/3] 加载向量库...", flush=True)
        self.embeddings = DashScopeEmbeddings(model='text-embedding-v2')
        vectorstore_path = project_root / 'src' / 'data' / 'vectorstore'
        print(f"   向量库路径: {vectorstore_path}", flush=True)
        self.vectorstore = FAISS.load_local(
            str(vectorstore_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"   向量数量: {self.vectorstore.index.ntotal}", flush=True)

        # 初始化图谱检索器
        print("[2/3] 初始化图谱检索器...", flush=True)
        self.graph_retriever = GraphRetriever(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="neo4j123"
        )
        self.graph_driver = self.graph_retriever.driver
        print("   [OK] Neo4j连接成功", flush=True)

        # 初始化融合检索器和智能路由器
        print("[3/3] 初始化检索器...", flush=True)
        self.fusion_retriever = FusionRetriever([
            self.vectorstore.as_retriever(search_kwargs={"k": 5}),
        ])

        # 初始化智能路由器（需要llm和retriever）
        from src.models.llm import get_llm
        self.llm = get_llm()
        self.intelligent_router = IntelligentRouter(
            llm=self.llm,
            retriever=self.fusion_retriever
        )
        print("   [OK] 初始化完成", flush=True)

        print(flush=True)

    def close(self):
        """关闭连接"""
        self.graph_driver.close()

    def evaluate_query(
        self,
        query_data: Dict[str, Any],
        retrieval_method: str
    ) -> EvaluationResult:
        """
        评估单个查询

        Args:
            query_data: 查询数据（来自test_queries.json）
            retrieval_method: 检索方法（vector/graph/fusion/intelligent）

        Returns:
            EvaluationResult: 评估结果
        """
        query = query_data['query']
        expected_chunks = query_data['expected_chunks']

        start_time = time.time()
        error = None
        retrieved_docs = []

        try:
            # 根据检索方法获取文档
            if retrieval_method == 'vector':
                docs = self.vectorstore.similarity_search(query, k=5)
                retrieved_docs = [doc.page_content for doc in docs]

            elif retrieval_method == 'graph':
                docs = self.graph_retriever.retrieve(query, top_k=5)
                retrieved_docs = [doc.page_content for doc in docs]

            elif retrieval_method == 'fusion':
                docs = self.fusion_retriever.get_relevant_documents(query)[:5]
                retrieved_docs = [doc.page_content for doc in docs]

            elif retrieval_method == 'intelligent':
                # 使用智能路由器
                result = self.intelligent_router.route(query)

                # 智能路由器返回的是 {'route': 'chitchat'/'tool_call'/'graph'/..., 'retrieved': bool, 'sources': [...]}
                route = result.get('route', '')

                if route in ['chitchat', 'tool_call']:
                    # 闲聊或工具调用，不检索
                    retrieved_docs = []
                elif result.get('retrieved', False):
                    # 已经检索过，使用返回的sources
                    sources = result.get('sources', [])
                    if sources and hasattr(sources[0], 'page_content'):
                        retrieved_docs = [doc.page_content for doc in sources[:5]]
                    else:
                        # 可能是字符串列表
                        retrieved_docs = sources[:5] if isinstance(sources, list) else []
                else:
                    # 需要检索但还没检索（理论上不应该到这里）
                    retrieved_docs = []

        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            print(f"   [ERROR] {error}")

        latency_ms = (time.time() - start_time) * 1000

        # 计算召回率
        recall_at_1 = self._check_recall(retrieved_docs[:1], expected_chunks)
        recall_at_3 = self._check_recall(retrieved_docs[:3], expected_chunks)
        recall_at_5 = self._check_recall(retrieved_docs[:5], expected_chunks)

        # 计算MRR（Mean Reciprocal Rank）
        reciprocal_rank = self._calculate_reciprocal_rank(retrieved_docs, expected_chunks)

        return EvaluationResult(
            query_id=query_data['id'],
            query=query,
            query_type=query_data['query_type'],
            difficulty=query_data['difficulty'],
            retrieval_type=query_data['retrieval_type'],
            category=query_data['category'],
            retrieved_docs=retrieved_docs[:3],  # 只保存前3个，节省空间
            retrieval_method=retrieval_method,
            recall_at_1=recall_at_1,
            recall_at_3=recall_at_3,
            recall_at_5=recall_at_5,
            reciprocal_rank=reciprocal_rank,
            latency_ms=latency_ms,
            error=error
        )

    def _check_recall(self, retrieved_docs: List[str], expected_chunks: List[str]) -> bool:
        """
        检查是否召回了预期的文档块

        对于闲聊和工具查询（expected_chunks为空），返回True表示正确不检索
        """
        if not expected_chunks:
            # 闲聊/工具查询，不应该检索文档
            return len(retrieved_docs) == 0

        if not retrieved_docs:
            return False

        # 检查是否至少有一个预期关键词出现在检索结果中
        retrieved_text = ' '.join(retrieved_docs).lower()
        for chunk in expected_chunks:
            if chunk.lower() in retrieved_text:
                return True
        return False

    def _calculate_reciprocal_rank(self, retrieved_docs: List[str], expected_chunks: List[str]) -> float:
        """
        计算倒数排名（Reciprocal Rank）

        返回第一个相关文档的排名倒数，如果没有相关文档则返回0
        """
        if not expected_chunks:
            # 闲聊/工具查询
            return 1.0 if len(retrieved_docs) == 0 else 0.0

        if not retrieved_docs:
            return 0.0

        for rank, doc in enumerate(retrieved_docs, start=1):
            doc_lower = doc.lower()
            if any(chunk.lower() in doc_lower for chunk in expected_chunks):
                return 1.0 / rank
        return 0.0

    def run_evaluation(
        self,
        test_queries: List[Dict[str, Any]],
        retrieval_method: str
    ) -> List[EvaluationResult]:
        """
        运行评估

        Args:
            test_queries: 测试查询列表
            retrieval_method: 检索方法

        Returns:
            List[EvaluationResult]: 评估结果列表
        """
        print(f"\n{'='*80}")
        print(f"开始评估: {retrieval_method.upper()}")
        print(f"{'='*80}")

        results = []
        for i, query_data in enumerate(test_queries, 1):
            print(f"[{i}/{len(test_queries)}] {query_data['query'][:40]}...")
            result = self.evaluate_query(query_data, retrieval_method)
            results.append(result)

        return results


def calculate_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    """
    计算聚合指标

    Args:
        results: 评估结果列表

    Returns:
        Dict: 聚合指标
    """
    total = len(results)
    successful = [r for r in results if r.error is None]

    if not successful:
        return {
            'total_queries': total,
            'successful_queries': 0,
            'success_rate': 0.0,
        }

    return {
        'total_queries': total,
        'successful_queries': len(successful),
        'success_rate': len(successful) / total * 100,

        # 召回率
        'recall_at_1': sum(r.recall_at_1 for r in successful) / len(successful) * 100,
        'recall_at_3': sum(r.recall_at_3 for r in successful) / len(successful) * 100,
        'recall_at_5': sum(r.recall_at_5 for r in successful) / len(successful) * 100,

        # MRR
        'mrr': sum(r.reciprocal_rank for r in successful) / len(successful),

        # 延迟（毫秒）
        'latency_p50': sorted([r.latency_ms for r in successful])[len(successful) // 2],
        'latency_p95': sorted([r.latency_ms for r in successful])[int(len(successful) * 0.95)],
        'latency_avg': sum(r.latency_ms for r in successful) / len(successful),

        # 错误统计
        'error_count': total - len(successful),
    }


def calculate_metrics_by_group(
    results: List[EvaluationResult],
    group_by: str
) -> Dict[str, Dict[str, Any]]:
    """
    按组计算指标

    Args:
        results: 评估结果列表
        group_by: 分组字段（difficulty/query_type/retrieval_type）

    Returns:
        Dict: 分组指标
    """
    groups = defaultdict(list)
    for result in results:
        group_key = getattr(result, group_by)
        groups[group_key].append(result)

    return {
        group_key: calculate_metrics(group_results)
        for group_key, group_results in groups.items()
    }


def generate_html_report(
    all_results: Dict[str, List[EvaluationResult]],
    output_path: Path
):
    """
    生成HTML评估报告

    Args:
        all_results: 所有检索方法的评估结果
        output_path: 输出路径
    """
    print(f"\n生成HTML报告: {output_path}")

    # 计算每种方法的聚合指标
    method_metrics = {
        method: calculate_metrics(results)
        for method, results in all_results.items()
    }

    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG端到端评估报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .metric-best {{
            background-color: #d4edda;
            font-weight: bold;
        }}
        .metric-worst {{
            background-color: #f8d7da;
        }}
        .summary {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RAG端到端评估报告</h1>
        <p class="timestamp">生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h3>📊 测试概览</h3>
            <ul>
                <li>测试查询数: {len(list(all_results.values())[0])}个</li>
                <li>检索方法: {', '.join(all_results.keys())}</li>
                <li>评估指标: Recall@1/3/5, MRR, 延迟</li>
            </ul>
        </div>

        <h2>🎯 总体指标对比</h2>
        <table>
            <tr>
                <th>检索方法</th>
                <th>成功率</th>
                <th>Recall@1</th>
                <th>Recall@3</th>
                <th>Recall@5</th>
                <th>MRR</th>
                <th>延迟P50</th>
                <th>延迟P95</th>
            </tr>
"""

    # 找出每列的最佳值
    best_values = {
        'recall_at_1': max(m.get('recall_at_1', 0) for m in method_metrics.values()),
        'recall_at_3': max(m.get('recall_at_3', 0) for m in method_metrics.values()),
        'recall_at_5': max(m.get('recall_at_5', 0) for m in method_metrics.values()),
        'mrr': max(m.get('mrr', 0) for m in method_metrics.values()),
        'latency_p50': min(m.get('latency_p50', float('inf')) for m in method_metrics.values()),
    }

    for method, metrics in method_metrics.items():
        html += "<tr>"
        html += f"<td><strong>{method.upper()}</strong></td>"
        html += f"<td>{metrics.get('success_rate', 0):.1f}%</td>"

        # Recall@1
        r1 = metrics.get('recall_at_1', 0)
        css_class = 'metric-best' if r1 == best_values['recall_at_1'] else ''
        html += f"<td class='{css_class}'>{r1:.1f}%</td>"

        # Recall@3
        r3 = metrics.get('recall_at_3', 0)
        css_class = 'metric-best' if r3 == best_values['recall_at_3'] else ''
        html += f"<td class='{css_class}'>{r3:.1f}%</td>"

        # Recall@5
        r5 = metrics.get('recall_at_5', 0)
        css_class = 'metric-best' if r5 == best_values['recall_at_5'] else ''
        html += f"<td class='{css_class}'>{r5:.1f}%</td>"

        # MRR
        mrr = metrics.get('mrr', 0)
        css_class = 'metric-best' if mrr == best_values['mrr'] else ''
        html += f"<td class='{css_class}'>{mrr:.3f}</td>"

        # 延迟
        lat_p50 = metrics.get('latency_p50', 0)
        css_class = 'metric-best' if lat_p50 == best_values['latency_p50'] else ''
        html += f"<td class='{css_class}'>{lat_p50:.0f}ms</td>"
        html += f"<td>{metrics.get('latency_p95', 0):.0f}ms</td>"

        html += "</tr>"

    html += """
        </table>

        <h2>📈 按难度分组</h2>
"""

    # 按难度分组的指标
    for method, results in all_results.items():
        metrics_by_difficulty = calculate_metrics_by_group(results, 'difficulty')

        html += f"<h3>{method.upper()}</h3>"
        html += "<table>"
        html += "<tr><th>难度</th><th>数量</th><th>Recall@5</th><th>MRR</th><th>延迟P50</th></tr>"

        for difficulty in ['EASY', 'MEDIUM', 'HARD']:
            if difficulty in metrics_by_difficulty:
                m = metrics_by_difficulty[difficulty]
                html += f"""<tr>
                    <td>{difficulty}</td>
                    <td>{m['total_queries']}</td>
                    <td>{m.get('recall_at_5', 0):.1f}%</td>
                    <td>{m.get('mrr', 0):.3f}</td>
                    <td>{m.get('latency_p50', 0):.0f}ms</td>
                </tr>"""

        html += "</table>"

    html += """
    </div>
</body>
</html>
"""

    # 写入文件
    output_path.write_text(html, encoding='utf-8')
    print(f"[OK] 报告已生成: {output_path}")


def main():
    """主函数"""
    # 配置stdout编码为utf-8
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("RAG端到端自动评估")
    print("="*80)

    # 加载测试查询
    test_queries_path = project_root / 'data' / 'test_queries.json'
    print(f"\n加载测试查询: {test_queries_path}")
    with open(test_queries_path, 'r', encoding='utf-8') as f:
        test_queries = json.load(f)
    print(f"[OK] 加载了 {len(test_queries)} 个测试查询")

    # 初始化评估器
    evaluator = RAGEvaluator()

    try:
        # 运行评估（4种方法）
        all_results = {}

        methods = ['vector', 'graph', 'fusion', 'intelligent']
        for method in methods:
            results = evaluator.run_evaluation(test_queries, method)
            all_results[method] = results

            # 打印简要统计
            metrics = calculate_metrics(results)
            print(f"\n{'='*80}")
            print(f"[统计] {method.upper()} 评估结果")
            print(f"{'='*80}")
            print(f"成功率: {metrics.get('success_rate', 0):.1f}%")
            print(f"Recall@5: {metrics.get('recall_at_5', 0):.1f}%")
            print(f"MRR: {metrics.get('mrr', 0):.3f}")
            print(f"延迟P50: {metrics.get('latency_p50', 0):.0f}ms")

        # 保存原始结果（JSON）
        output_dir = project_root / 'tests' / 'evaluation'
        output_dir.mkdir(parents=True, exist_ok=True)

        json_output = output_dir / 'rag_e2e_results.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump({
                method: [r.to_dict() for r in results]
                for method, results in all_results.items()
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 原始结果已保存: {json_output}")

        # 生成HTML报告
        html_output = output_dir / 'rag_e2e_report.html'
        generate_html_report(all_results, html_output)

        print(f"\n{'='*80}")
        print("[OK] 评估完成")
        print(f"{'='*80}")

    finally:
        evaluator.close()


if __name__ == '__main__':
    main()
