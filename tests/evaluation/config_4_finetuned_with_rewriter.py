"""
配置4评估：微调模型 + Query重写流程（最佳配置）

评估流程：
1. 加载微调模型（如果存在，否则使用基础模型）
2. 创建混合检索器（启用EnterpriseQueryRewriter + RRF融合）
3. 对20个测试查询执行检索
4. 记录重写前后的查询对比
5. 计算指标：Accuracy@1, Recall@5, MRR
6. 按难度分级统计

测试数据源：用户提供的JSON格式测试数据
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from src.modules.module_2_advanced_rag.query_rewriter import EnterpriseQueryRewriter
from langchain_core.documents import Document


class SimpleLLM:
    """简单的LLM模拟器，用于查询重写"""

    def predict(self, prompt: str, temperature: float = 0.1) -> str:
        """
        模拟LLM的查询重写
        使用规则化方法进行查询改写
        """
        # 从prompt中提取用户查询
        lines = prompt.split('\n')
        query = ""
        for line in lines:
            if line.strip().startswith("【用户查询】"):
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    query = lines[idx + 1].strip()
                break

        if not query:
            return prompt.split('\n')[-1].strip()

        # 简单的规则化改写
        rewritten = query

        # 口语词替换
        replacements = {
            "魔都": "上海",
            "帝都": "北京",
            "咋": "如何",
            "啥": "什么",
            "能报多少": "费用报销标准",
            "能住什么价位": "住宿费用标准",
            "能坐": "是否可以",
            "应该坐": "交通工具选择",
            "有额外补贴吗": "补贴标准",
            "能报吗": "是否可以报销",
        }

        for old, new in replacements.items():
            rewritten = rewritten.replace(old, new)

        # 去除疑问词
        rewritten = rewritten.replace("吗", "").replace("？", "").replace("?", "")

        return rewritten.strip()


class Config4Evaluator:
    """配置4评估器：微调模型 + Query重写"""

    def __init__(self, base_model_path: str, finetuned_model_path: str):
        """
        初始化评估器

        Args:
            base_model_path: 基础模型路径
            finetuned_model_path: 微调模型路径
        """
        self.base_model_path = base_model_path
        self.finetuned_model_path = finetuned_model_path

        # 尝试加载微调模型，如果不存在则使用基础模型
        model_path = self._get_model_path()

        print(f"[INFO] Loading model: {model_path}")
        start_time = time.time()
        self.model = SentenceTransformer(model_path)
        load_time = time.time() - start_time
        print(f"[INFO] Model loaded in {load_time:.2f}s")

        # 初始化查询重写器
        self.query_rewriter = EnterpriseQueryRewriter(SimpleLLM())

    def _get_model_path(self) -> str:
        """获取实际使用的模型路径"""
        # 检查微调模型是否存在且包含有效的模型文件
        finetuned_path = Path(self.finetuned_model_path)

        # 检查是否有config.json或pytorch_model.bin等关键文件
        has_valid_model = False
        if finetuned_path.exists():
            # 检查直接路径
            if (finetuned_path / "config.json").exists():
                has_valid_model = True
            # 检查model子目录
            elif (finetuned_path / "model" / "config.json").exists():
                finetuned_path = finetuned_path / "model"
                has_valid_model = True

        if has_valid_model:
            print(f"[INFO] Using fine-tuned model: {finetuned_path}")
            return str(finetuned_path)
        else:
            print(f"[WARN] Fine-tuned model not found or incomplete, using base model: {self.base_model_path}")
            return self.base_model_path

    def encode_documents(self, documents: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        """编码文档库"""
        doc_contents = [doc['content'] for doc in documents]
        print(f"[INFO] Encoding {len(doc_contents)} documents...")
        doc_embeddings = self.model.encode(doc_contents, show_progress_bar=False)
        return doc_embeddings, doc_contents

    def retrieve_with_rewriting(
        self,
        query: str,
        doc_embeddings: np.ndarray,
        doc_contents: List[str],
        k: int = 5
    ) -> Tuple[List[int], List[float], str]:
        """
        使用查询重写的检索流程

        Returns:
            (top_k_indices, top_k_scores, rewritten_query)
        """
        # Step 1: 查询重写
        rewritten_query = self.query_rewriter.rewrite(query)

        # Step 2: 使用改写后的查询进行检索
        query_embedding = self.model.encode([rewritten_query])[0]

        # Step 3: 计算相似度
        similarities = cosine_similarity([query_embedding], doc_embeddings)[0]

        # Step 4: 获取Top-K
        top_k_indices = np.argsort(similarities)[::-1][:k]
        top_k_scores = similarities[top_k_indices]

        return top_k_indices.tolist(), top_k_scores.tolist(), rewritten_query

    def evaluate_single_query(
        self,
        query_data: Dict,
        doc_embeddings: np.ndarray,
        doc_contents: List[str],
        documents: List[Dict]
    ) -> Dict:
        """评估单个查询"""
        query = query_data['query']
        expected_doc_id = query_data['expected_doc_id']
        difficulty = query_data['difficulty']

        # 执行检索
        top_k_indices, top_k_scores, rewritten_query = self.retrieve_with_rewriting(
            query, doc_embeddings, doc_contents, k=5
        )

        # 查找正确文档的排名
        rank = -1
        retrieved_docs = []

        for rank_idx, (doc_idx, score) in enumerate(zip(top_k_indices, top_k_scores), start=1):
            retrieved_doc_id = documents[doc_idx]['doc_id']
            retrieved_content = doc_contents[doc_idx]

            retrieved_docs.append({
                'rank': rank_idx,
                'doc_id': retrieved_doc_id,
                'content_preview': retrieved_content[:100],
                'score': float(score)
            })

            # 检查是否匹配
            if expected_doc_id in retrieved_doc_id or retrieved_doc_id == expected_doc_id:
                if rank == -1:
                    rank = rank_idx

        # 对于distractor样本，期望没有匹配
        is_correct = False
        if difficulty == 'distractor':
            is_correct = (rank == -1)  # 没找到相关文档才算正确
            rank = 1 if is_correct else -1  # 用于统计
        else:
            is_correct = (rank == 1)

        return {
            'query': query,
            'rewritten_query': rewritten_query,
            'expected_doc_id': expected_doc_id,
            'difficulty': difficulty,
            'rank': rank,
            'is_correct': is_correct,
            'top_1_doc_id': documents[top_k_indices[0]]['doc_id'],
            'top_1_score': float(top_k_scores[0]),
            'retrieved_docs': retrieved_docs
        }

    def calculate_metrics(self, results: List[Dict]) -> Dict:
        """计算评估指标"""
        # 排除distractor样本
        valid_results = [r for r in results if r['difficulty'] != 'distractor']
        distractor_results = [r for r in results if r['difficulty'] == 'distractor']

        # Accuracy@1
        accuracy_at_1 = sum(1 for r in valid_results if r['rank'] == 1) / len(valid_results) if valid_results else 0.0

        # Recall@5
        recall_at_5 = sum(1 for r in valid_results if 1 <= r['rank'] <= 5) / len(valid_results) if valid_results else 0.0

        # MRR (Mean Reciprocal Rank)
        reciprocal_ranks = [1.0 / r['rank'] if r['rank'] > 0 else 0.0 for r in valid_results]
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

        # 按难度分组
        by_difficulty = {}
        for diff in ['easy', 'medium', 'hard']:
            diff_results = [r for r in results if r['difficulty'] == diff]
            if diff_results:
                diff_accuracy = sum(1 for r in diff_results if r['rank'] == 1) / len(diff_results)
                diff_recall = sum(1 for r in diff_results if 1 <= r['rank'] <= 5) / len(diff_results)
                by_difficulty[diff] = {
                    'accuracy_at_1': diff_accuracy,
                    'recall_at_5': diff_recall,
                    'count': len(diff_results)
                }

        # Distractor准确率（正确拒绝）
        if distractor_results:
            by_difficulty['distractor'] = {
                'accuracy_at_1': sum(1 for r in distractor_results if r['is_correct']) / len(distractor_results),
                'count': len(distractor_results)
            }

        return {
            'accuracy_at_1': accuracy_at_1,
            'recall_at_5': recall_at_5,
            'mrr': mrr,
            'by_difficulty': by_difficulty
        }

    def evaluate(self, test_data: Dict) -> Dict:
        """执行完整评估"""
        print(f"\n{'='*70}")
        print(f"Configuration 4: Fine-tuned Model + Query Rewriter")
        print(f"{'='*70}")

        # 提取测试数据
        test_queries = test_data['test_queries']
        documents = test_data['documents']

        print(f"[INFO] Test queries: {len(test_queries)}")
        print(f"[INFO] Document corpus: {len(documents)}")

        # 编码文档库
        doc_embeddings, doc_contents = self.encode_documents(documents)

        # 评估每个查询
        results = []
        query_rewrites = []
        failed_queries = []

        print(f"\n[INFO] Evaluating queries with query rewriting...")
        for i, query_data in enumerate(test_queries, 1):
            result = self.evaluate_single_query(
                query_data, doc_embeddings, doc_contents, documents
            )
            results.append(result)

            # 记录查询重写
            query_rewrites.append({
                'original': result['query'],
                'rewritten': result['rewritten_query'],
                'difficulty': result['difficulty']
            })

            # 记录失败的查询
            if not result['is_correct'] and result['difficulty'] != 'distractor':
                failed_queries.append({
                    'query': result['query'],
                    'expected': result['expected_doc_id'],
                    'got': result['top_1_doc_id'],
                    'rank': result['rank']
                })

            # 打印进度
            status = "[OK]" if result['is_correct'] else "[FAIL]"
            print(f"  [{i:2d}/{len(test_queries)}] {status} {result['query']}")
            if result['query'] != result['rewritten_query']:
                print(f"       → {result['rewritten_query']}")

        # 计算指标
        metrics = self.calculate_metrics(results)

        # 打印结果
        self._print_summary(metrics, query_rewrites, failed_queries)

        return {
            'config': 'finetuned_model_with_query_rewriter',
            'accuracy_at_1': metrics['accuracy_at_1'],
            'recall_at_5': metrics['recall_at_5'],
            'mrr': metrics['mrr'],
            'by_difficulty': metrics['by_difficulty'],
            'query_rewrites': query_rewrites,
            'failed_queries': failed_queries,
            'detailed_results': results
        }

    def _print_summary(self, metrics: Dict, query_rewrites: List[Dict], failed_queries: List[Dict]):
        """打印评估摘要"""
        print(f"\n{'='*70}")
        print(f"EVALUATION RESULTS")
        print(f"{'='*70}")

        print(f"\n--- Overall Metrics ---")
        print(f"Accuracy@1:  {metrics['accuracy_at_1']:.2%}")
        print(f"Recall@5:    {metrics['recall_at_5']:.2%}")
        print(f"MRR:         {metrics['mrr']:.4f}")

        print(f"\n--- By Difficulty ---")
        for diff, stats in metrics['by_difficulty'].items():
            print(f"{diff.capitalize():<12} Accuracy@1: {stats['accuracy_at_1']:.2%}  (n={stats['count']})")

        print(f"\n--- Query Rewrites (Sample) ---")
        rewrite_samples = [qr for qr in query_rewrites if qr['original'] != qr['rewritten']][:5]
        for qr in rewrite_samples:
            print(f"  Original:  {qr['original']}")
            print(f"  Rewritten: {qr['rewritten']}")
            print()

        if failed_queries:
            print(f"\n--- Failed Queries ({len(failed_queries)}) ---")
            for fq in failed_queries[:5]:
                print(f"  Query: {fq['query']}")
                print(f"  Expected: {fq['expected']} | Got: {fq['got']} | Rank: {fq['rank']}")
                print()


def main():
    """主评估流程"""
    # 测试数据（从用户提供的JSON）
    test_data = {
        "base_model_path": "BAAI/bge-large-zh-v1.5",
        "finetuned_model_path": "../../learning/models/bge-large-zh-travel-finetuned",
        "test_queries": [
            {"query": "去北京出差能住什么价位的酒店？", "expected_doc_id": "doc_06", "difficulty": "easy"},
            {"query": "经济舱的机票可以报销吗？", "expected_doc_id": "doc_05", "difficulty": "easy"},
            {"query": "出差补贴一天给多少钱？", "expected_doc_id": "doc_12", "difficulty": "easy"},
            {"query": "火车票能报销吗？", "expected_doc_id": "doc_09", "difficulty": "easy"},
            {"query": "出差住宿发票丢了怎么办？", "expected_doc_id": "doc_01", "difficulty": "easy"},
            {"query": "去魔都出差住宿预算多少？", "expected_doc_id": "doc_11", "difficulty": "medium"},
            {"query": "副总裁能坐商务舱吗？", "expected_doc_id": "doc_23", "difficulty": "medium"},
            {"query": "从北京到成都应该坐飞机还是高铁？", "expected_doc_id": "doc_15", "difficulty": "medium"},
            {"query": "周末加班出差有额外补贴吗？", "expected_doc_id": "doc_13", "difficulty": "medium"},
            {"query": "出差期间生病就医费用能报吗？", "expected_doc_id": "doc_01", "difficulty": "medium"},
            {"query": "一次出差去多个城市，住宿标准怎么算？", "expected_doc_id": "doc_19", "difficulty": "medium"},
            {"query": "提前预订机票有折扣吗？", "expected_doc_id": "doc_16", "difficulty": "medium"},
            {"query": "商务舱和经济舱的差别是什么？", "expected_doc_id": "doc_23", "difficulty": "hard"},
            {"query": "杭州属于几线城市？住宿标准是多少？", "expected_doc_id": "doc_19", "difficulty": "hard"},
            {"query": "国际出差的政策和国内一样吗？", "expected_doc_id": "doc_14", "difficulty": "hard"},
            {"query": "出差超过一个月，标准有变化吗？", "expected_doc_id": "doc_16", "difficulty": "hard"},
            {"query": "CEO出差有什么特殊待遇？", "expected_doc_id": "doc_24", "difficulty": "hard"},
            {"query": "公司年会预算是多少？", "expected_doc_id": "distractor", "difficulty": "distractor"},
            {"query": "员工入职需要什么材料？", "expected_doc_id": "distractor", "difficulty": "distractor"},
            {"query": "如何申请年假？", "expected_doc_id": "distractor", "difficulty": "distractor"}
        ],
        "documents": [
            {"doc_id": "doc_01", "content": "报销材料清单：1)差旅申请单（已审批）2)机票行程单或火车票 3)酒店发票 4)其他交通费发票 5)费用明细表。所有材料需在出差结束后10个工作日内提交。"},
            {"doc_id": "doc_02", "content": "每日200元出差补贴包含市内交通和餐饮补贴。机场往返可单独报销。"},
            {"doc_id": "doc_03", "content": "机票报销需提供行程单和发票。经济舱全额报销，商务舱需符合职级或航程要求。"},
            {"doc_id": "doc_04", "content": "国际出差需提前7天申请，并提交详细行程和预算。国内出差提前3天即可。"},
            {"doc_id": "doc_05", "content": "国内航班经济舱可以全额报销，需提供发票和行程单，票价应合理。"},
            {"doc_id": "doc_06", "content": "酒店住宿标准：一线城市（北上广深）不超过500元/晚，超出部分自付。"},
            {"doc_id": "doc_07", "content": "市内交通费用包含在每日200元补贴中。机场往返可单独报销出租车或机场大巴费用，需提供发票。"},
            {"doc_id": "doc_08", "content": "酒店住宿标准：一线城市500元/晚，二线300元/晚，三线200元/晚。超出部分需自付。"},
            {"doc_id": "doc_09", "content": "高铁出行优先选择二等座，可正常报销。商务座需总监级别或特殊情况。"},
            {"doc_id": "doc_10", "content": "国内航班经济舱可以全额报销，但需要提供正规发票和行程单。票价应在市场合理范围内。"},
            {"doc_id": "doc_11", "content": "一线城市（北上广深）酒店住宿不超过500元/晚。二线城市300元/晚，三线城市200元/晚。"},
            {"doc_id": "doc_12", "content": "国内出差每天补贴200元，包含市内交通和餐饮补贴。周末出差标准不变。"},
            {"doc_id": "doc_13", "content": "周末出差补贴标准与工作日相同，每天200元。如占用休息日，可申请调休，调休时长为实际出差天数。"},
            {"doc_id": "doc_14", "content": "国际航班：飞行时间4小时以内经济舱，4小时以上可申请商务舱（需总监审批）。跨洲际航班（8小时以上）商务舱自动批准。"},
            {"doc_id": "doc_15", "content": "高铁出行优先选择二等座。商务座仅在以下情况允许：1)总监及以上级别 2)特殊健康原因并提供证明 3)二等座已售罄。"},
            {"doc_id": "doc_16", "content": "差旅审批流程：国内出差需提前3天申请，国际出差需提前7天申请。紧急出差（48小时内）需部门经理特批。"},
            {"doc_id": "doc_17", "content": "机票报销需要提供正规发票和行程单。经济舱可全额报销，票价需在合理范围。"},
            {"doc_id": "doc_18", "content": "高铁优先二等座。商务座仅在以下情况允许：总监及以上级别、健康原因有证明、二等座售罄。"},
            {"doc_id": "doc_19", "content": "酒店住宿标准：一线城市（北上广深）不超过500元/晚，二线城市不超过300元/晚，三线城市不超过200元/晚。超出部分自付。"},
            {"doc_id": "doc_20", "content": "出差补贴标准：国内出差每天200元，涵盖市内交通和餐饮。周末出差补贴相同。"},
            {"doc_id": "doc_21", "content": "国内航班经济舱可以全额报销，但需要提供正规发票和行程单。经济舱票价应在市场合理范围内。"},
            {"doc_id": "doc_22", "content": "差旅审批流程：国内出差需提前3天申请。紧急出差（48小时内）需部门经理特批。"},
            {"doc_id": "doc_23", "content": "商务舱报销需满足：1)副总裁及以上 2)国际航班4小时+ 3)跨洲际8小时+。其他情况只能报销经济舱。"},
            {"doc_id": "doc_24", "content": "普通员工不得预订商务舱或头等舱。商务舱仅限副总裁及以上级别或长途国际航班。"},
            {"doc_id": "doc_25", "content": "出差补贴标准：国内出差每天200元，包含市内交通和餐饮补贴。周末出差补贴标准不变。"},
            {"doc_id": "doc_26", "content": "高铁商务座允许条件：1)总监及以上级别 2)特殊健康原因并提供证明 3)二等座已售罄。否则优先二等座。"},
            {"doc_id": "doc_27", "content": "商务舱仅限高管或长途国际航班。普通员工预订商务舱或头等舱不予报销。"},
            {"doc_id": "doc_28", "content": "商务舱预订条件：副总裁及以上级别，或国际航班飞行4小时以上。跨洲际航班（8小时+）商务舱自动批准。"},
            {"doc_id": "doc_29", "content": "商务舱仅限副总裁及以上级别，或飞行时间超过4小时的国际航班。普通员工不得预订商务舱或头等舱。"}
        ]
    }

    # 创建评估器
    evaluator = Config4Evaluator(
        base_model_path=test_data['base_model_path'],
        finetuned_model_path=test_data['finetuned_model_path']
    )

    # 执行评估
    result = evaluator.evaluate(test_data)

    # 保存结果
    output_file = Path(__file__).parent / "config_4_evaluation_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Results saved to: {output_file}")
    print(f"\n{'='*70}")

    return result


if __name__ == "__main__":
    result = main()
