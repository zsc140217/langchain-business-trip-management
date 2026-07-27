# 推理能力与工具使用能力评测系统

## 概述

本评测系统专注于评估RAG系统的两大核心能力：
1. **推理能力** - 简单推理和复杂推理
2. **工具使用能力** - 工具选择、参数构造、结果解读

## 目录结构

```
tests/evaluation/
├── evaluators/                    # 评估器模块
│   ├── __init__.py
│   ├── cost_tracker.py           # 成本追踪器
│   ├── llm_judge.py              # LLM-as-Judge基础模块
│   ├── reasoning_evaluator.py    # 推理能力评估器
│   └── tool_evaluator.py         # 工具使用评估器
├── test_data/                     # 测试数据
│   ├── reasoning_simple.json     # 简单推理测试(10条)
│   ├── reasoning_complex.json    # 复杂推理测试(8条)
│   └── tool_usage.json           # 工具使用测试(12条)
├── reports/                       # 评测报告
│   └── comprehensive/
└── run_reasoning_tool_evaluation.py  # 统一评测入口
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 运行评测

```bash
cd tests/evaluation
python run_reasoning_tool_evaluation.py
```

### 3. 查看报告

报告保存在 `reports/comprehensive/` 目录下：
- `reasoning_tool_evaluation_YYYYMMDD_HHMMSS.md` - Markdown格式报告
- `cost_details_YYYYMMDD_HHMMSS.json` - 成本详细记录

## 测试数据说明

### reasoning_simple.json (10条)

简单推理测试用例，1-2步推理：

```json
{
  "id": "reasoning_simple_001",
  "query": "我是L5员工，出差上海住宿标准是多少？",
  "expected_reasoning": "L5→高级经理→省外标准500元/天",
  "expected_answer": "500元/天",
  "expected_keywords": ["500", "元/天"],
  "difficulty": "SIMPLE",
  "category": "职级标准查询"
}
```

### reasoning_complex.json (8条)

复杂推理测试用例，4-9步推理：

```json
{
  "id": "reasoning_complex_001",
  "query": "张三去北京出差3天，住宿500元/天，餐补100元/天，交通费800元，总共能报多少？",
  "expected_reasoning": "步骤1: 住宿=500×3...",
  "expected_numbers": ["1500", "300", "800", "2600"],
  "reasoning_steps": 4,
  "requires_tool": false
}
```

### tool_usage.json (12条)

工具使用测试用例，分3类：

**工具选择 (4条)**:
```json
{
  "id": "tool_selection_001",
  "query": "销售部有多少人？",
  "expected_tool": "GraphRetriever",
  "test_type": "tool_selection"
}
```

**工具参数 (4条)**:
```json
{
  "id": "tool_parameters_001",
  "query": "查询销售部经理李明的出差记录",
  "key_parameters": ["李明", "出差"],
  "test_type": "tool_parameters"
}
```

**工具解读 (4条)**:
```json
{
  "id": "tool_interpretation_001",
  "query": "销售部有多少人？",
  "mock_tool_result": {...},
  "expected_answer": "销售部有3人",
  "test_type": "tool_interpretation"
}
```

## 评估方法

### 混合评估策略

- **代码规则评估 (30%)**: 关键词匹配、数字提取、工具选择验证
- **LLM-as-Judge评估 (70%)**: 推理路径、逻辑完整性、语义理解

### 评分标准 (1-5分)

- **5分**: 完全正确
- **4分**: 正确但有小瑕疵
- **3分**: 部分正确(及格线)
- **2分**: 有严重错误
- **1分**: 完全错误

### Bad Case自动标注

系统会自动标记需要人工review的case：
- `overall_score < 3`
- `reasoning_score < 2`
- 缺失关键词

## 成本追踪

系统自动记录每次LLM调用的成本：

```python
# 成本追踪器会记录
- 模型名称
- Token消耗(输入/输出)
- 成本(人民币)
- 评估目的(simple_reasoning/complex_reasoning/tool_interpretation)
```

## 扩展开发

### 添加新的测试用例

编辑对应的JSON文件即可：
```bash
tests/evaluation/test_data/reasoning_simple.json
```

### 添加新的评估维度

1. 在 `evaluators/` 创建新评估器
2. 继承基础类并实现 `evaluate()` 方法
3. 在主程序中调用

### 集成实际系统API

修改 `_collect_system_responses()` 方法：

```python
async def _collect_system_responses(self, test_data_path: Path):
    import requests
    
    responses = []
    for test_case in test_cases:
        # 调用实际API
        response = requests.post(
            'http://localhost:8000/api/query',
            json={'question': test_case['query']}
        )
        
        responses.append({
            'test_id': test_case['id'],
            'answer': response.json()['answer'],
            'latency_ms': response.elapsed.total_seconds() * 1000,
            'tool_calls': response.json().get('tool_calls', [])
        })
    
    return responses
```

## 面试准备

这个评测系统展示了以下技术能力：

1. **架构设计**: 五层架构，职责清晰，易扩展
2. **评估策略**: 混合评估(规则30% + LLM 70%)
3. **成本意识**: 完整的成本追踪和分析
4. **工程实践**: 模块化、可测试、易维护
5. **问题解决**: LLM评分稳定性、复杂推理验证、工具参数灵活性

## 常见问题

**Q: 为什么要用混合评估？**
A: 代码规则快速确定，LLM灵活语义理解，两者互补。

**Q: 如何保证LLM评分稳定？**
A: Temperature=0.1 + 结构化Prompt + 强制JSON输出

**Q: 成本大概多少？**
A: 使用qwen-max，单用例约¥0.05-0.15(取决于复杂度)

**Q: 可以用其他LLM吗？**
A: 可以，修改 `llm_judge.py` 中的API调用即可

## 作者

评测系统设计与实现 - 2026-07-26
