# 评测系统集成指南

## 系统已就绪

评测系统已完成部署，Mock数据已移除，现在会调用实际业务API。

## API要求

评测系统会调用以下API：

**端点**: `http://localhost:8000/api/query`

**请求格式**:
```json
{
  "question": "我是L5员工，出差上海住宿标准是多少？"
}
```

**响应格式**:
```json
{
  "answer": "L5员工出差上海的住宿标准是500元/天",
  "tool_calls": [
    {
      "tool_name": "VectorRetriever",
      "parameters": {"query": "L5 住宿标准"}
    }
  ],
  "retrieved_docs": ["政策文档1", "政策文档2"]
}
```

## 运行评测

### 1. 启动业务系统
```bash
# 确保业务系统运行在 http://localhost:8000
python src/main.py
```

### 2. 运行评测
```bash
cd tests/evaluation
python run_reasoning_tool_evaluation.py
```

### 3. 查看报告
报告保存在：
```
reports/comprehensive/reasoning_tool_evaluation_YYYYMMDD_HHMMSS.md
```

## 评测流程

```
[Phase 1/4] 简单推理能力评估 (10条)
    [1/10] 测试: reasoning_simple_001
    [2/10] 测试: reasoning_simple_002
    ...

[Phase 2/4] 复杂推理能力评估 (8条)
    [1/8] 测试: reasoning_complex_001
    ...

[Phase 3/4] 工具使用能力评估 (12条)
    [1/12] 测试: tool_selection_001
    ...

[Phase 4/4] 生成综合报告
```

## 测试覆盖

- **简单推理** (10条): 职级标准查询、组织架构查询、地域判断、政策查询
- **复杂推理** (8条): 多步计算、费用核算、标准校验
- **工具使用** (12条): 工具选择4条 + 参数构造4条 + 结果解读4条

## 错误处理

如果业务系统未启动，会显示：
```
错误: 无法连接到业务系统API (http://localhost:8000/api/query)
请确保业务系统正在运行
```

评测会继续执行，但该用例会标记为失败。

## 预期结果

真实系统运行后，预期评测结果：
- **简单推理**: 平均分 4.0-4.5/5，通过率 80%+
- **复杂推理**: 平均分 3.5-4.0/5，通过率 70%+
- **工具使用**: 平均分 4.0-4.5/5，通过率 75%+

## 成本预估

- 单次完整评测：约 CNY 0.5-0.8
- 单用例成本：约 CNY 0.02
- 总Token消耗：约 8,000-12,000 tokens

## 下一步

评测系统已完全就绪，可以：
1. 启动业务系统
2. 运行评测
3. 根据报告优化系统
4. 用于面试展示

---

**状态**: ✅ Ready for Production
