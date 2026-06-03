# LangChain 交互式学习路径

> 通过运行实际代码，深入理解LangChain生态系统

---

## 🎯 学习目标

通过7个递进的实战模块，从零到生产级掌握LangChain：

1. ✅ Module 1: Simple RAG - 理解LCEL基础
2. ✅ Module 2: Advanced RAG - 掌握混合检索
3. ✅ Module 3: ReAct Agent - 理解智能体
4. ✅ Module 4: Multi-Agent - 掌握LangGraph
5. ✅ Module 5: Chain Composition - 理解并行组合
6. ✅ Module 6: Memory System - 掌握记忆管理
7. ✅ Module 7: Production - 生产级优化

---

## 📋 环境准备

### 1. 安装依赖

```bash
cd E:/Desktop/langchain-business-trip-management
pip install -r requirements.txt
```

### 2. 配置API Key

```bash
# Windows
set DASHSCOPE_API_KEY=your-dashscope-api-key
set LANGCHAIN_API_KEY=your-langsmith-api-key
set LANGCHAIN_TRACING_V2=true
set LANGCHAIN_PROJECT=business-trip-learning

# Linux/Mac
export DASHSCOPE_API_KEY="your-dashscope-api-key"
export LANGCHAIN_API_KEY="your-langsmith-api-key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="business-trip-learning"
```

### 3. 验证环境

```bash
python verify_environment.py
```

---

## 🎓 Module 1: Simple RAG - LCEL基础

### 学习目标
- ✅ 理解LCEL管道操作符
- ✅ 掌握retriever、prompt、llm、parser组合
- ✅ 理解数据流转过程

### 核心代码解析

**位置**: `src/modules/module_1_simple_rag/chain.py:101-109`

```python
rag_chain = (
    {
        "context": retriever | format_docs,  # 检索→格式化
        "question": RunnablePassthrough()     # 直接传递
    }
    | prompt      # 填充模板
    | llm         # LLM生成
    | StrOutputParser()  # 解析输出
)
```

**数据流分析**：
```
输入: "去上海出差住宿能报多少钱？"
    ↓
步骤1: {"context": "...", "question": "..."}
步骤2: prompt模板填充
步骤3: llm推理
步骤4: 字符串解析
    ↓
输出: "上海属于一线城市，住宿标准不超过500元/晚。"
```

### 实战运行

```bash
cd src/modules/module_1_simple_rag
python chain.py
```

### 🤔 思考题
1. `RunnablePassthrough()`的作用是什么？
2. 为什么要用`format_docs`函数？
3. LCEL比传统LLMChain好在哪里？

---

## 🚀 Module 2: Advanced RAG - 混合检索

### 学习目标
- ✅ 理解查询改写的价值
- ✅ 掌握三路混合检索
- ✅ 理解RRF融合算法
- ✅ 掌握重排序优化

### 核心架构

**三路召回**：
```
原始: "魔都出差住宿能报多少？"
    ↓
改写: "上海一类城市差旅住宿费报销标准"
    ↓
路径1: BM25(原始) → 12个文档
路径2: Dense(原始) → 10个文档
路径3: Dense(改写) → 10个文档
    ↓
RRF融合 → 15个唯一文档
    ↓
重排序 → Top-3最相关
```

### 实战运行

```bash
cd src/modules/module_2_advanced_rag
python chain.py
```

### 准确率对比

| 方法 | 准确率 |
|------|--------|
| 单路BM25 | 50% |
| 单路Dense | 60% |
| 三路混合+RRF | 80% |

### 🤔 思考题
1. 为什么需要三路召回？
2. RRF的k=60参数如何调优？
3. Cross-Encoder vs Bi-Encoder的区别？

---

## 🤖 Module 3: ReAct Agent - 智能体

### 学习目标
- ✅ 理解ReAct循环
- ✅ 掌握工具定义和绑定
- ✅ 理解复杂度评估策略

### ReAct循环

```python
while True:
    # Thought: 思考
    response = llm_with_tools.invoke(messages)
    
    # Action: 行动
    if not response.tool_calls:
        return response.content
    
    # Observation: 观察
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(ToolMessage(content=result))
```

### 复杂度评估策略

**代码**: `src/agents/complexity_assessor.py`

```python
def assess(self, query: str):
    # 80%用规则判断（<1ms）
    rule_result = self._assess_by_rule(query)
    
    # 20%用LLM判断（1-2s）
    if rule_result == COMPLEX:
        return self._assess_by_llm(query)
    
    return rule_result
```

**效果**：
- 工具调用率：0% → 100%
- 延迟：<500ms
- 成本节省：80%

### 实战运行

```bash
cd src/modules/module_3_react_agent
python agent.py
```

---

## 🕸️ Module 4: Multi-Agent - LangGraph

### 学习目标
- ✅ 理解StateGraph
- ✅ 掌握条件路由
- ✅ 理解Supervisor-Worker模式

### StateGraph架构

```python
workflow = StateGraph(State)

# 添加节点
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("policy", policy_agent)
workflow.add_node("weather", weather_agent)

# 添加条件边
workflow.add_conditional_edges(
    "supervisor",
    decide_next,
    {"policy": "policy", "weather": "weather", "end": END}
)

app = workflow.compile()
```

### 执行流程

```
用户查询
    ↓
Supervisor分析
    ↓
路由到专业Agent
    ↓
返回结果
    ↓
判断是否继续
    ↓
最终答案
```

### 实战运行

```bash
cd src/modules/module_4_multi_agent
python example.py
```

---

## 🧠 Module 6: Memory System - 记忆管理

### 学习目标
- ✅ 理解三层记忆架构
- ✅ 掌握增量学习机制
- ✅ 理解个性化推荐

### 三层记忆

```
Layer 1: 短期记忆
  - 存储：文件
  - 容量：20条
  - 用途：上下文

Layer 2: 工作记忆
  - 存储：内存
  - TTL：30分钟
  - 用途：实体提取

Layer 3: 长期记忆
  - 存储：JSON
  - 容量：无限
  - 用途：用户画像
```

### 实战运行

```bash
cd src/modules/module_6_memory
python example.py
```

---

## ⚡ Module 7: Production - 生产级优化

### 学习目标
- ✅ 掌握LangSmith追踪
- ✅ 理解缓存策略
- ✅ 掌握流式输出
- ✅ 理解批处理优化

### 四大优化

```
1. LangSmith: 调试时间 数小时 → 5分钟
2. 缓存: 成本节省 60%
3. 流式: 感知延迟降低 95%
4. 批处理: 吞吐量提升 75%
```

### 实战运行

```bash
cd src/modules/module_7_production
python example_usage.py
```

---

## 📊 学习检查清单

### LCEL基础
- [ ] 理解管道操作符`|`
- [ ] 掌握RunnablePassthrough
- [ ] 能手写Simple RAG链

### Advanced RAG
- [ ] 理解三路混合检索
- [ ] 理解RRF融合
- [ ] 能实现重排序

### Agent系统
- [ ] 理解ReAct循环
- [ ] 能定义工具
- [ ] 理解复杂度评估

### LangGraph
- [ ] 理解StateGraph
- [ ] 能实现条件路由
- [ ] 能实现Supervisor模式

### Memory系统
- [ ] 理解三层记忆
- [ ] 能实现增量学习

### 生产级特性
- [ ] 配置LangSmith
- [ ] 实现缓存
- [ ] 实现流式输出

---

## 🚀 启动完整系统

### API服务

```bash
# Windows
start_api.bat

# Linux/Mac
./run_api.sh
```

### 访问地址

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- Simple RAG: http://localhost:8000/simple-rag/playground
- Advanced RAG: http://localhost:8000/advanced-rag/playground

---

## 📚 参考文档

- [LangChain生态指南](LANGCHAIN_ECOSYSTEM_GUIDE.md) - 理论深度讲解
- [项目README](README.md) - 项目概述
- [快速开始](QUICK_START.md) - 环境配置
- [架构文档](docs/ARCHITECTURE.md) - 系统设计

---

**祝学习愉快！** 🎉
