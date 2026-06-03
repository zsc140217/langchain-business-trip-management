# 第二章：架构模式对比

> **学习目标**：掌握 RAG、Agent、Multi-Agent、Chain、Memory 五大架构模式的选型决策

---

## 📚 必背知识点

### 五大架构模式（面试必问）
1. **RAG** - 检索增强生成（6种模式）
2. **Agent** - 智能体（5种模式）
3. **Multi-Agent** - 多智能体协作（7种模式）
4. **Chain** - 链式组合（5种模式）
5. **Memory** - 记忆系统（5种模式）

### 记忆口诀
> "RAG 检索知识库，Agent 自主做决策，Multi 协作分任务，Chain 组合成流水，Memory 记住上下文"

---

## 1. RAG 架构模式

### 1.1 六种 RAG 模式对比（必背）

| 模式 | 复杂度 | 准确率 | 延迟 | 成本 | 适用场景 |
|------|--------|--------|------|------|---------|
| **Simple RAG** | ⭐ | 60% | 低 | 低 | 简单问答 |
| **Advanced RAG** | ⭐⭐⭐ | 80% | 中 | 中 | 生产应用 |
| **Agentic RAG** | ⭐⭐⭐⭐ | 85% | 高 | 高 | 复杂查询 |
| **Graph RAG** | ⭐⭐⭐⭐⭐ | 90% | 高 | 高 | 知识图谱 |
| **Self-RAG** | ⭐⭐⭐⭐ | 88% | 高 | 高 | 自我修正 |
| **Corrective RAG** | ⭐⭐⭐ | 82% | 中 | 中 | 纠错场景 |

### 1.2 Simple RAG（基础必会）

**流程**：
```
用户查询 → 向量检索 → 拼接上下文 → LLM 生成
```

**代码示例**：
```python
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

**优点**：
- ✅ 实现简单（<50行代码）
- ✅ 延迟低（<1s）
- ✅ 成本低

**缺点**：
- ❌ 准确率低（60%）
- ❌ 无法处理复杂查询
- ❌ 检索质量依赖查询质量

**💡 记忆要点**：Simple RAG = 检索 + 拼接 + 生成，适合原型验证

### 1.3 Advanced RAG（生产推荐）⭐⭐⭐

**核心技术**：
1. **Query Rewriting** - 查询重写
2. **Hybrid Search** - 混合检索（BM25 + Dense）
3. **Reranking** - 重排序
4. **Multi-Query** - 多查询生成

**流程**：
```
用户查询 
  → Query Rewriting（标准化）
  → Hybrid Search（BM25 + Dense + Rewritten）
  → RRF Fusion（融合排序）
  → Reranking（重排序）
  → LLM 生成
```

**准确率提升**：
- Simple RAG: 60%
- + Query Rewriting: 70% (+10%)
- + Hybrid Search: 80% (+10%)
- + Reranking: 85% (+5%)

**💡 记忆要点**：Advanced RAG = 查询优化 + 混合检索 + 重排序，准确率 80%+

### 1.4 Agentic RAG（智能决策）

**核心思想**：Agent 决定何时检索、检索什么、如何使用

**流程**：
```
用户查询
  → Agent 分析（需要检索吗？）
  → 决策：直接回答 OR 检索
  → 如果检索：选择检索策略
  → 评估检索结果（足够吗？）
  → 决策：生成答案 OR 继续检索
```

**优点**：
- ✅ 智能决策（不是所有查询都需要检索）
- ✅ 多轮检索（不够就继续）
- ✅ 准确率高（85%）

**缺点**：
- ❌ 延迟高（多次 LLM 调用）
- ❌ 成本高（每次决策都调用 LLM）
- ❌ 复杂度高

**💡 记忆要点**：Agentic RAG = Agent 控制检索流程，适合复杂查询

---

## 2. Agent 架构模式

### 2.1 五种 Agent 模式对比（必背）

| 模式 | 推理方式 | Token 效率 | 可靠性 | 适用场景 |
|------|---------|-----------|--------|---------|
| **ReAct** | 交替推理+行动 | 中 | 高 | 通用工具调用 |
| **Plan-and-Execute** | 先规划后执行 | 低 | 中 | 复杂多步任务 |
| **ReWOO** | 推理无观察 | 高 | 中 | 并行工具调用 |
| **Reflexion** | 自我反思 | 低 | 高 | 需要自我修正 |
| **OpenAI Functions** | 函数调用 | 高 | 高 | OpenAI 模型 |

### 2.2 ReAct（最常用）⭐⭐⭐

**核心思想**：Reasoning（推理）+ Acting（行动）交替进行

**流程**：
```
Thought: 我需要查询天气
Action: weather_tool("北京")
Observation: 北京今天晴天，25°C
Thought: 我已经得到天气信息
Action: Finish
Answer: 北京今天晴天，温度25°C
```

**代码示例**：
```python
from langchain.agents import create_react_agent

agent = create_react_agent(
    llm=model,
    tools=[weather_tool, calculator_tool],
    prompt=react_prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools)
result = agent_executor.invoke({"input": "北京天气如何？"})
```

**优点**：
- ✅ 可解释性强（每步都有推理）
- ✅ 可靠性高（逐步验证）
- ✅ 通用性强（适合大多数场景）

**缺点**：
- ❌ Token 消耗中等（每步都要推理）
- ❌ 延迟较高（串行执行）

**💡 记忆要点**：ReAct = 想一步做一步，最常用的 Agent 模式

### 2.3 Plan-and-Execute（复杂任务）

**核心思想**：先制定完整计划，再逐步执行

**流程**：
```
Planning Phase:
  用户：帮我规划北京3天旅游
  Agent: 生成计划
    1. 查询北京天气
    2. 推荐景点
    3. 预订酒店
    4. 规划路线

Execution Phase:
  执行步骤1 → 执行步骤2 → 执行步骤3 → 执行步骤4
```

**优点**：
- ✅ 适合复杂多步任务
- ✅ 计划可预览和修改
- ✅ 并行执行可能性

**缺点**：
- ❌ Token 消耗高（生成完整计划）
- ❌ 灵活性低（计划固定）
- ❌ 错误传播（前面错了后面全错）

**💡 记忆要点**：Plan-and-Execute = 先规划后执行，适合复杂任务

---

## 3. Multi-Agent 架构模式

### 3.1 七种协作模式对比（必背）

| 模式 | 协调方式 | 复杂度 | 扩展性 | 适用场景 |
|------|---------|--------|--------|---------|
| **Supervisor-Worker** | 中心化 | ⭐⭐ | 高 | 任务分发 |
| **Sequential** | 流水线 | ⭐ | 中 | 线性流程 |
| **Parallel** | 并行 | ⭐⭐ | 高 | 独立任务 |
| **Dynamic Routing** | 动态选择 | ⭐⭐⭐ | 高 | 复杂路由 |
| **Debate** | 辩论共识 | ⭐⭐⭐⭐ | 低 | 决策场景 |
| **Swarm** | 去中心化 | ⭐⭐⭐⭐⭐ | 高 | 探索场景 |
| **Graph Workflow** | 图编排 | ⭐⭐⭐ | 高 | 复杂依赖 |

### 3.2 Supervisor-Worker（最常用）⭐⭐⭐

**架构**：
```
        Supervisor（监督者）
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 Worker1   Worker2   Worker3
（政策）   （天气）   （酒店）
```

**流程**：
```python
# LangGraph 实现
workflow = StateGraph(State)

# 添加节点
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("policy_agent", policy_agent_node)
workflow.add_node("weather_agent", weather_agent_node)

# Supervisor 动态路由
workflow.add_conditional_edges(
    "supervisor",
    route_to_worker,
    {
        "policy": "policy_agent",
        "weather": "weather_agent",
        "end": END
    }
)
```

**优点**：
- ✅ 清晰的职责分工
- ✅ 易于扩展（添加新 Worker）
- ✅ 中心化控制（易于调试）

**缺点**：
- ❌ Supervisor 是瓶颈
- ❌ 单点故障风险

**💡 记忆要点**：Supervisor-Worker = 一个管理者 + 多个执行者，最常用

### 3.3 Sequential Pipeline（流水线）

**架构**：
```
Agent1 → Agent2 → Agent3 → Agent4
（研究） （写作） （编辑） （发布）
```

**特点**：
- 每个 Agent 的输出是下一个的输入
- 适合内容生成流水线
- 简单但不灵活

**💡 记忆要点**：Sequential = 流水线，适合线性流程

---

## 4. Chain 架构模式

### 4.1 五种 Chain 模式（必背）

| 模式 | 用途 | LCEL 实现 | 适用场景 |
|------|------|-----------|---------|
| **Sequential** | 顺序执行 | `chain1 \| chain2` | 线性流程 |
| **Parallel** | 并行执行 | `RunnableParallel` | 独立任务 |
| **Router** | 条件路由 | `RunnableBranch` | 分支逻辑 |
| **Map-Reduce** | 映射归约 | `RunnableMap` | 批量处理 |
| **Transform** | 数据转换 | `RunnableLambda` | 自定义逻辑 |

### 4.2 Sequential Chain（最基础）

```python
# LCEL 实现
chain = prompt1 | model | parser | prompt2 | model | parser
```

**💡 记忆要点**：Sequential = 管道连接，最简单的 Chain

### 4.3 Parallel Chain（并行加速）

```python
# 并行执行多个任务
parallel_chain = RunnableParallel(
    summary=summary_chain,
    translation=translation_chain,
    keywords=keywords_chain
)

result = parallel_chain.invoke({"text": "..."})
# 返回: {"summary": "...", "translation": "...", "keywords": [...]}
```

**性能提升**：
- 串行：3s + 2s + 1s = 6s
- 并行：max(3s, 2s, 1s) = 3s
- **提升：50%**

**💡 记忆要点**：Parallel = 并行执行，节省 50% 时间

---

## 5. Memory 架构模式

### 5.1 五种 Memory 模式对比（必背）

| 模式 | 存储方式 | 容量 | 检索速度 | 适用场景 |
|------|---------|------|---------|---------|
| **Buffer** | 全部保留 | 小 | 快 | 短对话 |
| **Summary** | 摘要压缩 | 中 | 快 | 长对话 |
| **Entity** | 实体提取 | 中 | 中 | 结构化信息 |
| **Knowledge Graph** | 图结构 | 大 | 慢 | 复杂关系 |
| **Vector Store** | 向量检索 | 大 | 中 | 语义搜索 |

### 5.2 Buffer Memory（最简单）

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
memory.save_context({"input": "你好"}, {"output": "你好！"})
memory.save_context({"input": "天气如何"}, {"output": "今天晴天"})

# 获取历史
history = memory.load_memory_variables({})
# 返回完整对话历史
```

**优点**：简单、快速
**缺点**：占用 Token 多

**💡 记忆要点**：Buffer = 全部保留，适合短对话

### 5.3 Summary Memory（长对话推荐）

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=model)
# 自动摘要历史对话
```

**Token 节省**：
- Buffer: 1000 tokens（完整历史）
- Summary: 200 tokens（摘要）
- **节省：80%**

**💡 记忆要点**：Summary = 摘要压缩，节省 80% Token

---

## 6. 架构选型决策树（必背）

```
需求分析
├── 需要知识库？
│   ├── 是 → RAG 架构
│   │   ├── 简单问答 → Simple RAG
│   │   ├── 生产应用 → Advanced RAG
│   │   └── 复杂查询 → Agentic RAG
│   └── 否 → 继续
├── 需要工具调用？
│   ├── 是 → Agent 架构
│   │   ├── 通用场景 → ReAct
│   │   ├── 复杂任务 → Plan-and-Execute
│   │   └── OpenAI 模型 → OpenAI Functions
│   └── 否 → 继续
├── 需要多个专家？
│   ├── 是 → Multi-Agent 架构
│   │   ├── 任务分发 → Supervisor-Worker
│   │   ├── 线性流程 → Sequential
│   │   └── 并行任务 → Parallel
│   └── 否 → 继续
├── 需要组合多个步骤？
│   ├── 是 → Chain 架构
│   │   ├── 顺序执行 → Sequential Chain
│   │   └── 并行执行 → Parallel Chain
│   └── 否 → 简单 LLM 调用
└── 需要记住上下文？
    └── 是 → 添加 Memory
        ├── 短对话 → Buffer Memory
        └── 长对话 → Summary Memory
```

---

## 7. 面试问答模板

### Q1: RAG 和 Agent 有什么区别？
**答题框架**：
> "RAG 是检索增强生成，通过检索知识库来增强 LLM 的回答，适合知识密集型任务。Agent 是智能体，能自主决策使用哪些工具，适合需要多步推理和工具调用的任务。两者可以结合：Agentic RAG 就是用 Agent 控制 RAG 的检索流程。"

### Q2: 什么时候用 Multi-Agent？
**答题框架**：
> "当任务需要多个专业领域的能力时用 Multi-Agent。比如差旅管理系统，需要政策专家、天气查询、酒店推荐等不同能力，用 Supervisor-Worker 模式，一个监督者根据查询路由到不同的专家 Agent。相比单一 Agent，Multi-Agent 职责更清晰，更易维护和扩展。"

### Q3: Simple RAG 和 Advanced RAG 的区别？
**答题框架**：
> "Simple RAG 是直接检索+生成，准确率约 60%。Advanced RAG 增加了查询重写、混合检索（BM25+Dense）、重排序等技术，准确率提升到 80%。在我的项目中，通过三路混合检索（BM25 + Dense原始 + Dense重写）+ RRF融合，准确率从 60% 提升到 80%，召回率提升 20-30%。"

---

## 8. 学习检查清单

### 必须掌握（⭐⭐⭐）
- [ ] 六种 RAG 模式的区别和选择
- [ ] ReAct Agent 的工作原理
- [ ] Supervisor-Worker 多智能体模式
- [ ] Sequential vs Parallel Chain
- [ ] Buffer vs Summary Memory

### 应该了解（⭐⭐）
- [ ] Agentic RAG 的优势
- [ ] Plan-and-Execute Agent
- [ ] Dynamic Routing 多智能体
- [ ] Map-Reduce Chain
- [ ] Vector Store Memory

---

## 9. 记忆卡片

### 卡片 1：RAG 准确率
```
正面：不同 RAG 模式的准确率？
背面：
- Simple RAG: 60%
- Advanced RAG: 80%
- Agentic RAG: 85%
- Graph RAG: 90%
```

### 卡片 2：Agent 选择
```
正面：什么时候用 ReAct vs Plan-and-Execute？
背面：
- ReAct: 通用工具调用，逐步推理
- Plan-and-Execute: 复杂多步任务，先规划后执行
```

### 卡片 3：Multi-Agent 模式
```
正面：最常用的多智能体模式？
背面：
Supervisor-Worker
- 一个监督者
- 多个专家 Worker
- 动态路由
- 易于扩展
```

---

**下一章预告**：第三章将对比向量数据库、嵌入模型、LLM 提供商等技术栈选型。
