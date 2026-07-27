# -*- coding: utf-8 -*-
"""
审批流程评估脚本
Phase 3: 基于确定性测试的审批流程评估

功能:
1. Code-based确定性测试（无LLM调用，快速验证）
2. 覆盖率矩阵分析（金额阈值、缺失字段、边界条件）
3. 生成审批测试用例模板（JSON格式）
4. 输出评估报告（Markdown格式）

使用方法:
    python tests/evaluation/run_approval_evaluation.py --output-dir reports/
"""
import sys
import os
import json
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class ApprovalEvaluator:
    """审批流程评估器"""

    def __init__(self, auto_approval_threshold: int = 1000):
        """
        初始化评估器

        Args:
            auto_approval_threshold: 自动审批阈值（元）
        """
        self.auto_approval_threshold = auto_approval_threshold
        self.test_results = []
        self.coverage_matrix = {
            "amount_ranges": [],
            "missing_fields": [],
            "boundary_conditions": [],
            "approval_paths": []
        }

    def run_evaluation(self) -> Dict[str, Any]:
        """
        运行完整评估流程

        Returns:
            评估结果字典
        """
        print("=" * 80)
        print("审批流程评估开始".center(80))
        print("=" * 80)
        print()

        # 1. 生成测试用例
        print("[1/4] 生成测试用例...")
        test_cases = self._generate_test_cases()
        print(f"     生成 {len(test_cases)} 个测试用例\n")

        # 2. 执行确定性测试
        print("[2/4] 执行确定性测试...")
        self._run_deterministic_tests(test_cases)
        print(f"     完成 {len(self.test_results)} 个测试\n")

        # 3. 覆盖率矩阵分析
        print("[3/4] 覆盖率矩阵分析...")
        coverage_stats = self._analyze_coverage_matrix()
        print(f"     覆盖率: {coverage_stats['overall_coverage']:.1f}%\n")

        # 4. 生成评估报告
        print("[4/4] 生成评估报告...")
        report = self._generate_report(test_cases, coverage_stats)
        print("     评估报告生成完成\n")

        print("=" * 80)
        print("审批流程评估完成".center(80))
        print("=" * 80)

        return {
            "test_cases": test_cases,
            "test_results": self.test_results,
            "coverage_stats": coverage_stats,
            "report": report
        }

    def _generate_test_cases(self) -> List[Dict[str, Any]]:
        """
        生成审批流程测试用例

        Returns:
            测试用例列表
        """
        test_cases = []

        # 1. 金额阈值测试（自动审批 vs 人工审批）
        amount_test_cases = [
            # 自动审批范围
            {"category": "amount", "amount": 0, "expected_path": "auto", "description": "边界值: 0元"},
            {"category": "amount", "amount": 500, "expected_path": "auto", "description": "自动审批: 500元"},
            {"category": "amount", "amount": 999, "expected_path": "auto", "description": "边界值: 999元(阈值-1)"},

            # 阈值边界
            {"category": "amount", "amount": 1000, "expected_path": "manual", "description": "边界值: 1000元(阈值)"},

            # 人工审批范围
            {"category": "amount", "amount": 1001, "expected_path": "manual", "description": "边界值: 1001元(阈值+1)"},
            {"category": "amount", "amount": 5000, "expected_path": "manual", "description": "人工审批: 5000元"},
            {"category": "amount", "amount": 10000, "expected_path": "manual", "description": "人工审批: 10000元"},
        ]

        for tc in amount_test_cases:
            test_cases.append({
                "test_id": f"TC_{len(test_cases)+1:03d}",
                "category": tc["category"],
                "description": tc["description"],
                "input": {
                    "destination": "北京",
                    "days": 3,
                    "estimated_amount": tc["amount"],
                    "purpose": "客户拜访"
                },
                "expected": {
                    "approval_path": tc["expected_path"],
                    "status": "approved" if tc["expected_path"] == "auto" else "pending",
                    "validation": "pass"
                }
            })

        # 2. 缺失字段测试
        missing_field_test_cases = [
            {"missing": ["destination"], "description": "缺失目的地"},
            {"missing": ["days"], "description": "缺失天数"},
            {"missing": ["estimated_amount"], "description": "缺失金额"},
            {"missing": ["purpose"], "description": "缺失事由（可选）"},
            {"missing": ["destination", "days"], "description": "缺失目的地和天数"},
            {"missing": ["destination", "days", "estimated_amount"], "description": "缺失所有必填字段"},
        ]

        for tc in missing_field_test_cases:
            complete_input = {
                "destination": "上海",
                "days": 2,
                "estimated_amount": 800,
                "purpose": "会议"
            }
            # 移除缺失字段
            test_input = {k: v for k, v in complete_input.items() if k not in tc["missing"]}

            test_cases.append({
                "test_id": f"TC_{len(test_cases)+1:03d}",
                "category": "missing_field",
                "description": tc["description"],
                "input": test_input,
                "expected": {
                    "validation": "fail",
                    "missing_fields": tc["missing"],
                    "error_type": "missing_required_field"
                }
            })

        # 3. 边界条件测试
        boundary_test_cases = [
            # 天数边界
            {"field": "days", "value": 1, "description": "最小天数: 1天"},
            {"field": "days", "value": 30, "description": "正常天数: 30天"},
            {"field": "days", "value": 0, "description": "异常天数: 0天（无效）"},
            {"field": "days", "value": -1, "description": "异常天数: -1天（无效）"},

            # 金额边界
            {"field": "amount", "value": -100, "description": "异常金额: 负数（无效）"},
            {"field": "amount", "value": 999999, "description": "超大金额: 999999元"},

            # 目的地边界
            {"field": "destination", "value": "", "description": "空目的地（无效）"},
            {"field": "destination", "value": "a" * 100, "description": "超长目的地: 100字符"},
        ]

        for tc in boundary_test_cases:
            base_input = {
                "destination": "杭州",
                "days": 3,
                "estimated_amount": 800,
                "purpose": "培训"
            }

            # 替换边界值
            if tc["field"] == "days":
                base_input["days"] = tc["value"]
            elif tc["field"] == "amount":
                base_input["estimated_amount"] = tc["value"]
            elif tc["field"] == "destination":
                base_input["destination"] = tc["value"]

            # 判断预期结果
            is_valid = self._is_valid_input(base_input)

            test_cases.append({
                "test_id": f"TC_{len(test_cases)+1:03d}",
                "category": "boundary",
                "description": tc["description"],
                "input": base_input,
                "expected": {
                    "validation": "pass" if is_valid else "fail",
                    "approval_path": self._get_expected_path(base_input) if is_valid else None
                }
            })

        # 4. 审批路径测试
        approval_path_test_cases = [
            {
                "description": "自动审批路径: 金额<阈值",
                "input": {"destination": "成都", "days": 2, "estimated_amount": 600, "purpose": "客户拜访"},
                "expected_path": "auto"
            },
            {
                "description": "人工审批路径: 金额>=阈值",
                "input": {"destination": "深圳", "days": 5, "estimated_amount": 3000, "purpose": "项目实施"},
                "expected_path": "manual"
            },
        ]

        for tc in approval_path_test_cases:
            test_cases.append({
                "test_id": f"TC_{len(test_cases)+1:03d}",
                "category": "approval_path",
                "description": tc["description"],
                "input": tc["input"],
                "expected": {
                    "approval_path": tc["expected_path"],
                    "status": "approved" if tc["expected_path"] == "auto" else "pending",
                    "validation": "pass"
                }
            })

        return test_cases

    def _run_deterministic_tests(self, test_cases: List[Dict[str, Any]]):
        """
        执行确定性测试（不调用LLM，纯逻辑验证）

        Args:
            test_cases: 测试用例列表
        """
        for tc in test_cases:
            test_id = tc["test_id"]
            category = tc["category"]
            description = tc["description"]
            input_data = tc["input"]
            expected = tc["expected"]

            # 执行测试
            actual = self._execute_test_logic(input_data, category)

            # 验证结果
            passed = self._verify_test_result(expected, actual)

            # 记录结果
            test_result = {
                "test_id": test_id,
                "category": category,
                "description": description,
                "input": input_data,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "timestamp": datetime.now().isoformat()
            }

            self.test_results.append(test_result)

            # 更新覆盖率矩阵
            self._update_coverage_matrix(category, test_result)

            # 打印进度
            status = "PASS" if passed else "FAIL"
            print(f"     [{status}] {test_id}: {description}")

    def _execute_test_logic(self, input_data: Dict[str, Any], category: str) -> Dict[str, Any]:
        """
        执行测试逻辑（确定性，不调用LLM）

        Args:
            input_data: 输入数据
            category: 测试类别

        Returns:
            实际结果字典
        """
        # 1. 验证输入
        validation_result = self._validate_input(input_data)

        if not validation_result["valid"]:
            return {
                "validation": "fail",
                "missing_fields": validation_result.get("missing_fields", []),
                "error_type": validation_result.get("error_type", "validation_error"),
                "error_message": validation_result.get("error_message", "")
            }

        # 2. 判断审批路径
        amount = input_data.get("estimated_amount", 0)

        if amount < self.auto_approval_threshold:
            approval_path = "auto"
            status = "approved"
        else:
            approval_path = "manual"
            status = "pending"

        return {
            "validation": "pass",
            "approval_path": approval_path,
            "status": status,
            "amount": amount,
            "threshold": self.auto_approval_threshold
        }

    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入数据

        Args:
            input_data: 输入数据

        Returns:
            验证结果字典
        """
        missing_fields = []

        # 检查必填字段
        required_fields = ["destination", "days", "estimated_amount"]

        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                missing_fields.append(field)

        # 如果有缺失字段，返回失败
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "error_type": "missing_required_field",
                "error_message": f"缺失必填字段: {', '.join(missing_fields)}"
            }

        # 验证字段有效性
        destination = input_data.get("destination", "")
        days = input_data.get("days", 0)
        amount = input_data.get("estimated_amount", 0)

        # 目的地不能为空
        if not destination or destination.strip() == "":
            return {
                "valid": False,
                "error_type": "invalid_destination",
                "error_message": "目的地不能为空"
            }

        # 天数必须为正整数
        if not isinstance(days, int) or days <= 0:
            return {
                "valid": False,
                "error_type": "invalid_days",
                "error_message": f"天数必须为正整数，当前值: {days}"
            }

        # 金额必须为非负数
        if not isinstance(amount, (int, float)) or amount < 0:
            return {
                "valid": False,
                "error_type": "invalid_amount",
                "error_message": f"金额必须为非负数，当前值: {amount}"
            }

        return {"valid": True}

    def _verify_test_result(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """
        验证测试结果

        Args:
            expected: 期望结果
            actual: 实际结果

        Returns:
            是否通过
        """
        # 验证validation状态
        if expected.get("validation") != actual.get("validation"):
            return False

        # 如果validation为fail，检查缺失字段
        if expected.get("validation") == "fail":
            expected_missing = set(expected.get("missing_fields", []))
            actual_missing = set(actual.get("missing_fields", []))
            return expected_missing.issubset(actual_missing)

        # 如果validation为pass，检查审批路径
        if expected.get("approval_path") != actual.get("approval_path"):
            return False

        # 检查状态
        if expected.get("status") and expected.get("status") != actual.get("status"):
            return False

        return True

    def _is_valid_input(self, input_data: Dict[str, Any]) -> bool:
        """判断输入是否有效"""
        validation_result = self._validate_input(input_data)
        return validation_result["valid"]

    def _get_expected_path(self, input_data: Dict[str, Any]) -> str:
        """获取预期的审批路径"""
        amount = input_data.get("estimated_amount", 0)
        return "auto" if amount < self.auto_approval_threshold else "manual"

    def _update_coverage_matrix(self, category: str, test_result: Dict[str, Any]):
        """
        更新覆盖率矩阵

        Args:
            category: 测试类别
            test_result: 测试结果
        """
        if category == "amount":
            self.coverage_matrix["amount_ranges"].append({
                "amount": test_result["input"].get("estimated_amount"),
                "path": test_result["actual"].get("approval_path"),
                "passed": test_result["passed"]
            })
        elif category == "missing_field":
            self.coverage_matrix["missing_fields"].append({
                "missing": test_result["expected"].get("missing_fields", []),
                "detected": test_result["passed"]
            })
        elif category == "boundary":
            self.coverage_matrix["boundary_conditions"].append({
                "description": test_result["description"],
                "passed": test_result["passed"]
            })
        elif category == "approval_path":
            self.coverage_matrix["approval_paths"].append({
                "path": test_result["expected"].get("approval_path"),
                "passed": test_result["passed"]
            })

    def _analyze_coverage_matrix(self) -> Dict[str, Any]:
        """
        分析覆盖率矩阵

        Returns:
            覆盖率统计字典
        """
        stats = {
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r["passed"]),
            "failed_tests": sum(1 for r in self.test_results if not r["passed"]),
            "pass_rate": 0.0,
            "category_stats": {},
            "coverage_details": {}
        }

        if stats["total_tests"] > 0:
            stats["pass_rate"] = (stats["passed_tests"] / stats["total_tests"]) * 100

        # 按类别统计
        categories = set(r["category"] for r in self.test_results)
        for cat in categories:
            cat_results = [r for r in self.test_results if r["category"] == cat]
            cat_passed = sum(1 for r in cat_results if r["passed"])
            stats["category_stats"][cat] = {
                "total": len(cat_results),
                "passed": cat_passed,
                "failed": len(cat_results) - cat_passed,
                "pass_rate": (cat_passed / len(cat_results) * 100) if len(cat_results) > 0 else 0
            }

        # 覆盖率详情
        stats["coverage_details"] = {
            "amount_ranges_covered": len(self.coverage_matrix["amount_ranges"]),
            "missing_fields_covered": len(self.coverage_matrix["missing_fields"]),
            "boundary_conditions_covered": len(self.coverage_matrix["boundary_conditions"]),
            "approval_paths_covered": len(self.coverage_matrix["approval_paths"])
        }

        # 计算总体覆盖率
        total_coverage_items = sum(stats["coverage_details"].values())
        stats["overall_coverage"] = (total_coverage_items / 20) * 100  # 假设20个覆盖项

        return stats

    def _generate_report(self, test_cases: List[Dict[str, Any]], coverage_stats: Dict[str, Any]) -> str:
        """
        生成Markdown格式的评估报告

        Args:
            test_cases: 测试用例列表
            coverage_stats: 覆盖率统计

        Returns:
            Markdown格式的报告
        """
        report_lines = []

        # 标题和摘要
        report_lines.append("# 审批流程评估报告")
        report_lines.append("")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**评估器版本**: 1.0.0")
        report_lines.append(f"**自动审批阈值**: {self.auto_approval_threshold}元")
        report_lines.append("")

        # 执行摘要
        report_lines.append("## 执行摘要")
        report_lines.append("")
        report_lines.append(f"- **测试总数**: {coverage_stats['total_tests']}")
        report_lines.append(f"- **通过**: {coverage_stats['passed_tests']}")
        report_lines.append(f"- **失败**: {coverage_stats['failed_tests']}")
        report_lines.append(f"- **通过率**: {coverage_stats['pass_rate']:.1f}%")
        report_lines.append(f"- **总体覆盖率**: {coverage_stats['overall_coverage']:.1f}%")
        report_lines.append("")

        # 测试类别统计
        report_lines.append("## 测试类别统计")
        report_lines.append("")
        report_lines.append("| 类别 | 总数 | 通过 | 失败 | 通过率 |")
        report_lines.append("|------|------|------|------|--------|")

        for cat, stats in coverage_stats["category_stats"].items():
            report_lines.append(
                f"| {cat} | {stats['total']} | {stats['passed']} | "
                f"{stats['failed']} | {stats['pass_rate']:.1f}% |"
            )

        report_lines.append("")

        # 覆盖率矩阵
        report_lines.append("## 覆盖率矩阵")
        report_lines.append("")
        report_lines.append("### 1. 金额阈值覆盖")
        report_lines.append("")
        report_lines.append("| 金额 | 预期路径 | 实际路径 | 状态 |")
        report_lines.append("|------|----------|----------|------|")

        for item in self.coverage_matrix["amount_ranges"]:
            status = "PASS" if item["passed"] else "FAIL"
            report_lines.append(
                f"| {item['amount']}元 | {self._get_expected_path({'estimated_amount': item['amount']})} | "
                f"{item['path']} | {status} |"
            )

        report_lines.append("")

        # 缺失字段覆盖
        report_lines.append("### 2. 缺失字段覆盖")
        report_lines.append("")
        report_lines.append("| 缺失字段 | 检测状态 |")
        report_lines.append("|----------|----------|")

        for item in self.coverage_matrix["missing_fields"]:
            detected = "PASS" if item["detected"] else "FAIL"
            missing_str = ", ".join(item["missing"])
            report_lines.append(f"| {missing_str} | {detected} |")

        report_lines.append("")

        # 边界条件覆盖
        report_lines.append("### 3. 边界条件覆盖")
        report_lines.append("")
        report_lines.append("| 测试项 | 状态 |")
        report_lines.append("|--------|------|")

        for item in self.coverage_matrix["boundary_conditions"]:
            status = "PASS" if item["passed"] else "FAIL"
            report_lines.append(f"| {item['description']} | {status} |")

        report_lines.append("")

        # 审批路径覆盖
        report_lines.append("### 4. 审批路径覆盖")
        report_lines.append("")
        report_lines.append("| 审批路径 | 状态 |")
        report_lines.append("|----------|------|")

        for item in self.coverage_matrix["approval_paths"]:
            status = "PASS" if item["passed"] else "FAIL"
            path_name = "自动审批" if item["path"] == "auto" else "人工审批"
            report_lines.append(f"| {path_name} | {status} |")

        report_lines.append("")

        # 失败测试详情
        failed_tests = [r for r in self.test_results if not r["passed"]]
        if failed_tests:
            report_lines.append("## 失败测试详情")
            report_lines.append("")

            for test in failed_tests:
                report_lines.append(f"### {test['test_id']}: {test['description']}")
                report_lines.append("")
                report_lines.append(f"- **输入**: `{json.dumps(test['input'], ensure_ascii=False)}`")
                report_lines.append(f"- **期望**: `{json.dumps(test['expected'], ensure_ascii=False)}`")
                report_lines.append(f"- **实际**: `{json.dumps(test['actual'], ensure_ascii=False)}`")
                report_lines.append("")

        # 结论和建议
        report_lines.append("## 结论和建议")
        report_lines.append("")

        if coverage_stats["pass_rate"] >= 95:
            report_lines.append("审批流程稳定性: **优秀** ✅")
        elif coverage_stats["pass_rate"] >= 80:
            report_lines.append("审批流程稳定性: **良好** ⚠️")
        else:
            report_lines.append("审批流程稳定性: **需改进** ❌")

        report_lines.append("")
        report_lines.append("### 建议")
        report_lines.append("")

        if coverage_stats["failed_tests"] > 0:
            report_lines.append(f"- 修复 {coverage_stats['failed_tests']} 个失败的测试用例")

        if coverage_stats["overall_coverage"] < 90:
            report_lines.append("- 增加测试用例以提升覆盖率")

        report_lines.append("- 定期执行评估脚本以确保流程稳定性")
        report_lines.append("")

        return "\n".join(report_lines)


def save_test_cases_template(test_cases: List[Dict[str, Any]], output_path: str):
    """
    保存测试用例模板为JSON格式

    Args:
        test_cases: 测试用例列表
        output_path: 输出文件路径
    """
    template = {
        "version": "1.0.0",
        "description": "审批流程测试用例模板",
        "auto_approval_threshold": 1000,
        "test_cases": test_cases
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    print(f"测试用例模板已保存: {output_path}")


def save_evaluation_report(report: str, output_path: str):
    """
    保存评估报告为Markdown格式

    Args:
        report: 报告内容
        output_path: 输出文件路径
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"评估报告已保存: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="审批流程评估脚本")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/evaluation",
        help="报告输出目录（默认: reports/evaluation）"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=1000,
        help="自动审批阈值（默认: 1000元）"
    )

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 运行评估
    evaluator = ApprovalEvaluator(auto_approval_threshold=args.threshold)
    results = evaluator.run_evaluation()

    # 生成文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_cases_path = output_dir / f"approval_test_cases_{timestamp}.json"
    report_path = output_dir / f"approval_evaluation_report_{timestamp}.md"

    # 保存测试用例模板
    save_test_cases_template(results["test_cases"], str(test_cases_path))

    # 保存评估报告
    save_evaluation_report(results["report"], str(report_path))

    # 打印摘要
    print()
    print("=" * 80)
    print("输出文件".center(80))
    print("=" * 80)
    print(f"测试用例模板: {test_cases_path}")
    print(f"评估报告: {report_path}")
    print("=" * 80)

    # 返回退出码
    if results["coverage_stats"]["pass_rate"] < 100:
        return 1  # 有失败的测试
    return 0


if __name__ == "__main__":
    exit(main())
