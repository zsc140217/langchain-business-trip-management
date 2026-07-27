# 评估测试用例说明

本目录包含用于评估差旅管理系统各个模块的测试用例集。

## 文件结构

```
test_cases/
├── rag_test_cases.json           # RAG检索质量测试用例（50条）
├── routing_test_cases.json       # 智能路由测试用例（30条）
├── approval_test_cases.json      # 审批引擎测试用例（20条）
└── README.md                      # 本说明文档
```

## 1. RAG测试用例 (rag_test_cases.json)

### 用途
评估RAG检索系统的准确性和召回率，确保能够正确检索到相关的政策文档片段。

### 数据结构
```json
{
  "id": "RAG_001",
  "category": "policy_query",
  "query": "用户查询内容",
  "expected_chunks": ["预期检索到的文档片段ID"],
  "ground_truth_answer": "标准答案",
  "difficulty": "easy|medium|hard"
}
```

### 测试类别
- **policy_query**: 政策查询类（标准明确）
- **procedure_query**: 流程查询类（步骤清晰）
- **complex_scenario**: 复杂场景类（多条件组合）
- **exception_handling**: 异常处理类（特殊情况）
- **time_constraint**: 时间约束类
- **approval_flow**: 审批流程类
- **international_travel**: 国际出差类
- **meal_allowance**: 餐费补贴类
- **group_travel**: 团队出差类
- 等等...

### 难度级别
- **easy**: 单一条件，直接匹配（10条）
- **medium**: 2-3个条件，需要推理（20条）
- **hard**: 多条件组合，需要深度理解（20条）

### 评估指标
- **Precision**: 检索结果的准确率
- **Recall**: 相关文档的召回率
- **F1 Score**: 准确率和召回率的调和平均
- **MRR**: 平均倒数排名
- **NDCG**: 归一化折损累计增益

### 使用方法
```python
from tests.evaluation.rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator()
results = evaluator.run_evaluation("test_cases/rag_test_cases.json")
print(f"Precision: {results['precision']:.2%}")
print(f"Recall: {results['recall']:.2%}")
```

---

## 2. 路由测试用例 (routing_test_cases.json)

### 用途
评估智能路由系统是否能正确识别用户意图并选择合适的执行引擎。

### 数据结构
```json
{
  "id": "ROUTE_001",
  "query": "用户查询内容",
  "expected_intent": "simple_query|complex_analysis|multi_step",
  "expected_engine": "ReAct|Planning|ComplexTask",
  "reasoning": "选择该引擎的原因",
  "confidence_threshold": "high|medium|low"
}
```

### 意图类型
- **simple_query**: 简单查询 → 使用 ReAct 引擎
- **complex_analysis**: 复杂分析 → 使用 Planning 引擎
- **multi_step**: 多步骤任务 → 使用 ComplexTask 引擎

### 评估指标
- **Accuracy**: 路由决策的准确率
- **Precision**: 各引擎选择的精确度
- **Recall**: 各引擎的召回率
- **F1 Score**: 综合评分

### 使用方法
```python
from tests.evaluation.routing_evaluator import RoutingEvaluator

evaluator = RoutingEvaluator()
results = evaluator.run_evaluation("test_cases/routing_test_cases.json")
print(f"Routing Accuracy: {results['accuracy']:.2%}")
```

---

## 3. 审批测试用例 (approval_test_cases.json)

### 用途
评估审批引擎的规则匹配准确性和决策一致性。

### 数据结构
```json
{
  "id": "APPROVAL_001",
  "input": {
    "user_level": "staff|manager|director|vp",
    "destination": "目的地城市",
    "duration": 出差天数,
    "estimated_cost": 预估费用,
    "over_budget_ratio": 超预算比例（可选）
  },
  "expected_approval_level": "auto|manager|director|vp|cfo",
  "rules_triggered": ["触发的规则列表"],
  "explanation": "决策说明"
}
```

### 审批级别
- **auto**: 自动通过
- **manager**: 经理审批
- **director**: 总监审批
- **vp**: VP审批
- **cfo**: CFO审批

### 评估指标
- **Accuracy**: 审批级别判断的准确率
- **Consistency**: 相同条件下的决策一致性
- **Rule Coverage**: 规则覆盖率

### 使用方法
```python
from tests.evaluation.approval_evaluator import ApprovalEvaluator

evaluator = ApprovalEvaluator()
results = evaluator.run_evaluation("test_cases/approval_test_cases.json")
print(f"Approval Accuracy: {results['accuracy']:.2%}")
```

---

## 测试用例扩展指南

当前提供的测试用例包含：
- **RAG**: 前10条为详细用例，后40条为模板（需根据实际业务填充）
- **Routing**: 前5条为详细用例，后25条为模板
- **Approval**: 前5条为详细用例，后15条为模板

### 如何扩展测试用例

1. **基于真实用户查询**
   - 从系统日志中提取真实用户查询
   - 标注正确答案和预期行为
   - 添加到对应的JSON文件

2. **覆盖边界情况**
   - 超长查询
   - 含糊不清的查询
   - 多意图混合查询
   - 包含错误信息的查询

3. **负面测试用例**
   - 恶意查询
   - 无效输入
   - 系统无法处理的查询

4. **回归测试用例**
   - 从bug报告中提取
   - 确保修复后的问题不再复现

### 用例质量标准

✓ **明确的预期输出**: 每个用例都有清晰的正确答案  
✓ **可验证性**: 能够自动化验证结果  
✓ **独立性**: 用例之间互不依赖  
✓ **覆盖性**: 覆盖主要业务场景和边界情况  
✓ **可维护性**: 业务变更时易于更新  

---

## 批量测试运行

运行所有评估测试：

```bash
# 运行所有评估
python tests/evaluation/run_all_evaluations.py

# 只运行RAG评估
python tests/evaluation/rag_evaluator.py

# 只运行路由评估
python tests/evaluation/routing_evaluator.py

# 只运行审批评估
python tests/evaluation/approval_evaluator.py
```

---

## 评估报告

评估结果将保存在 `tests/evaluation/reports/` 目录：

```
reports/
├── rag_evaluation_report_20260725.json
├── routing_evaluation_report_20260725.json
└── approval_evaluation_report_20260725.json
```

每份报告包含：
- 总体指标
- 分类别指标
- 错误案例分析
- 改进建议

---

## 持续改进

1. **定期更新**: 每月至少更新一次测试用例
2. **监控指标**: 设置阈值告警（如准确率<90%）
3. **A/B测试**: 对比不同版本的性能差异
4. **用户反馈**: 将用户反馈转化为测试用例

---

## 注意事项

⚠️ **模板数据**: 部分用例使用了模板数据，请根据实际业务场景完善  
⚠️ **数据隐私**: 不要在测试用例中包含真实的个人信息  
⚠️ **版本管理**: 测试用例变更需要版本控制和变更说明  
⚠️ **定期审查**: 每季度审查测试用例的有效性和覆盖率  

---

## 联系方式

如有问题或建议，请联系：
- 项目负责人: [填写联系方式]
- 技术支持: [填写联系方式]
