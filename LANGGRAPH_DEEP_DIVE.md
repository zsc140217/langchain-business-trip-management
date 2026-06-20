# LangGraph 深度讲解 - 状态管理与Multi-Agent路由

> 详解LangGraph的四大核心能力和实际应用

本文档已因成本考虑简化。关键要点：

## 1. 复杂状态管理

**核心**：TypedDict定义共享状态，在所有Agent之间传递

```python
class AgentState(TypedDict):
    query: str
    results: Dict[str, Any]  # 累积各Agent结果
    messages: Annotated[List, operator.add]  # 自动追加
```

**代码位置**：`src/modules/module_4_multi_agent/state_graph.py:31-54`

## 2. 条件分支（Conditional Edges）

**实现if-else逻辑**：

```python
workflow.add_conditional_edges(
    "supervisor",
    decide_next,  # 决策函数
    {
        "weather_worker": "weather_worker",
        "policy_worker": "policy_worker",
        "END": END
    }
)
```

**代码位置**：`state_graph.py:132-147`

## 3. 人工审批（Human-in-the-loop）

**中断执行，等待人工输入**：

```python
workflow.add_node("approval", approval_node, interrupt_before=True)

# 执行到approval会暂停
result = app.invoke(input_state, config)

# 人工审批后继续
app.invoke(None, config)
```

## 4. 状态持久化（Checkpointing）

**保存状态到数据库**：

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = workflow.compile(checkpointer=checkpointer)

# 每个节点执行后自动保存检查点
# 崩溃后可从检查点恢复
```

## 5. Multi-Agent路由机制

**Supervisor-Worker模式**：

1. **识别需求**：关键词匹配识别需要哪些Worker
2. **优先级路由**：weather → policy → itinerary
3. **任务完成判断**：所有需要的Worker都执行完
4. **结果整合**：LLM综合所有Worker结果

**代码位置**：`src/modules/module_4_multi_agent/supervisor.py`

---

**运行示例**：
```bash
cd src/modules/module_4_multi_agent
python example.py
```

详细内容请参考：
- [LangChain生态指南](LANGCHAIN_ECOSYSTEM_GUIDE.md)
- [交互式学习路径](INTERACTIVE_LEARNING.md)
