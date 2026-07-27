#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键运行所有评估模块

功能：
1. 按顺序运行4个评估模块（RAG、Routing、Approval、LoadTest）
2. 汇总结果生成总报告
3. 命令行参数支持选择性运行
4. 显示进度条和预估时间
5. 成本监控（预估 + 实际）

使用方法：
    # 运行所有评估
    python tests/evaluation/run_all_evaluations.py

    # 仅运行指定模块
    python tests/evaluation/run_all_evaluations.py --modules rag routing

    # 跳过负载测试
    python tests/evaluation/run_all_evaluations.py --skip load

    # 自定义输出目录
    python tests/evaluation/run_all_evaluations.py --output-dir custom_reports/

作者：Claude
创建时间：2026-07-25
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class CostEstimate:
    """成本预估"""
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    estimated_cost_cny: float = 0.0

    def add(self, other: 'CostEstimate') -> 'CostEstimate':
        """累加成本"""
        return CostEstimate(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
            estimated_cost_cny=self.estimated_cost_cny + other.estimated_cost_cny
        )


@dataclass
class ModuleConfig:
    """评估模块配置"""
    name: str
    display_name: str
    script_path: str
    enabled: bool = True
    estimated_duration_seconds: int = 60
    estimated_cost: CostEstimate = field(default_factory=CostEstimate)
    requires_llm: bool = True
    description: str = ""


@dataclass
class ModuleResult:
    """单个模块执行结果"""
    module_name: str
    success: bool
    duration_seconds: float
    start_time: datetime
    end_time: datetime
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    actual_cost: Optional[CostEstimate] = None
    error_message: str = ""


@dataclass
class EvaluationSummary:
    """整体评估汇总"""
    total_duration_seconds: float
    start_time: datetime
    end_time: datetime
    modules_run: int
    modules_success: int
    modules_failed: int
    total_estimated_cost: CostEstimate
    total_actual_cost: Optional[CostEstimate]
    module_results: List[ModuleResult] = field(default_factory=list)


# ============================================================================
# 模块配置
# ============================================================================

EVALUATION_MODULES = [
    ModuleConfig(
        name="rag",
        display_name="RAG系统评估",
        script_path="tests/evaluation/run_rag_evaluation.py",
        estimated_duration_seconds=180,
        estimated_cost=CostEstimate(
            input_tokens=50000,
            output_tokens=10000,
            estimated_cost_usd=0.15,
            estimated_cost_cny=1.08
        ),
        requires_llm=True,
        description="评估检索增强生成系统的召回率、精确率和答案质量"
    ),
    ModuleConfig(
        name="routing",
        display_name="路由系统评估",
        script_path="tests/evaluation/run_routing_evaluation.py",
        estimated_duration_seconds=120,
        estimated_cost=CostEstimate(
            input_tokens=30000,
            output_tokens=5000,
            estimated_cost_usd=0.08,
            estimated_cost_cny=0.58
        ),
        requires_llm=True,
        description="评估意图识别、复杂度评估和执行模式路由准确率"
    ),
    ModuleConfig(
        name="approval",
        display_name="审批流程评估",
        script_path="tests/evaluation/run_approval_evaluation.py",
        estimated_duration_seconds=30,
        estimated_cost=CostEstimate(
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
            estimated_cost_cny=0.0
        ),
        requires_llm=False,
        description="确定性测试审批规则、阈值逻辑和边界条件"
    ),
    ModuleConfig(
        name="load",
        display_name="负载压测",
        script_path="tests/evaluation/run_load_test.py",
        estimated_duration_seconds=90,
        estimated_cost=CostEstimate(
            input_tokens=100000,
            output_tokens=20000,
            estimated_cost_usd=0.30,
            estimated_cost_cny=2.16
        ),
        requires_llm=False,  # 使用Mock LLM
        description="测试系统并发性能、延迟分布和错误率"
    )
]


# ============================================================================
# 进度条显示
# ============================================================================

class ProgressBar:
    """简单的进度条实现"""

    def __init__(self, total: int, width: int = 50, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0
        self.start_time = time.time()

    def update(self, current: int):
        """更新进度"""
        self.current = current
        percent = current / self.total
        filled = int(self.width * percent)
        bar = '=' * filled + '-' * (self.width - filled)

        # 计算预估剩余时间
        elapsed = time.time() - self.start_time
        if current > 0:
            eta_seconds = (elapsed / current) * (self.total - current)
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "N/A"

        print(f'\r{self.prefix}: [{bar}] {percent*100:.1f}% | ETA: {eta}', end='', flush=True)

    def finish(self):
        """完成进度条"""
        self.update(self.total)
        print()


# ============================================================================
# 核心执行逻辑
# ============================================================================

class EvaluationRunner:
    """评估运行器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ModuleResult] = []

    def estimate_total_cost(self, modules: List[ModuleConfig]) -> CostEstimate:
        """预估总成本"""
        total = CostEstimate()
        for module in modules:
            total = total.add(module.estimated_cost)
        return total

    def estimate_total_duration(self, modules: List[ModuleConfig]) -> int:
        """预估总时长（秒）"""
        return sum(m.estimated_duration_seconds for m in modules)

    def run_module(self, module: ModuleConfig, progress_callback=None) -> ModuleResult:
        """运行单个评估模块"""
        logger.info(f"\n{'='*80}")
        logger.info(f"开始运行: {module.display_name}")
        logger.info(f"脚本: {module.script_path}")
        logger.info(f"预估时长: {module.estimated_duration_seconds}秒")
        if module.requires_llm:
            logger.info(f"预估成本: ${module.estimated_cost.estimated_cost_usd:.4f} (¥{module.estimated_cost.estimated_cost_cny:.2f})")
        logger.info(f"{'='*80}\n")

        start_time = datetime.now()

        # 构建命令
        script_path = project_root / module.script_path
        if not script_path.exists():
            logger.error(f"脚本不存在: {script_path}")
            return ModuleResult(
                module_name=module.name,
                success=False,
                duration_seconds=0,
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=-1,
                error_message=f"Script not found: {script_path}"
            )

        cmd = [sys.executable, str(script_path)]

        # 添加输出目录参数
        if module.name == "approval":
            cmd.extend(["--output-dir", str(self.output_dir)])
        elif module.name == "load":
            cmd.extend(["--concurrency", "10", "--requests", "50"])

        # 执行脚本
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            stdout, stderr = process.communicate()
            exit_code = process.returncode

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            success = exit_code == 0

            # 提取指标
            metrics = self._extract_metrics(stdout, module.name)

            result = ModuleResult(
                module_name=module.name,
                success=success,
                duration_seconds=duration,
                start_time=start_time,
                end_time=end_time,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                metrics=metrics,
                actual_cost=None,  # TODO: 从输出中提取实际成本
                error_message="" if success else f"Exit code: {exit_code}"
            )

            logger.info(f"\n{'='*80}")
            logger.info(f"完成: {module.display_name}")
            logger.info(f"状态: {'成功' if success else '失败'}")
            logger.info(f"耗时: {duration:.1f}秒")
            if metrics:
                logger.info(f"关键指标: {json.dumps(metrics, ensure_ascii=False, indent=2)}")
            logger.info(f"{'='*80}\n")

            return result

        except Exception as e:
            logger.error(f"执行失败: {str(e)}")
            return ModuleResult(
                module_name=module.name,
                success=False,
                duration_seconds=0,
                start_time=start_time,
                end_time=datetime.now(),
                exit_code=-1,
                error_message=str(e)
            )

    def _extract_metrics(self, stdout: str, module_name: str) -> Dict[str, Any]:
        """从输出中提取关键指标"""
        metrics = {}

        try:
            # 尝试从JSON输出中提取
            lines = stdout.split('\n')
            for line in lines:
                if 'accuracy' in line.lower() or 'precision' in line.lower():
                    # 提取百分比数字
                    import re
                    numbers = re.findall(r'(\d+\.\d+)%', line)
                    if numbers:
                        if 'accuracy' in line.lower():
                            metrics['accuracy'] = float(numbers[0])
                        elif 'precision' in line.lower():
                            metrics['precision'] = float(numbers[0])

                # 提取召回率
                if 'recall' in line.lower():
                    import re
                    numbers = re.findall(r'(\d+\.\d+)%', line)
                    if numbers:
                        metrics['recall'] = float(numbers[0])

                # 提取F1分数
                if 'f1' in line.lower():
                    import re
                    numbers = re.findall(r'(\d+\.\d+)', line)
                    if numbers:
                        metrics['f1'] = float(numbers[0])

        except Exception as e:
            logger.warning(f"提取指标失败: {str(e)}")

        return metrics

    def run_all(self, modules: List[ModuleConfig]) -> EvaluationSummary:
        """运行所有评估模块"""
        start_time = datetime.now()

        # 显示预估信息
        total_cost = self.estimate_total_cost(modules)
        total_duration = self.estimate_total_duration(modules)

        logger.info(f"\n{'='*80}")
        logger.info(f"评估任务总览")
        logger.info(f"{'='*80}")
        logger.info(f"待运行模块数: {len(modules)}")
        for module in modules:
            logger.info(f"  - {module.display_name} ({module.estimated_duration_seconds}秒)")
        logger.info(f"\n预估总时长: {total_duration}秒 (~{total_duration//60}分钟)")
        logger.info(f"预估总成本: ${total_cost.estimated_cost_usd:.4f} (¥{total_cost.estimated_cost_cny:.2f})")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"{'='*80}\n")

        # 询问确认
        try:
            response = input("是否继续? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                logger.info("已取消评估")
                return None
        except KeyboardInterrupt:
            logger.info("\n已取消评估")
            return None

        # 运行模块
        progress = ProgressBar(total=len(modules), prefix="总体进度")

        for idx, module in enumerate(modules):
            result = self.run_module(module)
            self.results.append(result)
            progress.update(idx + 1)

        progress.finish()

        end_time = datetime.now()
        total_duration_actual = (end_time - start_time).total_seconds()

        # 生成汇总
        summary = EvaluationSummary(
            total_duration_seconds=total_duration_actual,
            start_time=start_time,
            end_time=end_time,
            modules_run=len(modules),
            modules_success=sum(1 for r in self.results if r.success),
            modules_failed=sum(1 for r in self.results if not r.success),
            total_estimated_cost=total_cost,
            total_actual_cost=None,  # TODO: 汇总实际成本
            module_results=self.results
        )

        return summary

    def generate_report(self, summary: EvaluationSummary) -> Path:
        """生成评估总报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"evaluation_summary_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 评估总报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 执行摘要
            f.write("## 执行摘要\n\n")
            f.write(f"- 开始时间: {summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 结束时间: {summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 总耗时: {summary.total_duration_seconds:.1f}秒 (~{summary.total_duration_seconds/60:.1f}分钟)\n")
            f.write(f"- 运行模块数: {summary.modules_run}\n")
            f.write(f"- 成功: {summary.modules_success}\n")
            f.write(f"- 失败: {summary.modules_failed}\n")
            f.write(f"- 成功率: {summary.modules_success/summary.modules_run*100:.1f}%\n\n")

            # 成本分析
            f.write("## 成本分析\n\n")
            f.write(f"- 预估输入Token: {summary.total_estimated_cost.input_tokens:,}\n")
            f.write(f"- 预估输出Token: {summary.total_estimated_cost.output_tokens:,}\n")
            f.write(f"- 预估成本: ${summary.total_estimated_cost.estimated_cost_usd:.4f} (¥{summary.total_estimated_cost.estimated_cost_cny:.2f})\n\n")

            # 模块详情
            f.write("## 模块执行详情\n\n")
            for result in summary.module_results:
                status_icon = "✓" if result.success else "✗"
                f.write(f"### {status_icon} {result.module_name.upper()}\n\n")
                f.write(f"- 状态: {'成功' if result.success else '失败'}\n")
                f.write(f"- 耗时: {result.duration_seconds:.1f}秒\n")
                f.write(f"- 开始时间: {result.start_time.strftime('%H:%M:%S')}\n")
                f.write(f"- 结束时间: {result.end_time.strftime('%H:%M:%S')}\n")

                if result.metrics:
                    f.write(f"- 关键指标:\n")
                    for key, value in result.metrics.items():
                        if isinstance(value, float):
                            f.write(f"  - {key}: {value:.2f}\n")
                        else:
                            f.write(f"  - {key}: {value}\n")

                if not result.success:
                    f.write(f"- 错误信息: {result.error_message}\n")

                f.write("\n")

            # 结论与建议
            f.write("## 结论与建议\n\n")
            if summary.modules_failed == 0:
                f.write("所有评估模块均成功执行，系统各项功能正常。\n\n")
            else:
                f.write(f"有 {summary.modules_failed} 个模块执行失败，建议检查错误日志并修复问题。\n\n")

            f.write("### 下一步行动\n\n")
            f.write("1. 查看各模块详细报告\n")
            f.write("2. 针对失败模块进行问题排查\n")
            f.write("3. 针对性能瓶颈进行优化\n")
            f.write("4. 更新文档和测试用例\n")

        logger.info(f"\n总报告已生成: {report_path}")
        return report_path


# ============================================================================
# 命令行入口
# ============================================================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="一键运行所有评估模块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有评估
  python tests/evaluation/run_all_evaluations.py

  # 仅运行RAG和Routing评估
  python tests/evaluation/run_all_evaluations.py --modules rag routing

  # 跳过负载测试
  python tests/evaluation/run_all_evaluations.py --skip load

  # 自定义输出目录
  python tests/evaluation/run_all_evaluations.py --output-dir custom_reports/
        """
    )

    parser.add_argument(
        '--modules',
        nargs='+',
        choices=['rag', 'routing', 'approval', 'load'],
        help='指定要运行的模块（默认运行所有）'
    )

    parser.add_argument(
        '--skip',
        nargs='+',
        choices=['rag', 'routing', 'approval', 'load'],
        help='跳过指定的模块'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports/evaluation',
        help='评估报告输出目录（默认: reports/evaluation）'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='跳过执行前确认'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 确定要运行的模块
    if args.modules:
        # 仅运行指定模块
        selected_modules = [m for m in EVALUATION_MODULES if m.name in args.modules]
    else:
        # 运行所有模块（除非被跳过）
        skip_list = args.skip or []
        selected_modules = [m for m in EVALUATION_MODULES if m.name not in skip_list]

    if not selected_modules:
        logger.error("没有选择任何模块运行")
        return 1

    # 创建运行器
    output_dir = Path(args.output_dir)
    runner = EvaluationRunner(output_dir)

    # 运行评估
    summary = runner.run_all(selected_modules)

    if summary is None:
        return 1

    # 生成报告
    report_path = runner.generate_report(summary)

    # 打印最终总结
    logger.info(f"\n{'='*80}")
    logger.info(f"评估完成!")
    logger.info(f"{'='*80}")
    logger.info(f"总耗时: {summary.total_duration_seconds:.1f}秒")
    logger.info(f"成功: {summary.modules_success}/{summary.modules_run}")
    logger.info(f"失败: {summary.modules_failed}/{summary.modules_run}")
    logger.info(f"总报告: {report_path}")
    logger.info(f"{'='*80}\n")

    # 返回退出码
    return 0 if summary.modules_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
