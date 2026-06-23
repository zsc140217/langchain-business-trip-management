"""
Embedding评估器模块

支持两种Embedding模型的评估：
1. DashScope API (text-embedding-v2) - 通义千问通用模型
2. Finetuned Local Model (bge-large-zh-travel-finetuned) - 差旅领域微调模型
"""

import time
import numpy as np
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod
import logging

# DashScope
from langchain_community.embeddings import DashScopeEmbeddings

# Sentence Transformers (本地模型)
from sentence_transformers import SentenceTransformer

# 导入metrics模块
from metrics import calculate_all_metrics

logger = logging.getLogger(__name__)


class EmbeddingEvaluator(ABC):
    """Embedding评估器基类"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None

    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量矩阵 (n_texts, embedding_dim)
        """
        pass

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def evaluate(
        self,
        queries: List[Dict[str, Any]],
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        评估Embedding模型性能

        Args:
            queries: 查询列表，每个查询包含 {id, text, expected_doc_id, difficulty}
            documents: 文档列表，每个文档包含 {id, text}

        Returns:
            评估结果字典，包含：
            - model_name: 模型名称
            - metrics: 整体指标
            - difficulty_stats: 按难度分组统计
            - detailed_results: 详细结果列表
            - eval_time: 评估耗时(秒)
        """
        start_time = time.time()

        logger.info(f"开始评估模型: {self.model_name}")
        logger.info(f"查询数量: {len(queries)}, 文档数量: {len(documents)}")

        # 1. 编码所有文档
        doc_texts = [doc['text'] for doc in documents]
        doc_embeddings = self.encode(doc_texts)
        logger.info(f"文档编码完成，向量维度: {doc_embeddings.shape}")

        # 2. 逐个查询评估
        ranks = []  # 正确文档的排名
        detailed_results = []

        # 按难度分组
        difficulty_groups = {'easy': [], 'medium': [], 'hard': [], 'distractor': []}

        for query in queries:
            query_id = query['id']
            query_text = query['text']
            expected_doc_id = query['expected_doc_id']
            difficulty = query.get('difficulty', 'unknown')

            # 编码查询
            query_embedding = self.encode([query_text])[0]

            # 计算与所有文档的相似度
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                sim = self.cosine_similarity(query_embedding, doc_embedding)
                similarities.append({
                    'doc_id': documents[i]['id'],
                    'similarity': float(sim)
                })

            # 按相似度降序排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # 找到正确文档的排名
            rank = -1
            for i, sim_result in enumerate(similarities, start=1):
                if sim_result['doc_id'] == expected_doc_id:
                    rank = i
                    break

            ranks.append(rank)

            # 记录详细结果
            detailed_result = {
                'query_id': query_id,
                'query': query_text,
                'expected_doc_id': expected_doc_id,
                'rank': rank,
                'difficulty': difficulty,
                'top5_results': similarities[:5]
            }
            detailed_results.append(detailed_result)

            # 按难度分组
            if difficulty in difficulty_groups:
                difficulty_groups[difficulty].append(rank)

        # 3. 计算整体指标
        metrics = calculate_all_metrics(ranks, k_values=[1, 3, 5, 10])

        # 4. 计算按难度分组的指标
        difficulty_stats = {}
        for diff, diff_ranks in difficulty_groups.items():
            if diff_ranks:
                diff_metrics = calculate_all_metrics(diff_ranks, k_values=[1, 3, 5, 10])
                difficulty_stats[diff] = {
                    'count': len(diff_ranks),
                    'recall@5': diff_metrics['recall@5'],
                    'ndcg@5': diff_metrics['ndcg@5'],
                    'mrr': diff_metrics['mrr'],
                    'average_rank': diff_metrics['average_rank']
                }

        eval_time = time.time() - start_time

        logger.info(f"评估完成，耗时: {eval_time:.2f}秒")
        logger.info(f"Recall@5: {metrics['recall@5']:.4f}")

        return {
            'model_name': self.model_name,
            'metrics': metrics,
            'difficulty_stats': difficulty_stats,
            'detailed_results': detailed_results,
            'eval_time': eval_time
        }


class DashScopeEvaluator(EmbeddingEvaluator):
    """DashScope API Embedding评估器"""

    def __init__(self, api_key: str, model: str = "text-embedding-v2"):
        super().__init__(f"DashScope API ({model})")
        self.embeddings = DashScopeEmbeddings(
            model=model,
            dashscope_api_key=api_key
        )
        self.batch_size = 25  # API限制
        logger.info(f"初始化DashScope评估器: {model}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        使用DashScope API编码文本

        注意：需要批量处理，避免超过API限制
        """
        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self.embeddings.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)

            # API限流，稍微延迟
            if i + self.batch_size < len(texts):
                time.sleep(0.1)

        return np.array(all_embeddings)


class FinetunedEvaluator(EmbeddingEvaluator):
    """微调后的本地模型评估器"""

    def __init__(self, model_path: str = "learning/models/bge-large-zh-travel-finetuned"):
        super().__init__(f"Finetuned Local Model ({model_path.split('/')[-1]})")
        self.model = SentenceTransformer(model_path)
        self.batch_size = 128  # 本地无限制，可以大批量
        logger.info(f"初始化微调模型评估器: {model_path}")
        logger.info(f"模型向量维度: {self.model.get_sentence_embedding_dimension()}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """使用本地微调模型编码文本"""
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 简单测试数据
    test_queries = [
        {
            'id': 'Q01',
            'text': '北京出差住宿标准是多少',
            'expected_doc_id': 'D01',
            'difficulty': 'easy'
        }
    ]

    test_documents = [
        {
            'id': 'D01',
            'text': '北京市、上海市、广州市、深圳市等一线城市住宿标准为500元/晚'
        },
        {
            'id': 'D02',
            'text': '杭州市、成都市、武汉市、西安市等二线城市住宿标准为400元/晚'
        }
    ]

    print("=" * 60)
    print("测试微调模型评估器")
    print("=" * 60)

    evaluator = FinetunedEvaluator()
    result = evaluator.evaluate(test_queries, test_documents)

    print(f"\n模型: {result['model_name']}")
    print(f"Recall@5: {result['metrics']['recall@5']:.4f}")
    print(f"评估耗时: {result['eval_time']:.2f}秒")
    print(f"查询 '{test_queries[0]['text']}' 的正确文档排名: {result['detailed_results'][0]['rank']}")
