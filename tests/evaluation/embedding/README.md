# Embedding评估系统

## 概述

完整的Embedding模型评估系统，对比 DashScope API vs 微调本地模型的性能差异。

## 文件结构

```
tests/evaluation/embedding/
├── metrics.py              # 8个核心评估指标
├── evaluator.py            # 评估器（DashScope + 微调模型）
├── comparator.py           # 对比分析器
├── test_generator.py       # 测试集生成（17查询+10文档）
├── html_report.py          # HTML报告生成器
├── report_template.html    # HTML报告模板
├── run_eval.py             # 主执行脚本
└── embedding_evaluation_report.html  # 生成的评估报告
```

## 快速开始

```bash
# 1. 配置API密钥（.env文件）
DASHSCOPE_API_KEY=your_key

# 2. 运行评估
python tests/evaluation/embedding/run_eval.py

# 3. 查看HTML报告
# 浏览器打开: tests/evaluation/embedding/embedding_evaluation_report.html
```

## 评估结果（实际数据）

| 指标 | DashScope API | 微调模型 | 提升 |
|------|--------------|---------|------|
| Recall@5 | 88.24% | 94.12% | +6.67% |
| NDCG@5 | 0.8824 | 0.9412 | +6.67% |
| MRR | 0.8457 | 0.8921 | +5.49% |
| 延迟 | 8.16s | 4.61s | -43.5% |
| 成本 | ¥500/月 | ¥0 | -100% |

## 面试记忆要点

### 必背数字
- Recall@5提升: +6.7%
- 延迟降低: 43.5%
- 成本节省: 100%

### 30秒话术
> 我们的RAG系统最初使用DashScope的通用embedding，Recall@5只有88.2%。
> 我基于BGE-large-zh进行领域微调，用MNR Loss训练200组样本，
> Recall@5提升到94.1%（+6.7%），延迟从8s降到5s，完全零成本。

### 技术栈
- 基座模型: BGE-large-zh-v1.5
- 训练方法: MNR Loss
- 数据策略: Hard Negatives
- 评估指标: Recall@5, NDCG@5, MRR

## 测试集设计

### 文档库（10个）
- D01-D03: 住宿标准（一线/二线/三线）
- D04-D05: 交通费用
- D06-D10: 审批流程、发票等

### 查询集（17个）
- Easy (4个): 直接关键词匹配
- Medium (7个): 同义词/语序变化
- Hard (5个): 隐式推理
- Distractor (1个): 不在文档中

## 评估指标说明

- **Recall@K**: 在Top-K中找到相关文档的比例
- **NDCG@K**: 考虑排序位置的检索质量
- **MRR**: 第一个相关文档排名的倒数均值

## 更新日志

### 2026-06-22
- 实现完整评估系统（7个文件）
- 首次运行评估，生成HTML报告
- Recall@5: 88.24% → 94.12% (+6.67%)
- 延迟: 8.16s → 4.61s (-43.5%)
