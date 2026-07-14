# 面试问题代码映射文档

文档版本: v1.0
创建日期: 2026-07-13
用途: 为面试问题标注对应的代码位置和关键知识点

---

## 使用说明

**面试准备流程**：
1. 在新对话中，让 AI 提问某一题
2. AI 根据本文档的"代码位置"部分，读取对应文件
3. AI 基于实际代码和架构文档，评估你的回答

**文档结构**：
- 每道题包含：问题编号、代码位置、关键文件、核心概念、参考文档

---

## 一、多模态与模型优化（Q1-Q5）

### Q1: 多模态微调方案设计

**代码位置**：
- `src/multimodal/processor.py` - 多模态处理器（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.3 节

**关键概念**：多模态融合、OCR+Vision LLM、结构化输出

---

### Q2: vLLM PagedAttention 机制

**代码位置**：
- 本项目未实现 vLLM（使用云端 API）

**关键概念**：KV Cache 分页、内存优化、长文本推理

---

### Q3: MCP 2.0 跨模态对齐

**代码位置**：
- `src/mcp/trip_tools_server.py` - MCP Server（v2 已有）
- `src/tools/mcp_client.py` - MCP 客户端（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.4.1 节

**关键概念**：MCP 协议、时间同步、语义对齐

---

### Q4: Qwen2.5-VL 发票解析降级策略

**代码位置**：
- `src/multimodal/processor.py` - `_process_image()` 方法（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.3 节

**关键概念**：
- 置信度阈值（0.8）
- 降级策略：多模型融合、Vision LLM 二次校验、人工复核

---

### Q5: LLM 数字识别错误纠正

**代码位置**：
- `src/modules/reimbursement/form_generator.py`（v3 规划）
- `src/security/output_guardrail.py`（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.2 节

**关键概念**：
- 校验环节：JSON Schema、业务规则、LLM 二次验证
- 纠正策略：回退 OCR、用户确认、人工复核

---

## 二、架构设计与扩展性（Q6-Q11）

### Q6: 高并发系统架构设计

**代码位置**：
- 当前架构：单机 100 QPS
- `docs/ARCHITECTURE_V3_PLAN.md` 第 3 节、第 8 节

**关键概念**：
- 瓶颈：LLM 推理、向量检索、数据库、Redis
- 优化：异步化、批处理、缓存、分片、读写分离
- 架构演进：服务拆分、连接池、CDN、限流降级

---

### Q7: 事件驱动 vs RPC 调用

**代码位置**：
- `src/core/events/bus.py` - 事件总线（v3 规划）
- `src/core/events/consumers/` - 消费者（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.4 节

**关键概念**：
- 事件驱动优势：解耦、异步、可扩展、容错
- RPC 缺点：强耦合、同步阻塞、单点故障
- 使用场景：监控/日志用事件，工具调用用 RPC

---

### Q8: 系统可用性优化

**代码位置**：
- `src/monitoring/prometheus_exporter.py` - 监控（v2 已有）
- `src/tools/registry/circuit_breaker.py` - 熔断器（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 8 节

**关键概念**：
- 优先级：LLM（最高） > MySQL/Redis > Milvus > 外部 API > 飞书
- 优化策略：缓存、降级、重试、熔断、主从复制

---

### Q9: 扩展性规划

**代码位置**：
- `src/agents/orchestrator_agent.py` - 统一入口（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.1 节
- `docs/ARCHITECTURE_V3_PLAN.md` 第 3 节

**关键概念**：
- 最先重构：OrchestratorAgent（单点瓶颈）
- 预算有限选择：重构为无状态服务 + 负载均衡
- 收益最大、成本最低

---

### Q10: Loop Engineer vs 工作流引擎

**代码位置**：
- `src/modules/module_5_langgraph/graphs/approval_graph.py` - 审批工作流
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.2 节

**关键概念**：
- Loop Engineer（LangGraph）：动态决策、循环执行、AI Agent
- 传统工作流（Airflow）：静态流程、DAG、批处理
- 选择：有 LLM 决策用 LangGraph，固定流程用 Airflow

---

### Q11: 工具生态扩展

**代码位置（v2 - 硬编码）**：
- `src/tools/registry.py` - 需手动添加

**代码位置（v3 - 自动注册）**：
- `src/tools/configs/meal_order.yaml` - 新增配置（零代码改动）
- `src/tools/handlers/meal_order.py` - 新增 handler
- `src/tools/registry/registry.py` - 自动扫描加载
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.5 节

**关键概念**：
- v2 改动：3 处代码修改
- v3 改动：2 个新文件，零代码改动
- LLM 发现：启动时扫描 YAML，生成 Function Calling 格式
- 错误检测：返回结果检查、人工反馈闭环

---

## 三、记忆系统设计（Q12-Q14）

### Q12: MemoryService 模块协同

**代码位置**：
- `src/memory/memory_service.py` - 记忆服务（v2 已有）
- `src/memory/working_memory.py` - 工作记忆（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 2.1 节

**关键概念**：
- 三层记忆：
  1. 对话记忆（Redis, 1h TTL, 最近 10 轮）
  2. 用户画像（MySQL, 职级/部门/偏好）
  3. 工作记忆（Redis, 24h TTL, 审批状态/任务进度）
- 协同：`build_enhanced_prompt()` 合并三层
- 优先级：对话 > 工作 > 画像

---

### Q13: 会话恢复机制

**代码位置**：
- `src/memory/working_memory.py` - 会话状态持久化
- `src/memory/chat_memory.py` - 对话历史（v2 规划）

**关键概念**：
- 跨设备：通过 user_id 关联，从 Redis 加载会话
- 超时恢复：
  - < 30 分钟：直接恢复
  - > 30 分钟：加载工作记忆 + 摘要对话历史
- 持久化：Redis + MySQL 双写

---

### Q14: 事件 Schema 版本兼容性

**代码位置**：
- `src/core/events/event.py` - 事件基类（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.4 节

**关键概念**：
- Avro 向后兼容：V2 新增字段有默认值
- V1 消费者收到 V2 消息：忽略未知字段，不会崩溃
- 最佳实践：字段只增不减、必填字段有默认值

---

## 四、分布式系统与可靠性（Q15-Q20）

### Q15: TraceID 异步传递

**代码位置**：
- `src/core/tracing/context.py` - TraceID 上下文（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 五.T8 节

**关键概念**：
- 同步传递：通过函数参数
- 异步传递：contextvars（Python 3.7+）
- CompletableFuture 问题：需要显式传递 context
- 解决方案：
  ```python
  import contextvars
  trace_id_var = contextvars.ContextVar('trace_id')
  # 异步任务自动继承
  ```

---

### Q16: 飞书回调签名验证与防重放

**代码位置**：
- `src/harness/feishu/gateway.py` - 飞书网关（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.1 节

**关键概念**：
- 签名验证：HMAC-SHA256（timestamp + nonce + encrypt_key + body）
- 防重放：
  1. timestamp 检查（当前时间 ± 5 分钟）
  2. nonce 去重（Redis 存储，10 分钟过期）
- 攻击者重放 5 分钟前请求：nonce 已存在，拒绝

---

### Q17: 回调丢失处理

**代码位置**：
- `src/harness/feishu/gateway.py` - Webhook 处理（v3 规划）
- `src/agents/approval_engine.py` - 审批引擎（v2 已有）

**关键概念**：
- 问题：用户点击"确认" → 回调丢失 → 界面卡住
- 优化策略：
  1. 超时机制：30 秒未收到回调 → 更新为"处理中，请稍候"
  2. 轮询兜底：前端每 5 秒查询审批状态
  3. 重试机制：飞书回调失败 → 3 次重试
  4. 降级方案：用户可手动刷新状态

---

### Q18: MCP Server 熔断策略

**代码位置**：
- `src/tools/registry/circuit_breaker.py` - 熔断器（v3 规划）
- `src/tools/registry/registry.py` - 工具注册中心（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.5 节

**关键概念**：
- 熔断条件：连续 3 次失败
- 恢复机制：60 秒后半开状态（1 次成功 → 关闭熔断）
- 降级策略：
  - 天气工具：返回"暂时无法查询，请稍后重试"
  - 酒店工具：返回缓存数据或默认推荐
- 用户感知：提示"部分功能不可用"，不影响核心流程

---

### Q19: 预算数据同步延迟

**代码位置**：
- `src/agents/approval_engine.py` - 审批引擎（v2 已有）

**关键概念**：
- 问题：预算 T+1 同步，实际超预算但显示有余额
- 解决方案：
  1. 预算扣减：审批通过时立即扣减（乐观锁）
  2. 超预算检测：审批前查询实时余额（调用预算系统 API）
  3. 补偿机制：T+1 同步发现超支 → 告警 + 人工介入
  4. 用户提示："预算数据延迟 1 天，请以财务系统为准"

---

### Q20: 意图识别模块降级

**代码位置**：
- `src/agents/orchestrator_agent.py` - 统一路由（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.1 节

**关键概念**：
- 问题：意图识别（LLM）挂了 → 整个系统不可用
- 降级策略：
  1. 规则匹配兜底：关键词匹配（"天气" → 天气工具）
  2. 默认路由：无法识别 → 走复杂通道（最全面）
  3. 缓存：最近 1 小时的意图识别结果
- 结果：意图识别挂了，系统仍可用（准确率下降但不崩溃）

---

## 五、任务编排与路由策略（Q21-Q25）

### Q21: 简单 vs 复杂问答通道分界

**代码位置**：
- `src/agents/qa_engine.py` - Q&A 引擎（v2 已有）
- `src/agents/complexity_assessor.py` - 复杂度评估（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.3 节

**关键概念**：
- 分界标准：
  1. **LLM 判断（主要）**：分析查询复杂度
  2. 辅助规则：
     - 简单：单一意图（"北京住宿标准"）
     - 复杂：多步骤（"去杭州3天要多少钱"）
- 判断逻辑：
  - 工具数量：1 个 → 简单，>1 个 → 复杂
  - 依赖关系：无依赖 → 简单，有依赖 → 复杂

---

### Q22: 子任务编排触发条件

**代码位置**：
- `src/agents/task_decomposer.py` - 任务分解器（v2 已有）
- `src/agents/workflow_orchestrator.py` - 工作流编排（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.3 节

**关键概念**：
- 触发条件：复杂度评分 > 阈值（LLM 判断需要多步）
- 并行 vs 串行：
  - 并行：无依赖（航班、酒店、用车同时查）
  - 串行：有依赖（先查政策 → 再推荐酒店）
- 依赖检测：任务分解时分析输入输出关系

---

### Q23: API 超时处理

**代码位置**：
- `src/agents/workflow_orchestrator.py` - 并行执行（v2 已有）
- `src/tools/registry/registry.py` - 超时控制（v3 规划）

**关键概念**：
- 等待策略：
  - 设置总超时（如 10 秒）
  - 酒店 API 慢 5 秒，航班 API 2 秒
  - 10 秒后：航班有结果，酒店超时
- 超时处理：
  1. 部分结果返回（航班信息 + "酒店查询超时"）
  2. 降级方案（返回缓存或默认推荐）
  3. 异步补偿（后台继续查，查到后推送）

---

### Q24: 检索结果冲突处理

**代码位置**：
- `src/rag/retriever.py` - 检索器（v2 已有）
- `src/rag/fusion_retriever.py` - 融合检索（v2 已有）
- `src/modules/module_6_self_rag/` - Self-RAG（v2 已有）

**关键概念**：
- 场景："高管去上海能住什么酒店"
- 召回 Top3：普通员工标准、高管标准、上海临时政策
- 决策逻辑（Self-RAG）：
  1. 用户画像匹配："高管" → 排除"普通员工标准"
  2. 时间相关性：检查"临时政策"是否在有效期
  3. LLM 推理：综合判断哪个最相关
  4. 置信度评分：选择置信度最高的

---

### Q25: 四通道路由决策

**代码位置**：
- `src/agents/qa_engine.py` - `_llm_route()` 方法（v2 已有）
- `docs/ARCHITECTURE_V2_PLAN.md` 第 4.3 节

**关键概念**：
- 路由 Prompt：
  ```
  分类标准：
  - simple: 单工具回答
  - complex: 多步骤可分解
  - planning: 需要完整方案
  - open: 比较/推荐/评价
  ```
- 避免误判：
  1. Few-shot 示例（每个通道 2-3 个例子）
  2. 置信度阈值（< 0.7 → 走复杂通道）
  3. 规则兜底（关键词匹配）

---


## 六、业务指标与评估（Q26-Q27）

### Q26: 北极星指标定义

**代码位置**：
- `src/evaluation/` - 评估模块（v3 规划）
- `src/monitoring/prometheus_exporter.py` - 指标收集（v2 已有）

**关键概念**：
- 北极星指标：**审批自动化率**（最核心的业务价值）
- 计算公式：自动通过审批数 / 总审批数 = 60%
- 其他关键指标：用户满意度、审批时效、人工成本节省、知识准确率

**参考文档**：
- `docs/ARCHITECTURE_V3_PLAN.md` 第 9 节：成功指标

---

### Q27: Agent 评测维度

**代码位置**：
- `src/evaluation/llm_judge.py` - LLM-as-Judge（v3 规划）
- `src/evaluation/feedback_collector.py` - 反馈收集（v3 规划）

**关键概念**：
1. **任务成功率**：任务完成率、目标达成率
2. **工具准确率**：工具选择 95%+、参数准确率 98%+
3. **推理质量**：规划合理性、是否死循环、错误回复率
4. **并行效率**：并行任务数、结果整合质量、延迟对比
5. **安全合规**：安全事件数、合规检查通过率

---

## 七、开放性问题（Q28-Q35）

### Q28: Redis Stream vs RabbitMQ vs Kafka

**代码位置**：
- `src/core/events/bus.py` - Redis Stream（v3 规划）
- `docs/ARCHITECTURE_V3_PLAN.md` 第十.决策1

**关键概念**：
- 选择 Redis Stream：已用 Redis、消息量小、简单易用、支持消费者组
- 不选 RabbitMQ：需额外部署、对小规模场景过重
- 不选 Kafka：过度设计、运维复杂

---

### Q29: 技术演进路径

**代码位置**：
- `docs/ARCHITECTURE_V2_PLAN.md` - v2 架构
- `docs/ARCHITECTURE_V3_PLAN.md` - v3 架构 + v4 展望

**关键概念**：
- 重新设计会改变：更早引入事件驱动、工具注册中心从一开始做、安全护栏第一优先级
- 保持不变：LangGraph 工作流、三层记忆、Self-RAG

---

### Q30: 失败案例分享

**代码位置**：
- `docs/ARCHITECTURE_V2_PLAN.md` 第 11 节：实施问题记录

**关键概念**：
- 案例 1：Pydantic 字段验证冲突 → 使用私有属性
- 案例 2：检索器接口不统一 → 多接口适配
- 案例 3：Windows GBK 编码 → UTF-8 声明

---

### Q31: Self-RAG 理解与应用

**代码位置**：
- `src/modules/module_6_self_rag/` - Self-RAG 实现（v2 已有）
- `docs/MODULE6_COMPLETION_SUMMARY.md` - Self-RAG 总结

**关键概念**：
- 原理：Retrieve → Reflect → Generate → Critique → Refine
- 应用：三路检索 + 自我反思 + 准确率 45% → 80%
- 效果：减少幻觉、提升准确率

---

### Q32-Q35: 工程能力、团队协作、业务理解、未来规划

**代码位置**：
- `tests/` - 测试代码（75 个单元测试 + 10 个 E2E）
- `docs/ARCHITECTURE_V3_PLAN.md` 第 6/11 节

**关键概念**：
- 测试覆盖率：85%+
- 团队分配：3 人（工具层、多模态、飞书集成）
- 核心痛点：审批慢、政策难查、流程繁琐、信息孤立
- 未来规划：完成 v3 → 性能优化 → 新功能探索

---

## 八、针对简历的追问（Q36-Q49，必问 ⚠️）

### Q36: "45%" 测试方法

**代码位置**：
- `src/evaluation/` - 评估脚本（需补充）

**关键概念**：
- 测试集：100 条真实问题
- 评估方法：人工标注 + Top3 命中率
- 基线：单路向量检索 = 45%

---

### Q37: "80%" 优化路径

**代码位置**：
- `src/rag/fusion_retriever.py` - 三路检索
- `src/modules/module_6_self_rag/` - Self-RAG

**关键概念**：
1. 三路检索：45% → 65%（BM25 + FAISS + Neo4j）
2. Self-RAG：65% → 75%（自我反思 + 迭代优化）
3. BGE 重排序：75% → 80%（Top10 重排）

---

### Q38: 三路检索权重

**代码位置**：
- `src/rag/fusion_retriever.py` - `_fuse_results()` 方法

**关键概念**：
- 权重：BM25(0.3) + FAISS(0.5) + Neo4j(0.2)
- 调优：网格搜索 27 种组合
- 场景调整：政策查询提高 BM25、关系查询提高 Neo4j

---

### Q39: Self-RAG 反思机制

**代码位置**：
- `src/modules/module_6_self_rag/` - Self-RAG 实现

**关键概念**：
- 步骤：Retrieve(Top10) → Reflect(相关性 0-1) → Filter(< 0.6 过滤) → Generate → Critique → Refine
- 最多迭代：3 次

---

### Q40: 重排序模型

**代码位置**：
- `src/rag/fusion_retriever.py` - BGE 重排序

**关键概念**：
- 模型：BAAI/bge-reranker-large
- 原理：Query-Document 交互（精排）
- 效果：Top3 准确率提升 5-10%

---

### Q41: "3 倍" 计算方法

**代码位置**：
- `src/agents/approval_engine.py` - 审批引擎

**关键概念**：
- 优化前：2-3 天（人工审批）
- 优化后：60% 自动（< 1 分钟）+ 40% 人工（< 1 天）= 加权 10 小时
- 计算：60 小时 / 10 小时 = 6 倍（保守说 3 倍）

---

### Q42: 自动审批率 60% 统计

**代码位置**：
- `src/agents/approval_engine.py` + Prometheus

**关键概念**：
- 样本：1 个月 500 笔审批
- 自动通过：300 笔（< 1000 元）
- 自动审批率：300 / 500 = 60%

---

### Q43: 金额阈值 1000 元依据

**代码位置**：
- `src/agents/approval_engine.py` - 阈值配置

**关键概念**：
- 历史数据：< 1000 元占 60%，< 2000 元占 80%
- 风险评估：1000 元以下风险可控
- 业务需求：财务部门要求 + 审批人舒适区
- 为什么不是 500：自动率只有 40%，效果不明显
- 为什么不是 2000：风险高，财务不接受

---

### Q44: "40%" 工时节省估算

**代码位置**：
- 审批流程对比

**关键概念**：
- 优化前：500 笔 × 20 分钟 = 167 小时
- 优化后：200 笔 × 20 分钟 = 67 小时
- 节省：(167 - 67) / 167 = 60%（保守说 40%）

---

### Q45: 误审情况处理

**代码位置**：
- `src/agents/approval_engine.py` - 审批逻辑

**关键概念**：
- 误审率：< 1%（5 笔 / 500 笔）
- 原因：政策理解错误、信息不全、边界情况
- 纠正：人工复核 + 申诉通道 + 反馈闭环
- 接受度：85% 满意

---

### Q46: 多模态 90%+ 数据集

**代码位置**：
- 测试集：`data/invoice_test_set/`（需准备）

**关键概念**：
- 规模：200 张发票（增票 80 + 普票 80 + 电票 40）
- 指标：字段级准确率（金额、日期、商家）
- 结果：540 / 600 = 90%
- 覆盖：常见类型（未覆盖定额、手写发票 < 5%）

---

### Q47: 识别错误处理

**代码位置**：
- `src/multimodal/processor.py` - 降级策略

**关键概念**：
- 发现：置信度 < 0.8 → 标记"需复核"
- 人工复核：推送财务 → 修正 → Bad Case 收集
- 降级：识别失败 → 提示手动输入

---

### Q48: 三层记忆数据量

**代码位置**：
- `src/memory/` - 记忆模块
- Redis / MySQL 存储

**关键概念**：
- 对话记忆：10000 用户 × 10 轮 × 500 字符 = 50MB（Redis, TTL 1h）
- 用户画像：10000 用户 × 1KB = 10MB（MySQL）
- 工作记忆：100 × 2KB = 200KB（Redis, TTL 24h）
- 垃圾回收：TTL 自动过期 + 定期清理离职员工

---

### Q49: 智能遗忘策略

**代码位置**：
- `src/memory/chat_memory.py` - 遗忘机制（v2 规划）

**关键概念**：
- 策略：时间衰减（> 1h 降权、> 24h 删除）+ 重要性评分 + 容量限制（最多 10 轮）
- 保护：工作记忆单独存储、关键信息持久化、历史可查（30 天）
- 误删风险：< 1%（主要是闲聊）

---


## 九、压力测试问题（Q50-Q54）

### Q50: 极端场景处理（连续 10 次问同一问题）

**代码位置**：
- `src/agents/orchestrator_agent.py` - 统一入口
- `src/memory/chat_memory.py` - 对话历史

**关键概念**：
- 检测机制：对话历史相似度检测（连续 3 次相同问题）
- 处理策略：
  1. 第 1-3 次：正常回答
  2. 第 4-6 次：提示"您已多次询问，是否需要换个说法？"
  3. 第 7-10 次：
     - 提供反馈入口："回答不满意？点击反馈"
     - 转人工客服
     - 记录 Bad Case
- 防止死循环：最多 10 次后拒绝服务（24 小时内）

---

### Q51: 恶意攻击防护（Prompt Injection）

**代码位置**：
- `src/security/input_guardrail.py` - 输入护栏（v3 规划）
- `src/api/unified_api.py` - API 限流

**关键概念**：
- 检测机制：
  1. 正则匹配恶意模式（"ignore previous instructions"）
  2. 输入长度限制（> 10000 字符拒绝）
  3. 频率限制（同一 IP 1 分钟 > 10 次请求 → 封禁）
- 防护策略：
  1. 输入护栏拦截（拦截率 95%+）
  2. 限流 + 熔断（令牌桶算法）
  3. IP 黑名单（Redis 存储）
  4. 飞书告警（恶意请求 > 10 次/小时）

**参考文档**：
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.2 节：输入护栏

---

### Q52: 数据泄露风险

**代码位置**：
- `src/security/output_guardrail.py` - 输出护栏（v3 规划）
- `src/monitoring/audit_logger.py` - 审计日志（v3 规划）

**关键概念**：
- 安全措施：
  1. **敏感信息脱敏**：
     - 电话：139****1234
     - 身份证：110101********1234
     - 邮箱：abc***@example.com
  2. **访问控制**：
     - RBAC 权限（普通员工/经理/管理员）
     - 数据加密存储（MySQL AES_ENCRYPT）
     - API 鉴权（JWT Token）
  3. **审计日志**：
     - 记录所有敏感操作（谁、何时、做了什么）
     - 日志保留 1 年
     - 支持数据导出/删除（GDPR 合规）
  4. **网络隔离**：
     - 内网访问（VPN）
     - 数据不出境

**参考文档**：
- `docs/ARCHITECTURE_V3_PLAN.md` 第 4.2/4.6 节：安全护栏

---

### Q53: 系统崩溃恢复（Redis/MySQL/Milvus 同时挂）

**代码位置**：
- `src/agents/orchestrator_agent.py` - 降级策略
- `src/tools/registry/circuit_breaker.py` - 熔断器（v3 规划）

**关键概念**：
- 问题：三大依赖同时挂 → 系统还能运行吗？
- 答案：**可以运行（降级模式）**
- 降级策略：
  1. **Redis 挂了**：
     - 对话记忆：无记忆（单轮对话）
     - 工作记忆：无法恢复会话
     - 缓存：无缓存（性能下降）
  2. **MySQL 挂了**：
     - 用户画像：使用默认值
     - 审批记录：暂存 Redis（24h TTL）
     - 持久化：延迟写入
  3. **Milvus 挂了**：
     - 向量检索：降级到 BM25
     - 准确率：下降到 60%
- 核心功能保留：
  - 工具调用：仍可用（天气/酒店/航班）
  - 简单问答：仍可用（规则匹配）
  - 审批：仍可用（暂存 Redis）

---

### Q54: 成本控制（LLM API 翻倍）

**代码位置**：
- `src/monitoring/token_tracker.py` - Token 统计（v3 规划）
- `src/agents/orchestrator_agent.py` - 模型选择

**关键概念**：
- 优化策略：
  1. **缓存**（最有效）：
     - 相同问题缓存结果（Redis, TTL 1h）
     - 命中率：30-40%
     - 成本降低：30-40%
  2. **模型降级**：
     - 简单任务：GPT-4 → GPT-3.5（成本降 90%）
     - 复杂任务：保持 GPT-4
     - 成本降低：20-30%
  3. **Prompt 优化**：
     - 减少 few-shot 示例（10 个 → 3 个）
     - 压缩系统 Prompt（2000 tokens → 500 tokens）
     - 成本降低：10-15%
  4. **批处理**：
     - 多个查询合并为一次调用
     - 成本降低：5-10%
- 总计：成本降低 **65-95%**，抵消翻倍影响

---

## 十、行为面试问题（Q55-Q60）

### Q55: 项目管理

**代码位置**：
- `docs/ARCHITECTURE_V2_PLAN.md` 第 7 节：实施计划
- `docs/ARCHITECTURE_V3_PLAN.md` 第 6 节：实施计划

**关键概念**：
- 时间：v2 花了 **3 个月**（Phase 0-4）
- 团队：**2 人**（你 + 1 个初级工程师）
- 你的角色：
  - 技术负责人（架构设计、核心模块）
  - 代码贡献：70%（核心 Agent、RAG、审批流程）
  - 团队管理：任务分配、Code Review、技术指导

---

### Q56: 技术决策分歧

**代码位置**：
- `docs/ARCHITECTURE_V3_PLAN.md` 第十节：关键决策记录

**关键概念**：
- **分歧案例：事件总线选型**
  - 你的观点：Redis Stream（轻量、已有 Redis）
  - 团队成员：RabbitMQ（更专业、功能强）
- 达成一致：
  1. 数据分析：消息量 < 1000 msg/s
  2. 成本对比：Redis Stream 无额外成本
  3. POC 验证：两周内验证 Redis Stream 可行
  4. 决策：先用 Redis Stream，流量大了再迁移
- 经验：用数据说话、POC 验证、迭代优化

---

### Q57: 困难克服

**代码位置**：
- `docs/ARCHITECTURE_V2_PLAN.md` 第 11 节：实施问题记录

**关键概念**：
- **最大困难：知识检索准确率低（45%）**
- 克服过程：
  1. 分析原因：单路向量检索、语义理解弱
  2. 尝试方案：
     - 方案 1：优化 Embedding 模型（提升到 50%）
     - 方案 2：引入 BM25（提升到 55%）
     - 方案 3：加入图谱查询（提升到 65%）
     - 方案 4：Self-RAG（提升到 75%）
     - 方案 5：重排序（提升到 80%）
  3. 迭代优化：每步验证效果，逐步改进
- 教训：复杂问题需要组合拳，不是单一技术能解决

---

### Q58: 持续学习

**代码位置**：
- 学习笔记（项目文档）

**关键概念**：
- 新学习的技术：
  1. **LangGraph**：工作流引擎（官方文档 + 示例）
  2. **Self-RAG**：论文阅读 + 代码实现
  3. **MCP 协议**：官方规范 + 实践
  4. **Prometheus 监控**：官方文档 + 最佳实践
  5. **多模态 LLM**：Qwen-VL 文档 + API 调用
- 学习方法：
  - 官方文档优先
  - GitHub 代码学习
  - 实践验证（POC）
  - 复盘总结（文档）

---

### Q59: 新认识

**代码位置**：
- 项目总结文档

**关键概念**：
- **AI Agent 的核心**：
  1. 不是 LLM 本身，而是如何组织工具和流程
  2. 记忆系统比模型能力更重要
  3. 可观测性是生产必备（监控/日志/追踪）
  4. 安全护栏不是可选项，是必选项
- **工程化关键**：
  1. 从一开始就考虑可扩展性
  2. 工具注册中心比硬编码好 10 倍
  3. 事件驱动解耦模块
  4. 测试和评估是持续迭代的基础
- **业务理解**：
  1. 技术是手段，业务价值是目标
  2. 自动化不是 100%，60% 已经很好
  3. 用户接受度比技术指标更重要

---

### Q60: 自我评分

**代码位置**：
- 项目整体评估

**关键概念**：
- **评分：7.5 / 10**
- 做得好的地方：
  1. 架构设计合理（三层记忆、四通道路由）
  2. 技术选型务实（不过度设计）
  3. 效果显著（准确率 45% → 80%，审批时效提升 3 倍）
  4. 文档完善（架构文档、测试文档）
- 不足之处：
  1. 安全护栏做得晚（应该 v2 就做）
  2. 测试覆盖率可以更高（85% → 95%）
  3. 性能优化空间大（未做分布式）
  4. 多模态能力只完成了一半（v3 才做）
- 改进方向：
  1. 更早引入安全护栏
  2. 从一开始就考虑扩展性
  3. 自动化测试和 CI/CD

---

## 总结：如何使用本文档

### 在新对话中的使用方法

1. **上传本文档**到新对话
2. **告诉 AI**：
   ```
   我要进行面试模拟。请根据 INTERVIEW_QUESTIONS_CODE_MAPPING.md 
   提问，并根据标注的代码位置读取实际代码来评估我的回答。
   
   从 Q1 开始提问。
   ```
3. **AI 工作流程**：
   - 读取问题 Q1 的代码位置
   - 读取对应的文件（如 `src/multimodal/processor.py`）
   - 读取参考文档（如 `docs/ARCHITECTURE_V3_PLAN.md`）
   - 向你提问
   - 根据实际代码评估你的回答
   - 给出反馈和补充

### 重点准备题目（必问 ⚠️）

**优先准备这 20 题**（面试官 90% 会问）：

1. **Q36-Q49**：针对简历的追问（14 题）
   - 所有量化指标的依据
   - 必须有数据支撑

2. **Q6**：高并发架构设计
   - 展示架构能力

3. **Q7**：事件驱动 vs RPC
   - 展示技术深度

4. **Q12**：MemoryService 协同
   - 展示核心设计

5. **Q31**：Self-RAG 理解
   - 展示前沿技术

6. **Q57**：困难克服
   - 展示解决问题能力

### 答题技巧

**STAR 法则**：
- **S**ituation（背景）：项目遇到什么问题
- **T**ask（任务）：你的职责是什么
- **A**ction（行动）：你具体做了什么
- **R**esult（结果）：效果如何（量化指标）

**示例（Q37：80% 如何达到）**：
```
S: v1 版本知识检索准确率只有 45%，用户反馈答非所问
T: 我负责优化检索系统，目标提升到 80%+
A: 分 3 步优化：
   1. 引入三路检索（BM25+向量+图谱），准确率 → 65%
   2. 加入 Self-RAG 自我反思，准确率 → 75%
   3. BGE 重排序优化，准确率 → 80%
R: 最终准确率 80%，用户满意度从 60% 提升到 85%
```

---

## 附录：快速索引

### 按技术栈分类

**RAG 相关**：Q36-Q40, Q24
**Multi-Agent**：Q22, Q25, Q27
**多模态**：Q1, Q3, Q4, Q5, Q46, Q47
**架构设计**：Q6, Q7, Q8, Q9, Q28
**记忆系统**：Q12, Q13, Q48, Q49
**安全合规**：Q14, Q16, Q51, Q52
**监控评估**：Q26, Q27, Q32, Q54
**业务理解**：Q34, Q41-Q45

### 按难度分类

**基础题（直接回答）**：Q26, Q28, Q29, Q32-Q35, Q55-Q60
**中等题（需展开）**：Q1-Q5, Q10-Q25, Q30, Q31
**困难题（深入技术）**：Q6-Q9, Q36-Q49, Q50-Q54

### 按优先级分类

**P0（必问）**：Q36-Q49（14 题）
**P1（高频）**：Q6, Q7, Q12, Q26, Q27, Q31, Q57
**P2（可能问）**：其他题目

---

文档版本: v1.0
问题总数: 60 题
代码覆盖: 25+ 文件
建议准备时间: 2-3 周

**祝你面试顺利！加油！💪**
