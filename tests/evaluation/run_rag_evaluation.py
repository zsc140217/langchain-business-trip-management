"""
RAG系统综合评估脚本

功能：
1. 使用ComprehensiveEvaluator执行评估
2. 集成通义千问作为LLM Judge
3. 从JSON加载测试用例
4. 生成Markdown格式评估报告
5. 标记需要人工review的case
6. 对比微调模型 vs 云端API
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.comprehensive_evaluator import (
    ComprehensiveEvaluator,
    EvaluationResult,
    RetrievalMetrics,
    GenerationMetrics,
    SystemMetrics
)
from src.evaluation.llm_judge import QwenJudge, JudgeConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    query: str
    ground_truth_answer: Optional[str] = None
    ground_truth_docs: Optional[List[str]] = None
    expected_intent: Optional[str] = None
    category: str = "general"
    tags: List[str] = None
    needs_human_review: bool = False
    notes: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    type: str  # "finetuned" or "api"
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    description: str = ""


class RAGEvaluationRunner:
    """RAG评估运行器"""

    def __init__(
        self,
        test_cases_file: str,
        output_dir: str = "tests/evaluation/reports",
        judge_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化评估运行器

        Args:
            test_cases_file: 测试用例JSON文件路径
            output_dir: 输出报告目录
            judge_config: LLM Judge配置
        """
        self.test_cases_file = test_cases_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载测试用例
        self.test_cases = self._load_test_cases()
        logger.info(f"已加载 {len(self.test_cases)} 个测试用例")

        # 初始化LLM Judge
        if judge_config is None:
            judge_config = {
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "model_name": "qwen-plus",
                "temperature": 0.1,
                "max_tokens": 2000
            }

        self.judge = QwenJudge(JudgeConfig(**judge_config))
        logger.info("LLM Judge初始化完成")

        # 初始化评估器
        self.evaluator = ComprehensiveEvaluator(llm_judge=self.judge)

    def _load_test_cases(self) -> List[TestCase]:
        """加载测试用例"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            test_cases = []
            for item in data.get("test_cases", []):
                test_cases.append(TestCase(**item))

            return test_cases

        except Exception as e:
            logger.error(f"加载测试用例失败: {e}")
            raise

    def run_evaluation(
        self,
        model_configs: List[ModelConfig],
        rag_system_factory,
        save_report: bool = True
    ) -> Dict[str, List[EvaluationResult]]:
        """
        运行评估

        Args:
            model_configs: 模型配置列表
            rag_system_factory: RAG系统工厂函数，接收ModelConfig返回RAG系统实例
            save_report: 是否保存报告

        Returns:
            各模型的评估结果
        """
        all_results = {}

        for model_config in model_configs:
            logger.info(f"\n{'='*60}")
            logger.info(f"开始评估模型: {model_config.name} ({model_config.type})")
            logger.info(f"{'='*60}\n")

            # 创建RAG系统实例
            rag_system = rag_system_factory(model_config)

            # 运行测试用例
            results = []
            for i, test_case in enumerate(self.test_cases, 1):
                logger.info(f"[{i}/{len(self.test_cases)}] 执行测试: {test_case.id}")

                try:
                    # 调用RAG系统
                    response = rag_system.query(test_case.query)

                    # 评估
                    result = self.evaluator.evaluate(
                        query=test_case.query,
                        retrieved_docs=response.get("retrieved_docs", []),
                        generated_answer=response.get("answer", ""),
                        ground_truth_answer=test_case.ground_truth_answer,
                        ground_truth_docs=test_case.ground_truth_docs,
                        metadata={
                            "test_case_id": test_case.id,
                            "category": test_case.category,
                            "tags": test_case.tags,
                            "needs_human_review": test_case.needs_human_review,
                            "model_name": model_config.name,
                            "model_type": model_config.type
                        }
                    )

                    results.append(result)

                    # 实时显示关键指标
                    self._print_result_summary(result)

                except Exception as e:
                    logger.error(f"测试用例 {test_case.id} 执行失败: {e}")
                    continue

            all_results[model_config.name] = results

            # 生成单个模型的报告
            if save_report:
                self._save_model_report(model_config, results)

        # 生成对比报告
        if save_report and len(model_configs) > 1:
            self._save_comparison_report(model_configs, all_results)

        return all_results

    def _print_result_summary(self, result: EvaluationResult):
        """打印结果摘要"""
        print(f"  检索质量: {result.retrieval.quality_score:.3f}")
        print(f"  生成质量: {result.generation.overall_score:.3f}")
        print(f"  系统延迟: {result.system.latency_ms:.0f}ms")

        if result.generation.needs_human_review:
            print(f"  [!] 需要人工review: {result.generation.review_reason}")
        print()

    def _save_model_report(
        self,
        model_config: ModelConfig,
        results: List[EvaluationResult]
    ):
        """保存单个模型的评估报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"{model_config.name}_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_model_report(model_config, results))

        logger.info(f"报告已保存: {report_file}")

    def _generate_model_report(
        self,
        model_config: ModelConfig,
        results: List[EvaluationResult]
    ) -> str:
        """生成单个模型的Markdown报告"""
        # 计算统计数据
        stats = self._calculate_statistics(results)

        # 标记需要review的case
        review_cases = [r for r in results if r.generation.needs_human_review]

        # 生成报告
        report = f"""# RAG系统评估报告

## 模型信息

- **模型名称**: {model_config.name}
- **模型类型**: {model_config.type}
- **描述**: {model_config.description}
- **评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **测试用例数**: {len(results)}

---

## 整体指标

### 检索指标

| 指标 | 平均值 | 标准差 | 最小值 | 最大值 |
|------|--------|--------|--------|--------|
| 质量分数 | {stats['retrieval']['quality_score']['mean']:.3f} | {stats['retrieval']['quality_score']['std']:.3f} | {stats['retrieval']['quality_score']['min']:.3f} | {stats['retrieval']['quality_score']['max']:.3f} |
| 召回率 | {stats['retrieval']['recall']['mean']:.3f} | {stats['retrieval']['recall']['std']:.3f} | {stats['retrieval']['recall']['min']:.3f} | {stats['retrieval']['recall']['max']:.3f} |
| 准确率 | {stats['retrieval']['precision']['mean']:.3f} | {stats['retrieval']['precision']['std']:.3f} | {stats['retrieval']['precision']['min']:.3f} | {stats['retrieval']['precision']['max']:.3f} |
| MRR | {stats['retrieval']['mrr']['mean']:.3f} | {stats['retrieval']['mrr']['std']:.3f} | {stats['retrieval']['mrr']['min']:.3f} | {stats['retrieval']['mrr']['max']:.3f} |

### 生成指标

| 指标 | 平均值 | 标准差 | 最小值 | 最大值 |
|------|--------|--------|--------|--------|
| 整体分数 | {stats['generation']['overall_score']['mean']:.3f} | {stats['generation']['overall_score']['std']:.3f} | {stats['generation']['overall_score']['min']:.3f} | {stats['generation']['overall_score']['max']:.3f} |
| 忠实度 | {stats['generation']['faithfulness']['mean']:.3f} | {stats['generation']['faithfulness']['std']:.3f} | {stats['generation']['faithfulness']['min']:.3f} | {stats['generation']['faithfulness']['max']:.3f} |
| 相关性 | {stats['generation']['relevance']['mean']:.3f} | {stats['generation']['relevance']['std']:.3f} | {stats['generation']['relevance']['min']:.3f} | {stats['generation']['relevance']['max']:.3f} |
| 完整性 | {stats['generation']['completeness']['mean']:.3f} | {stats['generation']['completeness']['std']:.3f} | {stats['generation']['completeness']['min']:.3f} | {stats['generation']['completeness']['max']:.3f} |

### 系统指标

| 指标 | 平均值 | 标准差 | 最小值 | 最大值 |
|------|--------|--------|--------|--------|
| 延迟 (ms) | {stats['system']['latency_ms']['mean']:.0f} | {stats['system']['latency_ms']['std']:.0f} | {stats['system']['latency_ms']['min']:.0f} | {stats['system']['latency_ms']['max']:.0f} |
| Token数 | {stats['system']['token_count']['mean']:.0f} | {stats['system']['token_count']['std']:.0f} | {stats['system']['token_count']['min']:.0f} | {stats['system']['token_count']['max']:.0f} |

---

## 需要人工Review的Case ({len(review_cases)})

"""

        if review_cases:
            for i, result in enumerate(review_cases, 1):
                report += f"""
### Case {i}: {result.metadata.get('test_case_id', 'Unknown')}

- **原因**: {result.generation.review_reason}
- **查询**: {result.query}
- **生成回答**: {result.generated_answer[:200]}...
- **评分**: 整体 {result.generation.overall_score:.3f} | 忠实度 {result.generation.faithfulness:.3f} | 相关性 {result.generation.relevance:.3f}

"""
        else:
            report += "\n无需人工review的case。\n"

        report += """
---

## 按类别统计

"""
        # 按类别分组
        by_category = {}
        for result in results:
            category = result.metadata.get('category', 'unknown')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)

        for category, cat_results in by_category.items():
            cat_stats = self._calculate_statistics(cat_results)
            report += f"""
### {category} ({len(cat_results)} cases)

| 指标类型 | 质量分数 | 忠实度 | 相关性 | 完整性 |
|----------|----------|--------|--------|--------|
| 平均值 | {cat_stats['retrieval']['quality_score']['mean']:.3f} | {cat_stats['generation']['faithfulness']['mean']:.3f} | {cat_stats['generation']['relevance']['mean']:.3f} | {cat_stats['generation']['completeness']['mean']:.3f} |

"""

        report += """
---

## 详细结果

"""

        for i, result in enumerate(results, 1):
            report += f"""
### Test {i}: {result.metadata.get('test_case_id', f'case_{i}')}

**查询**: {result.query}

**检索结果**:
- 质量分数: {result.retrieval.quality_score:.3f}
- 召回率: {result.retrieval.recall:.3f}
- 准确率: {result.retrieval.precision:.3f}
- 检索到文档数: {result.retrieval.docs_retrieved}

**生成结果**:
- 整体分数: {result.generation.overall_score:.3f}
- 忠实度: {result.generation.faithfulness:.3f}
- 相关性: {result.generation.relevance:.3f}
- 完整性: {result.generation.completeness:.3f}
- 需要review: {'是' if result.generation.needs_human_review else '否'}

**生成回答**:
```
{result.generated_answer}
```

**系统指标**:
- 延迟: {result.system.latency_ms:.0f}ms
- Token数: {result.system.token_count}

---

"""

        return report

    def _save_comparison_report(
        self,
        model_configs: List[ModelConfig],
        all_results: Dict[str, List[EvaluationResult]]
    ):
        """保存模型对比报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"comparison_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_comparison_report(model_configs, all_results))

        logger.info(f"对比报告已保存: {report_file}")

    def _generate_comparison_report(
        self,
        model_configs: List[ModelConfig],
        all_results: Dict[str, List[EvaluationResult]]
    ) -> str:
        """生成模型对比Markdown报告"""
        report = f"""# RAG系统模型对比报告

**评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 参与对比的模型

"""

        for config in model_configs:
            report += f"- **{config.name}** ({config.type}): {config.description}\n"

        report += "\n---\n\n## 整体指标对比\n\n### 检索质量\n\n"

        # 检索指标对比表
        report += "| 模型 | 质量分数 | 召回率 | 准确率 | MRR |\n"
        report += "|------|----------|--------|--------|-----|\n"

        for config in model_configs:
            results = all_results[config.name]
            stats = self._calculate_statistics(results)
            report += f"| {config.name} | "
            report += f"{stats['retrieval']['quality_score']['mean']:.3f} | "
            report += f"{stats['retrieval']['recall']['mean']:.3f} | "
            report += f"{stats['retrieval']['precision']['mean']:.3f} | "
            report += f"{stats['retrieval']['mrr']['mean']:.3f} |\n"

        report += "\n### 生成质量\n\n"
        report += "| 模型 | 整体分数 | 忠实度 | 相关性 | 完整性 |\n"
        report += "|------|----------|--------|--------|--------|\n"

        for config in model_configs:
            results = all_results[config.name]
            stats = self._calculate_statistics(results)
            report += f"| {config.name} | "
            report += f"{stats['generation']['overall_score']['mean']:.3f} | "
            report += f"{stats['generation']['faithfulness']['mean']:.3f} | "
            report += f"{stats['generation']['relevance']['mean']:.3f} | "
            report += f"{stats['generation']['completeness']['mean']:.3f} |\n"

        report += "\n### 系统性能\n\n"
        report += "| 模型 | 平均延迟(ms) | 平均Token数 | 需Review数 |\n"
        report += "|------|--------------|-------------|------------|\n"

        for config in model_configs:
            results = all_results[config.name]
            stats = self._calculate_statistics(results)
            review_count = len([r for r in results if r.generation.needs_human_review])
            report += f"| {config.name} | "
            report += f"{stats['system']['latency_ms']['mean']:.0f} | "
            report += f"{stats['system']['token_count']['mean']:.0f} | "
            report += f"{review_count} |\n"

        # 按类别对比
        report += "\n---\n\n## 按类别对比\n\n"

        # 获取所有类别
        all_categories = set()
        for results in all_results.values():
            for result in results:
                all_categories.add(result.metadata.get('category', 'unknown'))

        for category in sorted(all_categories):
            report += f"### {category}\n\n"
            report += "| 模型 | 检索质量 | 生成质量 | 忠实度 | 相关性 |\n"
            report += "|------|----------|----------|--------|--------|\n"

            for config in model_configs:
                results = all_results[config.name]
                cat_results = [r for r in results if r.metadata.get('category') == category]

                if cat_results:
                    cat_stats = self._calculate_statistics(cat_results)
                    report += f"| {config.name} | "
                    report += f"{cat_stats['retrieval']['quality_score']['mean']:.3f} | "
                    report += f"{cat_stats['generation']['overall_score']['mean']:.3f} | "
                    report += f"{cat_stats['generation']['faithfulness']['mean']:.3f} | "
                    report += f"{cat_stats['generation']['relevance']['mean']:.3f} |\n"
                else:
                    report += f"| {config.name} | N/A | N/A | N/A | N/A |\n"

            report += "\n"

        # 推荐结论
        report += "\n---\n\n## 推荐结论\n\n"

        # 找出各指标最优模型
        best_retrieval = max(
            model_configs,
            key=lambda c: self._calculate_statistics(all_results[c.name])['retrieval']['quality_score']['mean']
        )

        best_generation = max(
            model_configs,
            key=lambda c: self._calculate_statistics(all_results[c.name])['generation']['overall_score']['mean']
        )

        best_latency = min(
            model_configs,
            key=lambda c: self._calculate_statistics(all_results[c.name])['system']['latency_ms']['mean']
        )

        report += f"- **检索质量最优**: {best_retrieval.name}\n"
        report += f"- **生成质量最优**: {best_generation.name}\n"
        report += f"- **响应速度最快**: {best_latency.name}\n"

        return report

    def _calculate_statistics(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """计算统计数据"""
        import numpy as np

        def calc_stats(values: List[float]) -> Dict[str, float]:
            return {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values)
            }

        return {
            'retrieval': {
                'quality_score': calc_stats([r.retrieval.quality_score for r in results]),
                'recall': calc_stats([r.retrieval.recall for r in results]),
                'precision': calc_stats([r.retrieval.precision for r in results]),
                'mrr': calc_stats([r.retrieval.mrr for r in results])
            },
            'generation': {
                'overall_score': calc_stats([r.generation.overall_score for r in results]),
                'faithfulness': calc_stats([r.generation.faithfulness for r in results]),
                'relevance': calc_stats([r.generation.relevance for r in results]),
                'completeness': calc_stats([r.generation.completeness for r in results])
            },
            'system': {
                'latency_ms': calc_stats([r.system.latency_ms for r in results]),
                'token_count': calc_stats([r.system.token_count for r in results])
            }
        }


def create_test_cases_template(output_file: str = "tests/evaluation/test_cases.json"):
    """创建测试用例模板"""
    template = {
        "version": "1.0",
        "description": "RAG系统评估测试用例",
        "test_cases": [
            {
                "id": "intent_detect_001",
                "query": "我要报销一笔差旅费用",
                "ground_truth_answer": None,
                "ground_truth_docs": None,
                "expected_intent": "reimbursement_submission",
                "category": "intent_detection",
                "tags": ["基础功能", "意图识别"],
                "needs_human_review": False,
                "notes": "测试基本意图识别"
            },
            {
                "id": "policy_query_001",
                "query": "出差交通费的报销标准是什么",
                "ground_truth_answer": "根据差旅报销制度，交通费报销标准为：火车票据实报销，飞机票经济舱据实报销，市内交通每天不超过100元。",
                "ground_truth_docs": ["policy_doc_001"],
                "expected_intent": "policy_query",
                "category": "policy_retrieval",
                "tags": ["政策查询", "交通费"],
                "needs_human_review": False,
                "notes": "测试政策检索准确性"
            },
            {
                "id": "complex_query_001",
                "query": "我上个月去北京出差3天，有火车票、酒店发票和餐费，应该怎么报销",
                "ground_truth_answer": None,
                "ground_truth_docs": ["policy_doc_001", "policy_doc_002"],
                "expected_intent": "reimbursement_guidance",
                "category": "complex_reasoning",
                "tags": ["复杂查询", "多步骤"],
                "needs_human_review": True,
                "notes": "测试复杂场景的推理能力，需要人工review生成质量"
            },
            {
                "id": "approval_status_001",
                "query": "查询我的报销单状态",
                "ground_truth_answer": None,
                "ground_truth_docs": None,
                "expected_intent": "status_query",
                "category": "status_query",
                "tags": ["状态查询"],
                "needs_human_review": False,
                "notes": "测试状态查询功能"
            }
        ]
    }

    # 确保目录存在
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # 保存模板
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    logger.info(f"测试用例模板已创建: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="RAG系统评估脚本")
    parser.add_argument(
        "--test-cases",
        default="tests/evaluation/test_cases.json",
        help="测试用例JSON文件路径"
    )
    parser.add_argument(
        "--output-dir",
        default="tests/evaluation/reports",
        help="输出报告目录"
    )
    parser.add_argument(
        "--create-template",
        action="store_true",
        help="创建测试用例模板"
    )

    args = parser.parse_args()

    # 如果需要创建模板
    if args.create_template:
        create_test_cases_template(args.test_cases)
        return

    # 示例：定义模型配置
    model_configs = [
        ModelConfig(
            name="finetuned_qwen",
            type="finetuned",
            model_path="/path/to/finetuned/model",
            description="微调后的千问模型"
        ),
        ModelConfig(
            name="qwen_api",
            type="api",
            endpoint="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            description="通义千问云端API"
        )
    ]

    # RAG系统工厂函数（需要根据实际项目实现）
    def rag_system_factory(model_config: ModelConfig):
        """
        创建RAG系统实例

        注意：这里需要根据实际项目的RAG系统实现来创建实例
        """
        from src.agents.intelligent_router import IntelligentRouter

        # 这里是示例代码，需要根据实际情况修改
        if model_config.type == "finetuned":
            # 加载微调模型
            pass
        else:
            # 使用API
            pass

        # 返回RAG系统实例（需要有query方法）
        class MockRAGSystem:
            def query(self, query: str) -> Dict[str, Any]:
                # 这里应该调用实际的RAG系统
                return {
                    "answer": "这是生成的回答",
                    "retrieved_docs": ["doc1", "doc2"]
                }

        return MockRAGSystem()

    # 初始化评估运行器
    runner = RAGEvaluationRunner(
        test_cases_file=args.test_cases,
        output_dir=args.output_dir
    )

    # 运行评估
    logger.info("开始运行评估...")
    results = runner.run_evaluation(
        model_configs=model_configs,
        rag_system_factory=rag_system_factory,
        save_report=True
    )

    logger.info("评估完成！")
    logger.info(f"报告保存在: {args.output_dir}")


if __name__ == "__main__":
    main()
