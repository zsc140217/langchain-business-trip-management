"""
深度失败案例分析

目标：
1. 查看失败案例中检索到的具体内容
2. 分析为什么expected_chunks没有在检索结果中出现
3. 给出优化建议
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

project_root = Path(__file__).parent.parent.parent

def analyze_failure_case(case: Dict) -> Dict:
    """深度分析单个失败案例"""
    query = case['query']
    expected_chunks = case['expected_chunks']
    retrieved_docs = case['retrieved_docs']

    analysis = {
        'query': query,
        'expected_chunks': expected_chunks,
        'category': case['category'],
        'retrieval_type': case['retrieval_type'],
        'issues': []
    }

    # 问题1: 检索到的文档是否相关
    retrieved_text = ' '.join(retrieved_docs).lower()

    # 问题2: expected_chunks是否出现在检索结果中
    missing_chunks = []
    for chunk in expected_chunks:
        if chunk.lower() not in retrieved_text:
            missing_chunks.append(chunk)

    if missing_chunks:
        analysis['issues'].append({
            'type': '关键词缺失',
            'detail': f"检索结果中缺失关键词: {', '.join(missing_chunks)}"
        })

    # 问题3: 图谱查询但返回向量结果
    if case['retrieval_type'] == 'GRAPH':
        # 检查是否返回了规则文档而不是图谱数据
        if any(keyword in retrieved_text for keyword in ['第', '条', '标准', '规定']):
            analysis['issues'].append({
                'type': '检索类型错误',
                'detail': '期望图谱查询（组织架构/统计数据），但返回了规则文档'
            })

    # 问题4: 检索结果重复
    unique_docs = set(retrieved_docs)
    if len(unique_docs) < len(retrieved_docs):
        analysis['issues'].append({
            'type': '结果重复',
            'detail': f'检索到{len(retrieved_docs)}个结果，但只有{len(unique_docs)}个是唯一的'
        })

    # 问题5: 检索结果质量
    if not retrieved_docs or all(len(doc.strip()) < 50 for doc in retrieved_docs):
        analysis['issues'].append({
            'type': '结果质量低',
            'detail': '检索结果为空或内容过短'
        })

    # 显示前200字符的检索结果
    analysis['retrieved_preview'] = [doc[:200] + '...' if len(doc) > 200 else doc
                                     for doc in retrieved_docs[:3]]

    return analysis


def main():
    """主函数"""
    # 设置stdout编码为utf-8
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("="*80)
    print("深度失败案例分析")
    print("="*80)

    # 加载分析结果
    results_path = project_root / 'tests' / 'evaluation' / 'recall_analysis.json'
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    vector_results = data['vector']

    # 筛选失败案例
    failed_cases = [case for case in vector_results if not case['recall_at_5']]

    print(f"\n总失败数: {len(failed_cases)}")
    print(f"{'='*80}\n")

    # 按失败原因分组
    from collections import defaultdict
    by_reason = defaultdict(list)
    for case in failed_cases:
        by_reason[case['failure_reason']].append(case)

    # 分析每种失败原因的典型案例
    for reason, cases in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{'='*80}")
        print(f"失败原因: {reason} (共{len(cases)}个)")
        print(f"{'='*80}\n")

        # 选择前3个典型案例详细分析
        for i, case in enumerate(cases[:3], 1):
            print(f"\n[案例 {i}]")
            analysis = analyze_failure_case(case)

            print(f"查询: {analysis['query']}")
            print(f"类别: {analysis['category']}")
            print(f"期望检索类型: {analysis['retrieval_type']}")
            print(f"期望关键词: {analysis['expected_chunks']}")

            print(f"\n问题诊断:")
            for issue in analysis['issues']:
                print(f"  - {issue['type']}: {issue['detail']}")

            print(f"\n检索结果预览:")
            for j, preview in enumerate(analysis['retrieved_preview'], 1):
                print(f"  [{j}] {preview}")

            print("\n" + "-"*80)

    # 总结优化建议
    print(f"\n{'='*80}")
    print("优化建议总结")
    print(f"{'='*80}\n")

    # 统计各类问题
    all_issues = defaultdict(int)
    for case in failed_cases:
        analysis = analyze_failure_case(case)
        for issue in analysis['issues']:
            all_issues[issue['type']] += 1

    print("问题分布:")
    for issue_type, count in sorted(all_issues.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {issue_type}: {count}次")

    print("\n核心优化方向:")

    # 图谱查询问题
    graph_failures = len(by_reason.get('other', []))
    if graph_failures > 15:
        print(f"\n1. 图谱检索系统 (影响{graph_failures}个查询)")
        print("   - 问题: 图谱查询（RETRIEVAL_TYPE=GRAPH）返回了向量检索结果")
        print("   - 原因: 系统没有正确路由到图谱检索器，或图谱数据不存在")
        print("   - 建议: 修复intelligent_router或实现专门的graph_retriever")

    # 多跳推理问题
    multi_hop_failures = len(by_reason.get('multi_hop', []))
    if multi_hop_failures > 0:
        print(f"\n2. 多跳推理能力 (影响{multi_hop_failures}个查询)")
        print("   - 问题: 需要多步推理或计算的查询失败")
        print("   - 原因: 单次检索无法覆盖所有必要信息")
        print("   - 建议: 实现多轮检索或使用Agent进行复杂查询分解")

    # 长尾查询问题
    long_tail_failures = len(by_reason.get('long_tail', []))
    if long_tail_failures > 0:
        print(f"\n3. 长尾查询召回 (影响{long_tail_failures}个查询)")
        print("   - 问题: 特殊条件组合（季节+地点）的查询失败")
        print("   - 原因: 训练数据中类似模式较少")
        print("   - 建议: 数据增强或微调embedding模型")

    # 实体识别问题
    entity_failures = len(by_reason.get('entity_recognition', []))
    if entity_failures > 0:
        print(f"\n4. 实体识别优化 (影响{entity_failures}个查询)")
        print("   - 问题: 地名分词错误导致召回失败")
        print("   - 原因: 通用分词器对业务实体识别不准")
        print("   - 建议: 使用命名实体识别(NER)或自定义词典")

    print(f"\n{'='*80}")


if __name__ == '__main__':
    main()
