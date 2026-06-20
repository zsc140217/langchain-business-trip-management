# Agent Loop学习型MVP - 7天实施方案

> 基于LangGraph的前沿技术学习项目  
> 目标：掌握Agent Loop + 整合现有资产 + 面试准备  
> 时间：2026-06-21 至 2026-06-27

---

## 🎯 核心定位

**这不是生产级项目，而是学习型MVP**

- ✅ 前沿技术学习（Agent Loop是2026年主流）
- ✅ 整合现有资产（Embedding微调 + RAG）
- ✅ 配套复习材料（按你的复习习惯）
- ✅ 面试导向（每个技术点都有话术）

---

## 📊 技术方案：复杂度分层

```
用户查询 → 复杂度评估
    ↓
┌──────────┬────────────┬─────────────┐
│ SIMPLE   │  MEDIUM    │  COMPLEX    │
│ 直接RAG  │ Loop Agent │ LangGraph   │
│ 单次检索 │ 迭代式     │ Multi-Agent │
└──────────┴────────────┴─────────────┘

示例：
- SIMPLE: "上海住宿标准是多少？" → 直接RAG检索
- MEDIUM: "对比北京和上海差旅标准" → Loop Agent迭代查询
- COMPLEX: "规划一次去上海的出差" → Multi-Agent协调
```

---

## 🗓️ 7天实施计划

### Day 1: 基础Loop Agent

**上午**（3h）：
- [ ] 创建`src/modules/module_5_langgraph/`
- [ ] 定义共享状态（TypedDict）
- [ ] 实现简单流程：retrieve → answer
- [ ] 运行第一个示例

**下午**（3h）：
- [ ] 集成现有RAG（`hybrid_retriever.py`）
- [ ] 集成Query Rewriter
- [ ] 添加query_rewrite节点
- [ ] 端到端测试

**产出**：
- `state.py` + `simple_loop_agent.py`
- `learning/day1_loop_basics/notes.md`
- `learning/day1_loop_basics/interview_qa.md`

**学习检查点**：
- [ ] 能画出StateGraph流程图
- [ ] 理解`Annotated[List, operator.add]`
- [ ] 能讲30秒：什么是Agent Loop

---

### Day 2: 条件分支 + ReAct循环

**上午**（3h）：
- [ ] 学习`add_conditional_edges`
- [ ] 实现`should_continue`判断
- [ ] 添加循环计数器
- [ ] 设置`recursion_limit=25`

**下午**（3h）：
- [ ] 实现ReAct模式（Thought → Action → Observation）
- [ ] 添加多轮工具调用
- [ ] 测试：对比北京和上海差旅标准

**产出**：
- `react_loop_agent.py`
- `learning/day2_conditional_loop/notes.md`

**学习检查点**：
- [ ] 能画出循环边流程图
- [ ] 理解`tools_condition`自动路由
- [ ] 能讲2分钟：ReAct vs 普通LLM

---

### Day 3: Checkpointing + 中断恢复

**上午**（3h）：
- [ ] 安装SQLite
- [ ] 理解`SqliteSaver`
- [ ] 实现Checkpointing
- [ ] 测试：Ctrl+C中断后恢复

**下午**（3h）：
- [ ] 添加`thread_id`会话管理
- [ ] 实现多用户隔离
- [ ] 对比：有/无Checkpointing的恢复时间

**产出**：
- `checkpoint_agent.py` + `checkpoints.db`
- `learning/day3_checkpointing/notes.md`

**学习检查点**：
- [ ] 能解释Checkpointing价值
- [ ] 理解`get_state`和`update_state`
- [ ] 能讲STAR故事：中断恢复

---

### Day 4: Human-in-the-Loop审批

**上午**（3h）：
- [ ] 学习`interrupt_before`
- [ ] 实现审批节点
- [ ] 测试：超预算触发审批

**下午**（3h）：
- [ ] 集成到差旅Agent
- [ ] 实现审批日志
- [ ] 设计面试话术

**产出**：
- `approval_agent.py` + `approval_logs.json`
- `learning/day4_human_in_loop/notes.md`

**学习检查点**：
- [ ] 能演示人工审批流程
- [ ] 理解`interrupt` vs `pause` vs `resume`
- [ ] 能讲3分钟：HITL业务价值

---

### Day 5: Send API并行执行

**上午**（3h）：
- [ ] 学习Send API
- [ ] 实现动态创建Worker
- [ ] 测试：不定数量的城市查询

**下午**（3h）：
- [ ] 实现结果聚合节点
- [ ] 对比：串行 vs 并行延迟
- [ ] 生成性能报告

**产出**：
- `parallel_agent.py`
- `learning/day5_send_api/performance_report.md`

**学习检查点**：
- [ ] 能画出Fan-out/Fan-in流程图
- [ ] 理解Send vs 静态并行
- [ ] 能量化：并行速度提升

---

### Day 6: 整合现有资产

**上午**（3h）：
- [ ] 集成Embedding微调模型
- [ ] 连接混合检索器
- [ ] 端到端测试

**下午**（3h）：
- [ ] 设计评估指标
- [ ] 运行10个测试案例
- [ ] 生成评估报告

**产出**：
- `full_system.py`
- `evaluation_results.json`

**学习检查点**：
- [ ] 系统端到端可运行
- [ ] 有量化评估数据
- [ ] 能演示完整流程

---

### Day 7: 学习材料整合

**全天**（6h）：
- [ ] 整合Day 1-6笔记
- [ ] 准备面试话术（30秒/2分钟/5分钟）
- [ ] 制作复习清单
- [ ] 准备STAR故事
- [ ] 录制演示视频（可选）

**产出**：
- `AGENT_LOOP_LEARNING_GUIDE.md`
- `AGENT_LOOP_INTERVIEW_PREP.md`
- `AGENT_LOOP_REVIEW_CHECKLIST.md`

**学习检查点**：
- [ ] 能流畅讲5分钟技术细节
- [ ] 能回答10个高频问题
- [ ] 准备好3个STAR故事

---

## 📁 学习目录结构

```
learning/
└── agent_loop_mvp/
    ├── day1_loop_basics/
    │   ├── notes.md
    │   ├── interview_qa.md
    │   └── review_checklist.md
    ├── day2_conditional_loop/
    ├── day3_checkpointing/
    ├── day4_human_in_loop/
    ├── day5_send_api/
    ├── day6_integration/
    ├── day7_learning_materials/
    └── README.md
```

---

## 🎯 整合现有资产

### T2 Embedding微调

```python
# Day 6集成
from learning.T2_LLM_Finetuning.embedding_finetune import load_finetuned_model

embeddings = load_finetuned_model("learning/models/bge-large-zh-travel-finetuned/")
vectorstore = FAISS.from_documents(docs, embeddings)
```

**面试话术整合**：
> "我的Agent Loop使用了微调的Embedding模型，检索准确率从33%提升到41%，Hard难度查询提升27个百分点，直接提升了工具调用的准确性。"

### Module 2 RAG

```python
# Day 1集成
from src.rag.hybrid_retriever import HybridRetriever

def rag_tool(query: str) -> str:
    results = hybrid_retriever.retrieve(query, top_k=5)
    return "\n".join([doc.page_content for doc in results])
```

### Module 3 ReAct Agent

- Day 2参考其ReAct实现
- 迁移到LangGraph的StateGraph
- 对比：旧版 vs LangGraph

---

## 📚 学习模板

### notes.md模板

```markdown
# Day X: [技术点]

## 核心概念（30秒）
[一句话总结]

## 关键代码片段
[20行以内可运行示例]

## 工作原理图
[ASCII图]

## 遇到的坑
- 问题 → 解决方案
```

### interview_qa.md模板

```markdown
## Q1: [技术点]是什么？（30秒）
**答**：

## Q2: 核心原理？（2分钟）
**答**：

## Q3: 项目中如何使用？（STAR）
**S**: [背景]
**T**: [任务]
**A**: [行动+技术]
**R**: [结果+数据]
```

### review_checklist.md模板

```markdown
## 第1次复习（完成后1天）
- [ ] 能画流程图
- [ ] 能说3个核心API
- [ ] 能讲30秒版本

## 第2次复习（完成后3天）
- [ ] 能从零写代码
- [ ] 能讲2分钟版本

## 第3次复习（完成后7天）
- [ ] 能流畅讲STAR故事
- [ ] 能回答5个追问

## 面试前1天
- [ ] 过一遍核心概念
- [ ] 背30秒+2分钟版本
```

---

## 🚀 立即开始

### 明天（Day 1）启动

```bash
# 1. 创建目录
mkdir -p learning/agent_loop_mvp/day1_loop_basics
mkdir -p src/modules/module_5_langgraph

# 2. 创建状态定义
touch src/modules/module_5_langgraph/state.py

# 3. 参考现有代码
# - LANGGRAPH_DEEP_DIVE.md
# - src/modules/module_4_multi_agent/
```

### 学习节奏

- Day 1-5：每天6小时（上午3h + 下午3h）
- Day 6：全天6小时
- Day 7：全天6小时
- Day 8+：按复习计划回顾

---

## 📊 预期成果

### 技术能力
- ✅ 掌握LangGraph核心API
- ✅ 理解Loop vs Workflow选型
- ✅ 能设计Multi-Agent架构

### 可演示
- ✅ 完整差旅Multi-Agent系统
- ✅ 5个独立Agent示例
- ✅ 性能对比报告

### 面试准备
- ✅ 30秒/2分钟/5分钟话术
- ✅ 3个STAR故事
- ✅ 10个高频问题答案

---

## 💡 关键成功因素

1. **前沿技术优先**：Agent Loop是2026年主流
2. **技术复用**：整合现有Embedding微调和RAG
3. **学习级实现**：SQLite够用，不追求生产级
4. **每天有产出**：代码 + 笔记 + 面试话术
5. **面试导向**：所有学习都为面试服务

---

**准备好了吗？明天（2026-06-21）从Day 1开始！**
