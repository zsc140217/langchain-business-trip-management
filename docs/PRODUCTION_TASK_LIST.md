# Agent Loop生产级MVP - 任务清单

> 目标：生产级AI应用系统，整合前沿技术  
> 复杂度：先按生产级实现，遇到困难再简化  
> 时间：10-15天，按模块完成度推进

---

## 🎯 核心技术栈（7大模块）

1. ✅ **Agent Loop**（LangGraph StateGraph）
2. ✅ **微信Bot接入**（企业微信/个人微信）
3. ✅ **多模态处理**（YOLO + OCR + Vision LLM）
4. ✅ **记忆系统**（短期/工作/长期三层）
5. ✅ **监控告警**（LangSmith + Prometheus + Grafana）
6. ✅ **中断恢复**（Checkpointing持久化）
7. ✅ **高级RAG**（Self-RAG + GraphRAG + Fusion）

---

## 📋 模块1：Agent Loop核心架构 🔴 P0

### T1.1 StateGraph基础架构

**任务**：
- [ ] 定义共享状态（`TravelAgentState`）
- [ ] 实现基础节点：retrieve → answer
- [ ] 集成现有RAG（Query Rewriter + Hybrid Retriever）
- [ ] 测试基础流程

**产出**：
- `src/modules/module_5_langgraph/state.py`
- `src/modules/module_5_langgraph/basic_agent.py`

### T1.2 条件分支 + ReAct循环

**任务**：
- [ ] 实现`add_conditional_edges`
- [ ] 实现`should_continue`判断（循环条件）
- [ ] 添加循环计数器（防无限循环）
- [ ] 测试：对比多城市差旅标准

**产出**：
- `src/modules/module_5_langgraph/react_agent.py`

### T1.3 Checkpointing持久化

**任务**：
- [ ] 选择方案：PostgreSQL（推荐）或 SQLite
- [ ] 实现状态保存和恢复
- [ ] 添加`thread_id`会话管理
- [ ] 测试：Ctrl+C中断 → 重启 → 继续

**产出**：
- `src/modules/module_5_langgraph/checkpoint_agent.py`
- `checkpoints.db`或PostgreSQL配置

### T1.4 Human-in-the-Loop审批

**任务**：
- [ ] 实现`interrupt_before`机制
- [ ] 审批节点（超预算/超天数触发）
- [ ] 审批通知（微信/企业微信/Webhook）
- [ ] 审批日志记录

**产出**：
- `src/modules/module_5_langgraph/approval_agent.py`
- `approval_logs.json`

### T1.5 Send API动态并行

**任务**：
- [ ] 实现Fan-out/Fan-in模式
- [ ] 动态创建Worker（不定数量）
- [ ] 结果聚合节点
- [ ] 性能对比：串行 vs 并行

**产出**：
- `src/modules/module_5_langgraph/parallel_agent.py`
- 性能测试报告

---

## 📋 模块2：微信Bot接入层 🔴 P0

### T2.1 选择接入方案

**决策**：
- 🟢 企业微信官方API（推荐）
- 🟡 个人微信Bot（wechaty/itchat）

**任务**：
- [ ] 申请企业微信API权限
- [ ] 或安装wechaty环境

### T2.2 FastAPI Webhook服务

**任务**：
- [ ] 接收微信消息（文本 + 图片）
- [ ] 消息去重（防重复处理）
- [ ] 请求限流（防滥用）
- [ ] 图片下载和存储

**产出**：
- `src/harness/webhook_server.py`

### T2.3 Redis消息队列

**任务**：
- [ ] Redis安装和配置
- [ ] 异步处理（微信5秒超时）
- [ ] 立即回复"处理中"
- [ ] 处理完成后推送结果

**产出**：
- `src/harness/message_queue.py`

### T2.4 多轮对话支持

**任务**：
- [ ] 会话状态管理（基于用户ID）
- [ ] 上下文保持（结合记忆系统）
- [ ] 信息补全（缺字段主动询问）

**产出**：
- `src/harness/wechat_bot.py`

---

## 📋 模块3：多模态处理 🟡 P1

### T3.1 YOLO模型集成

**任务**：
- [ ] 加载YOLO模型（票据检测）
- [ ] 检测票据类型（机票/酒店/发票）
- [ ] 定位关键区域
- [ ] 推理优化（GPU加速）

**产出**：
- `src/utils/yolo_detector.py`

**降级方案**：如果YOLO未准备好，跳过T3.1，直接用Vision LLM

### T3.2 OCR文字提取

**任务**：
- [ ] PaddleOCR集成
- [ ] 文字定位和识别
- [ ] 结果后处理（去噪）

**产出**：
- `src/utils/ocr_extractor.py`

### T3.3 Vision LLM验证

**任务**：
- [ ] GPT-4o或Claude Sonnet 4集成
- [ ] Prompt设计：验证OCR结果
- [ ] 结构化输出（金额/日期/类型）

**产出**：
- `src/agents/vision_agent.py`

### T3.4 完整Pipeline

**任务**：
- [ ] 图片 → YOLO → OCR → Vision LLM → 结构化
- [ ] 错误处理（图片模糊、OCR失败）
- [ ] 准确率测试

**产出**：
- `src/agents/multimodal_agent.py`
- 评估报告

---

## 📋 模块4：记忆系统 🟡 P1

### T4.1 短期记忆（对话历史）

**任务**：
- [ ] Redis存储最近10轮对话
- [ ] 自动过期（24小时）
- [ ] 上下文窗口管理

**产出**：
- `src/memory/short_term.py`

### T4.2 工作记忆（实体提取）

**任务**：
- [ ] 从对话提取实体（人名/地点/日期/金额）
- [ ] 实体去重和合并
- [ ] 实体关联

**产出**：
- `src/memory/working_memory.py`

### T4.3 长期记忆（用户画像）

**任务**：
- [ ] PostgreSQL存储用户偏好
- [ ] 向量数据库存储历史查询
- [ ] 画像更新策略

**产出**：
- `src/memory/long_term.py`

### T4.4 记忆检索策略

**任务**：
- [ ] 混合检索（时间衰减 + 语义相似度）
- [ ] 记忆相关性排序
- [ ] 记忆注入到Prompt

**产出**：
- `src/agents/memory_agent.py`

---

## 📋 模块5：监控告警系统 🟡 P1

### T5.1 LangSmith集成

**任务**：
- [ ] LangSmith API配置
- [ ] 调用链追踪（每个LLM调用）
- [ ] Prompt和响应记录
- [ ] 延迟和Token统计

**产出**：
- `src/monitoring/langsmith_tracer.py`

### T5.2 Prometheus指标

**任务**：
- [ ] 自定义指标：请求量、成功率、错误率
- [ ] LLM调用次数、Token消耗
- [ ] 检索命中率、缓存命中率
- [ ] /metrics端点

**产出**：
- `src/monitoring/prometheus_metrics.py`

### T5.3 Grafana看板

**任务**：
- [ ] 实时流量监控
- [ ] 错误率趋势
- [ ] 成本分析
- [ ] P95/P99延迟分布

**产出**：
- `monitoring/grafana_dashboard.json`

### T5.4 告警规则

**任务**：
- [ ] 错误率 > 5%
- [ ] P95延迟 > 10秒
- [ ] 日成本 > $50
- [ ] 微信/邮件通知

**产出**：
- 告警配置文件

---

## 📋 模块6：高级RAG 🟢 P2

### T6.1 Self-RAG

**任务**：
- [ ] LLM判断是否需要检索
- [ ] 闲聊直接回复，事实性才检索

**产出**：
- `src/rag/self_rag.py`

### T6.2 GraphRAG（知识图谱）

**任务**：
- [ ] Neo4j搭建
- [ ] 从政策文档提取实体和关系
- [ ] 图谱检索（多跳推理）

**产出**：
- `src/rag/graph_rag.py`

### T6.3 Fusion Retrieval

**任务**：
- [ ] 向量检索（FAISS + 微调Embedding）
- [ ] BM25检索（关键词匹配）
- [ ] 图谱检索（Neo4j）
- [ ] RRF融合算法

**产出**：
- `src/rag/fusion_retriever.py`

### T6.4 评估对比

**任务**：
- [ ] 准备测试数据集（20条查询）
- [ ] 对比各检索策略准确率
- [ ] 生成评估报告

**产出**：
- `tests/evaluation/rag_comparison.py`

---

## 📋 模块7：性能优化 🟢 P2

### T7.1 Prompt优化

**任务**：
- [ ] 减少Token消耗
- [ ] Prompt缓存（Anthropic/OpenAI）
- [ ] 系统Prompt前置

### T7.2 缓存策略

**任务**：
- [ ] Redis缓存检索结果（24小时）
- [ ] LLM响应缓存
- [ ] 缓存命中率统计

### T7.3 批处理优化

**任务**：
- [ ] 批量Embedding生成
- [ ] 批量LLM调用

### T7.4 模型分层

**任务**：
- [ ] 简单任务用小模型（Haiku）
- [ ] 复杂任务用大模型（Sonnet）
- [ ] 自动路由策略

### T7.5 性能测试

**任务**：
- [ ] 压力测试（并发100用户）
- [ ] 延迟分析（P50/P95/P99）
- [ ] 成本分析

**产出**：
- `docs/PERFORMANCE_OPTIMIZATION.md`
- 优化前后对比报告

---

## 🗓️ 实施策略

### 阶段1：核心功能（5-7天）

**必须完成**：
- 模块1（Agent Loop）- 3-4天
- 模块2（微信Bot）- 2-3天

**里程碑**：Agent Loop + 微信Bot端到端可运行

### 阶段2：高级功能（5-7天）

**选择性完成**：
- 模块3（多模态）- 2-3天
- 模块4（记忆系统）- 2-3天
- 模块5（监控告警）- 1-2天

**里程碑**：生产级特性完整

### 阶段3：优化和评估（2-3天）

**可选**：
- 模块6（高级RAG）- 1-2天
- 模块7（性能优化）- 1-2天

**里程碑**：完整评估报告和面试材料

---

## 📊 技术选型决策

| 技术点 | 生产级方案 | 简化方案 | 决策 |
|--------|-----------|---------|------|
| Checkpointing | PostgreSQL | SQLite | 先SQLite，后升级 |
| 微信接入 | 企业微信 | 个人微信 | 优先企业微信 |
| 多模态 | YOLO+OCR+Vision | 仅Vision LLM | 看YOLO是否准备好 |
| 记忆存储 | Redis+PostgreSQL | 全PostgreSQL | 分层存储 |
| 监控 | LangSmith+Prometheus | 仅LangSmith | LangSmith优先 |

---

## 📁 项目结构

```
src/
├── modules/
│   └── module_5_langgraph/      # 模块1
├── harness/                      # 模块2
├── agents/                       # 模块3+4
├── memory/                       # 模块4
├── monitoring/                   # 模块5
└── rag/                          # 模块6

learning/
└── agent_loop_production/        # 学习材料
    ├── module1_agent_loop/
    ├── module2_wechat_bot/
    ├── module3_multimodal/
    ├── module4_memory/
    ├── module5_monitoring/
    ├── module6_advanced_rag/
    └── module7_optimization/
```

---

## 💡 每个模块的学习产出

1. **代码实现**（完整可运行）
2. **学习笔记**（原理 + 实现 + 坑）
3. **面试话术**（30秒/2分钟/5分钟 + STAR）
4. **复习清单**（按你的复习习惯）

---

**准备好开始了吗？从模块1（Agent Loop）开始！**
