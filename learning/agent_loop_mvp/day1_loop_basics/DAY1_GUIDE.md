# Day 1: 基础Loop Agent + 状态管理

> 学习目标：理解StateGraph核心机制，搭建第一个Loop Agent  
> 时间：6小时（上午3h + 下午3h）  
> 日期：2026-06-21

---

## 🎯 今日目标

**上午**：搭建LangGraph基础架构，实现简单的retrieve → answer流程  
**下午**：集成现有RAG资产（Query Rewriter + Hybrid Retriever）

---

## 📚 上午任务（3小时）

### Task 1: 理解StateGraph基础（30分钟）

**阅读材料**：
- `LANGGRAPH_DEEP_DIVE.md`
- `src/modules/module_4_multi_agent/state_graph.py`

**关键概念**：
1. TypedDict状态定义：所有节点共享的数据结构
2. 节点函数：接收state，返回state更新
3. 边：定义执行顺序

**快速检查**：
- [ ] 理解StateGraph是什么
- [ ] 理解状态如何传递
- [ ] 理解`Annotated[List, operator.add]`作用

---

### Task 2: 定义共享状态（30分钟）

**创建文件**：`src/modules/module_5_langgraph/state.py`

```python
"""共享状态定义"""
from typing import TypedDict, Annotated, List, Optional
import operator

class TravelAgentState(TypedDict):
    query: str
    messages: Annotated[List[str], operator.add]  # 自动累积
    rewritten_query: Optional[str]
    rag_results: List[str]
    current_step: str
    iteration: int
    final_answer: str
```

---

### Task 3: 实现第一个简单Agent（1小时）

**创建文件**：`src/modules/module_5_langgraph/simple_agent.py`

**完整代码见文件末尾**

**运行测试**：
```bash
cd src/modules/module_5_langgraph
python simple_agent.py
```

---

### Task 4: 可视化理解（30分钟）

**流程图**：
```
START → retrieve → answer → END
```

**状态流动**：
- 初始：`{"query": "...", "messages": []}`
- retrieve后：`{"messages": ["[检索]..."], "rag_results": [...]}`
- answer后：`{"messages": ["[检索]...", "[回答]..."], "final_answer": "..."}`

---

## 📚 下午任务（3小时）

### Task 5: 集成Query Rewriter（1小时）

**修改simple_agent.py**：
1. 导入`SimpleQueryRewriter`
2. 添加`query_rewrite_node`
3. 修改图结构：`query_rewrite → retrieve → answer`

---

### Task 6: 集成真实RAG（1.5小时）

**替换模拟检索**：
1. 加载向量库
2. 使用真实retriever
3. 集成DeepSeek LLM

---

### Task 7: 端到端测试（30分钟）

**测试多个查询**：
- "上海出差住宿标准是多少"
- "去北京出差可以坐商务舱吗"
- "三线城市差旅补助多少钱"

---

## 📝 学习笔记

**创建文件**：`learning/agent_loop_mvp/day1_loop_basics/notes.md`

**核心概念（30秒）**：
Agent Loop通过StateGraph实现：定义共享状态 → 添加节点函数 → 添加边定义顺序 → 编译执行。状态自动传递，`Annotated[List, operator.add]`实现自动累积。

**遇到的坑**：
- 忘记`operator.add`导致列表被替换
- 节点返回字典只需包含更新字段

---

## ✅ 今日完成检查

- [ ] StateGraph基础概念理解
- [ ] 共享状态定义完成
- [ ] 简单Agent可运行
- [ ] Query Rewriter集成
- [ ] 真实RAG集成
- [ ] 端到端测试通过
- [ ] 学习笔记完成

**完成后继续Day 2：条件分支 + ReAct循环**
