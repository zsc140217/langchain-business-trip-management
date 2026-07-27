"""
快速路由评估脚本
基于recall_analysis.json数据，评估路由系统的准确性

评估维度：
1. 查询类型识别（规则查询 vs 业务查询）
2. 路由决策准确性
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("路由评估系统 - 快速版")
print("=" * 60)

# 加载测试数据
data_file = "tests/evaluation/recall_analysis.json"
print(f"\n加载数据: {data_file}")

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

test_cases = data['vector']
print(f"测试用例数: {len(test_cases)}")

# 定义查询类型规则（基于category字段）
def classify_query_type(category: str) -> str:
    """
    根据category分类查询类型
    规则查询: 查询政策、标准、规定
    业务查询: 查询员工、出差次数、统计数据
    """
    if category.startswith("规则-"):
        return "规则查询"
    elif category.startswith("业务-"):
        return "业务查询"
    else:
        return "未知"


def expected_retrieval_method(query_type: str) -> str:
    """
    期望的检索方法
    规则查询 -> RAG检索（向量检索政策文档）
    业务查询 -> GRAPH检索（知识图谱查询员工/出差数据）
    """
    if query_type == "规则查询":
        return "RAG"
    elif query_type == "业务查询":
        return "GRAPH"  # 修改：业务查询使用知识图谱
    else:
        return "UNKNOWN"


def actual_retrieval_method(test_case: Dict[str, Any]) -> str:
    """
    实际使用的检索方法（通过retrieval_type字段判断）
    """
    retrieval_type = test_case.get('retrieval_type', 'UNKNOWN')
    if retrieval_type == 'VECTOR':
        return "RAG"
    elif retrieval_type == 'DATABASE':
        return "DATABASE"
    else:
        return retrieval_type


# 评估路由准确性
print("\n" + "=" * 60)
print("开始评估...")
print("=" * 60)

results = []
correct_routing = 0
incorrect_routing = 0

for case in test_cases:
    case_id = case['id']
    query = case['query']
    category = case['category']

    # 分类
    query_type = classify_query_type(category)
    expected_method = expected_retrieval_method(query_type)
    actual_method = actual_retrieval_method(case)

    # 判断准确性
    is_correct = (expected_method == actual_method)

    if is_correct:
        correct_routing += 1
    else:
        incorrect_routing += 1

    results.append({
        'case_id': case_id,
        'query': query,
        'category': category,
        'query_type': query_type,
        'expected_method': expected_method,
        'actual_method': actual_method,
        'is_correct': is_correct
    })

# 计算统计数据
total = len(results)
accuracy = (correct_routing / total * 100) if total > 0 else 0

# 按查询类型统计
by_query_type = {}
for result in results:
    qtype = result['query_type']
    if qtype not in by_query_type:
        by_query_type[qtype] = {'correct': 0, 'total': 0}

    by_query_type[qtype]['total'] += 1
    if result['is_correct']:
        by_query_type[qtype]['correct'] += 1

# 打印结果
print("\n" + "=" * 60)
print("评估结果")
print("=" * 60)

print(f"\n总测试用例数: {total}")
print(f"路由正确数: {correct_routing}")
print(f"路由错误数: {incorrect_routing}")
print(f"整体准确率: {accuracy:.1f}%")

print("\n" + "-" * 60)
print("按查询类型统计")
print("-" * 60)

for qtype, stats in by_query_type.items():
    correct = stats['correct']
    total_count = stats['total']
    acc = (correct / total_count * 100) if total_count > 0 else 0
    print(f"\n{qtype}:")
    print(f"  正确: {correct}/{total_count}")
    print(f"  准确率: {acc:.1f}%")

# 显示错误案例
print("\n" + "-" * 60)
print("路由错误的案例")
print("-" * 60)

error_cases = [r for r in results if not r['is_correct']]
if error_cases:
    for i, case in enumerate(error_cases[:10], 1):  # 只显示前10个
        print(f"\n错误案例 {i}:")
        print(f"  ID: {case['case_id']}")
        print(f"  查询: {case['query']}")
        print(f"  类别: {case['category']}")
        print(f"  查询类型: {case['query_type']}")
        print(f"  期望路由: {case['expected_method']}")
        print(f"  实际路由: {case['actual_method']}")

    if len(error_cases) > 10:
        print(f"\n... 还有 {len(error_cases) - 10} 个错误案例（详见报告）")
else:
    print("\n无路由错误！")

# 生成Markdown报告
output_dir = Path("tests/evaluation/reports/routing")
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = output_dir / f"routing_evaluation_{timestamp}.md"

report = f"""# 路由系统评估报告

**评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**测试数据**: recall_analysis.json ({total}条)
**评估方法**: 基于category字段的规则分类

---

## 整体统计

| 指标 | 数值 |
|------|------|
| 总测试用例数 | {total} |
| 路由正确数 | {correct_routing} |
| 路由错误数 | {incorrect_routing} |
| **整体准确率** | **{accuracy:.1f}%** |

---

## 按查询类型统计

| 查询类型 | 正确数 | 总数 | 准确率 |
|----------|--------|------|--------|
"""

for qtype, stats in by_query_type.items():
    correct = stats['correct']
    total_count = stats['total']
    acc = (correct / total_count * 100) if total_count > 0 else 0
    report += f"| {qtype} | {correct} | {total_count} | {acc:.1f}% |\n"

report += """
---

## 路由错误案例

"""

if error_cases:
    for i, case in enumerate(error_cases, 1):
        report += f"""
### 错误案例 {i}

- **ID**: {case['case_id']}
- **查询**: {case['query']}
- **类别**: {case['category']}
- **查询类型**: {case['query_type']}
- **期望路由**: {case['expected_method']}
- **实际路由**: {case['actual_method']}

**问题分析**:
"""
        if case['query_type'] == "业务查询" and case['actual_method'] == "RAG":
            report += "业务查询错误地使用了RAG检索，应该直接查询数据库。\n"
        elif case['query_type'] == "规则查询" and case['actual_method'] == "DATABASE":
            report += "规则查询错误地查询了数据库，应该使用RAG检索政策文档。\n"

        report += "\n---\n"
else:
    report += "\n无路由错误！所有查询都被正确路由。\n"

report += """
---

## 结论

"""

if accuracy >= 90:
    report += "✅ 路由系统表现优秀，准确率在90%以上。\n"
elif accuracy >= 70:
    report += "⚠️ 路由系统表现良好，但仍有改进空间。\n"
else:
    report += "❌ 路由系统存在严重问题，需要优化。\n"

rule_query_acc = (by_query_type.get('规则查询', {}).get('correct', 0) / by_query_type.get('规则查询', {}).get('total', 1) * 100)
business_query_acc = (by_query_type.get('业务查询', {}).get('correct', 0) / by_query_type.get('业务查询', {}).get('total', 1) * 100)

report += f"""
### 主要发现

1. **整体准确率**: {accuracy:.1f}%
2. **规则查询准确率**: {rule_query_acc:.1f}%
3. **业务查询准确率**: {business_query_acc:.1f}%

### 改进建议

"""

if incorrect_routing > 0:
    report += """
1. **增强查询类型识别** — 添加关键词匹配规则（"有几次"、"统计"、"员工"等关键词识别业务查询）
2. **优化路由决策逻辑** — 明确区分规则查询和业务查询的路由规则
3. **添加路由日志** — 记录每次路由决策的依据，便于调试
4. **引入意图分类器** — 使用LLM或规则引擎自动判断查询意图
"""
else:
    report += "\n当前路由系统工作正常，暂无需改进。\n"

# 保存报告
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n报告已保存: {report_file}")
print("\n" + "=" * 60)
print("评估完成！")
print("=" * 60)
