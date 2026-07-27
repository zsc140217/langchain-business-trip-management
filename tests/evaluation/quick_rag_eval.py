#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速RAG评估 - 基于现有recall_analysis.json数据
生成评估报告而不需要重新运行RAG系统
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_recall_data():
    """加载召回分析数据"""
    recall_file = Path(__file__).parent / "recall_analysis.json"
    with open(recall_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def calculate_metrics(data):
    """计算评估指标"""
    # 向量检索
    vector_cases = data.get('vector', [])

    # 基础统计
    total = len(vector_cases)
    recall_at_5_count = sum(1 for case in vector_cases if case.get('recall_at_5', False))

    # 按难度分类
    by_difficulty = defaultdict(list)
    for case in vector_cases:
        difficulty = case.get('difficulty', 'UNKNOWN')
        by_difficulty[difficulty].append(case)

    # 按类别分类
    by_category = defaultdict(list)
    for case in vector_cases:
        category = case.get('category', 'UNKNOWN')
        by_category[category].append(case)

    # 失败案例
    failed_cases = [case for case in vector_cases if not case.get('recall_at_5', False)]

    return {
        'total': total,
        'recall_at_5_count': recall_at_5_count,
        'recall_at_5_rate': recall_at_5_count / total if total > 0 else 0,
        'by_difficulty': by_difficulty,
        'by_category': by_category,
        'failed_cases': failed_cases
    }

def generate_report(metrics):
    """生成Markdown报告"""
    report = []
    report.append("# RAG检索质量评估报告（基于历史数据）")
    report.append("")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**数据来源**: recall_analysis.json")
    report.append(f"**评估方法**: 向量检索召回分析")
    report.append("")

    # 执行摘要
    report.append("## 执行摘要")
    report.append("")
    report.append(f"- **测试总数**: {metrics['total']}")
    report.append(f"- **Recall@5成功**: {metrics['recall_at_5_count']}")
    report.append(f"- **Recall@5准确率**: {metrics['recall_at_5_rate']:.1%}")
    report.append("")

    # 按难度统计
    report.append("## 按难度分类")
    report.append("")
    report.append("| 难度 | 总数 | 召回成功 | 召回率 |")
    report.append("|------|------|----------|--------|")

    for difficulty in ['EASY', 'MEDIUM', 'HARD']:
        cases = metrics['by_difficulty'].get(difficulty, [])
        if cases:
            total = len(cases)
            success = sum(1 for c in cases if c.get('recall_at_5', False))
            rate = success / total if total > 0 else 0
            report.append(f"| {difficulty} | {total} | {success} | {rate:.1%} |")

    report.append("")

    # 按类别统计
    report.append("## 按类别分类")
    report.append("")
    report.append("| 类别 | 总数 | 召回成功 | 召回率 |")
    report.append("|------|------|----------|--------|")

    for category, cases in sorted(metrics['by_category'].items()):
        total = len(cases)
        success = sum(1 for c in cases if c.get('recall_at_5', False))
        rate = success / total if total > 0 else 0
        report.append(f"| {category} | {total} | {success} | {rate:.1%} |")

    report.append("")

    # 失败案例分析
    if metrics['failed_cases']:
        report.append("## 失败案例分析")
        report.append("")
        report.append(f"共 {len(metrics['failed_cases'])} 个召回失败案例：")
        report.append("")

        for i, case in enumerate(metrics['failed_cases'][:10], 1):
            report.append(f"### 案例 {i}: {case.get('query', 'N/A')}")
            report.append("")
            report.append(f"- **难度**: {case.get('difficulty', 'UNKNOWN')}")
            report.append(f"- **类别**: {case.get('category', 'UNKNOWN')}")
            report.append(f"- **失败原因**: {case.get('failure_reason', '未标注')}")
            report.append("")

        if len(metrics['failed_cases']) > 10:
            report.append(f"（还有 {len(metrics['failed_cases']) - 10} 个失败案例未显示）")
            report.append("")

    # 结论
    report.append("## 结论与建议")
    report.append("")

    recall_rate = metrics['recall_at_5_rate']
    if recall_rate >= 0.8:
        report.append("检索质量: **优秀** ✅")
    elif recall_rate >= 0.7:
        report.append("检索质量: **良好** ✓")
    elif recall_rate >= 0.6:
        report.append("检索质量: **及格** ⚠️")
    else:
        report.append("检索质量: **需改进** ❌")

    report.append("")
    report.append("### 建议")
    report.append("")

    # 按难度分析建议
    hard_cases = metrics['by_difficulty'].get('HARD', [])
    if hard_cases:
        hard_success = sum(1 for c in hard_cases if c.get('recall_at_5', False))
        hard_rate = hard_success / len(hard_cases)
        if hard_rate < 0.6:
            report.append(f"- HARD难度召回率仅{hard_rate:.1%}，建议增强多条件查询能力")

    # 失败案例建议
    if len(metrics['failed_cases']) > 5:
        report.append(f"- 共有{len(metrics['failed_cases'])}个失败案例，建议进行Bad Case分析和模型优化")

    report.append("")

    return "\n".join(report)

def main():
    """主函数"""
    print("=" * 80)
    print("RAG检索质量评估（基于历史数据）")
    print("=" * 80)
    print()

    # 加载数据
    print("[1/3] 加载recall_analysis.json...")
    data = load_recall_data()
    print(f"     加载完成，共 {len(data.get('vector', []))} 条数据")
    print()

    # 计算指标
    print("[2/3] 计算评估指标...")
    metrics = calculate_metrics(data)
    print(f"     Recall@5准确率: {metrics['recall_at_5_rate']:.1%}")
    print()

    # 生成报告
    print("[3/3] 生成评估报告...")
    report = generate_report(metrics)

    # 保存报告
    output_dir = Path(__file__).parent / "reports" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"rag_evaluation_report_{timestamp}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"     报告已保存: {report_file}")
    print()

    print("=" * 80)
    print("评估完成！")
    print("=" * 80)
    print()

    # 输出关键指标
    print("关键指标:")
    print(f"  - 测试总数: {metrics['total']}")
    print(f"  - Recall@5准确率: {metrics['recall_at_5_rate']:.1%}")
    print(f"  - 失败案例数: {len(metrics['failed_cases'])}")
    print()

if __name__ == "__main__":
    main()
