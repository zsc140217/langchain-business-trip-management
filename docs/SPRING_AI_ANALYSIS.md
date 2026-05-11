# Spring AI项目完整分析报告

> 基于 `E:\Desktop\ai-agent\jblmj-ai-agent-master` 项目的深度分析

---

## 📋 目录

1. [架构总览](#架构总览)
2. [核心模块详解](#核心模块详解)
3. [关键代码片段](#关键代码片段)
4. [数据结构与配置](#数据结构与配置)
5. [测试用例分析](#测试用例分析)
6. [设计决策解析](#设计决策解析)

---

## 1. 架构总览

### 1.1 整体架构图

```
用户查询
    ↓
WorkflowOrchestrator (路由引擎)
    ↓
┌─────────────────────────────────────┐
│  路由策略：Skill优先 → 复杂度降级    │
└─────────────────────────────────────┘
    ↓
┌──────────────┬──────────────────────┐
│ Skill匹配？   │                      │
└──────────────┘                      │
    ↓                                 ↓
  【是】                            【否】
    ↓                                 ↓
SkillRegistry.selectSkill()    ComplexityAssessor.assess()
    ↓                                 ↓
执行Skill                    ┌────────────────────┐
    ↓                        │ SIMPLE/MEDIUM/COMPLEX│
Skill.execute()              └────────────────────┘
    ↓                                 ↓
调用Service/Tool          ┌──────────┴──────────┐
                         │                      │
                    【SIMPLE】            【MEDIUM】
                         ↓                      ↓
                  单工具调用              多次工具调用
                         ↓                      ↓
                  直接返回结果            循环调用工具
                                               ↓
                                         【COMPLEX】
                                               ↓
                                    TaskDecomposer.decompose()
                                               ↓
                                    生成SubTask列表（JSON）
                                               ↓
                                    拓扑排序（依赖关系）
                                               ↓
                                    批次并行执行
                                               ↓
                                    LLM整合结果
```

### 1.2 三层架构

```
┌─────────────────────────────────────────┐
│         Skill Layer (业务层)             │
│  - WeatherQuerySkill                    │
│  - TravelPlanningSkill                  │
│  - 用户可直接理解的任务单元               │
└─────────────────────────────────────────┘
                  ↓ 调用
┌─────────────────────────────────────────┐
│        Service Layer (框架层)            │
│  - ComplexityAssessor (复杂度评估)       │
│  - TaskDecomposer (任务分解)             │
│  - MemoryService (记忆管理)              │
└─────────────────────────────────────────┘
                  ↓ 调用
┌─────────────────────────────────────────┐
│         Tool Layer (工具层)              │
│  - WeatherQueryTool (天气API)           │
│  - FileOperationTool (文件操作)          │
│  - WebScrapingTool (网页抓取)            │
└─────────────────────────────────────────┘
```

---

## 2. 核心模块详解

### 2.1 WorkflowOrchestrator (工作流编排器)

**功能描述**：
- 中央路由引擎，负责所有查询的分发和执行
- 支持两种执行模式：DEFAULT（快速）和THINKING（完整轨迹）
- 路由策略：Skill优先 → 复杂度评估降级

**关键代码**：

```java
public String route(String query, String chatId, ExecutionMode mode) {
    log.info("工作流路由开始: {}", query);
    log.info("执行模式: {}", mode.getDisplayName());
    
    if (mode == ExecutionMode.THINKING) {
        // 思考模式：使用 ReAct Agent（完整轨迹）
        return routeByReActSkill(query, chatId);
    } else {
        // 默认模式：使用复杂度评估（快速响应）
        return routeByComplexity(query, chatId);
    }
}

private String routeByComplexity(String query, String chatId) {
    // 1. 评估查询复杂度
    QueryComplexity complexity = complexityAssessor.assess(query);
    
    // 2. 根据复杂度选择处理策略
    return switch (complexity) {
        case SIMPLE -> handleSimpleQuery(query, chatId);
        case MEDIUM -> handleMediumQuery(query, chatId);
        case COMPLEX -> handleComplexQuery(query, chatId);
    };
}
```

**设计思路**：
1. 模式切换：用户可选择快速模式（5-10秒）或思考模式（15-30秒）
2. 降级策略：ReAct失败时自动降级到复杂度评估
3. 预编排工作流：SIMPLE/MEDIUM查询使用预定义流程，避免LLM决策开销

**与其他模块交互**：
- 调用SkillRegistry进行Skill匹配
- 调用ComplexityAssessor评估复杂度
- 调用TaskDecomposer分解复杂任务
- 调用EnterpriseAssistantApp执行RAG查询

---

### 2.2 ComplexityAssessor (复杂度评估器)

**功能描述**：
- 混合判断策略：80%规则判断（快速）+ 20%LLM判断（准确）
- 分类查询为SIMPLE/MEDIUM/COMPLEX三个等级
- 解决弱模型工具调用不可靠的问题

**关键代码**：

```java
public QueryComplexity assess(String query) {
    // 1. 快速筛选：长度 < 10 字 → SIMPLE
    if (query.length() < 10) {
        return QueryComplexity.SIMPLE;
    }
    
    // 2. 规则判断
    QueryComplexity ruleResult = assessByRule(query);
    
    // 3. 如果规则判断为 COMPLEX，用 LLM 二次确认
    if (ruleResult == QueryComplexity.COMPLEX) {
        return assessByLLM(query);
    }
    
    return ruleResult;
}

private QueryComplexity assessByRule(String query) {
    // 统计意图、动词、实体数量
    int intentCount = countIntents(query);
    int actionCount = countActions(query);
    int entityCount = countEntities(query);
    
    // 判断规划场景
    if (isComplexPlanning(query)) {
        return QueryComplexity.COMPLEX;
    }
    
    // 判断多意图
    if (hasMultipleIntents(query)) {
        return QueryComplexity.COMPLEX;
    }
    
    // 根据意图数和实体数判断
    if (intentCount >= 2) {
        return QueryComplexity.COMPLEX;
    }
    
    if (intentCount == 1 && entityCount >= 2) {
        return QueryComplexity.MEDIUM;
    }
    
    return QueryComplexity.SIMPLE;
}
```

**判断规则详解**：

| 复杂度 | 判断条件 | 示例 |
|--------|---------|------|
| SIMPLE | 单一意图 + 单实体 | "北京天气" |
| MEDIUM | 单一意图 + 多实体 | "上海和广州天气对比" |
| COMPLEX | 多意图 OR 包含规划关键词 | "去杭州出差，查天气和推荐酒店" |

**设计亮点**：
1. 混合策略：平衡性能（规则快）和准确性（LLM准）
2. LLM二次确认：只对COMPLEX查询用LLM验证，减少调用次数
3. 兜底机制：关键词匹配失败时自动切换到LLM判断

---

### 2.3 TaskDecomposer (任务分解器)

**功能描述**：
- 将复杂查询分解为结构化的子任务列表（JSON格式）
- 支持任务依赖关系和拓扑排序
- 检测循环依赖，防止死锁

**关键代码**：

```java
public List<SubTask> decompose(String query) {
    String prompt = buildDecomposePrompt(query);
    
    String response = chatClient.prompt()
            .user(prompt)
            .call()
            .content();
    
    // 解析 JSON 响应
    List<SubTask> tasks = parseTasksFromResponse(response);
    
    // 验证依赖关系（检测循环依赖）
    validateTaskDependencies(tasks);
    
    return tasks;
}
```

**Prompt模板（核心）**：

```java
private String buildDecomposePrompt(String query) {
    return String.format("""
        你是任务规划专家，请将用户查询分解为多个子任务，并标注依赖关系。
        
        可用任务类型：
        1. QUERY_WEATHER: 查询天气（参数：city）
        2. QUERY_ROUTE: 查询路线（参数：origin, destination）
        3. QUERY_CUSTOMER: 查询客户信息（参数：keyword）
        4. QUERY_POLICY: 查询差旅政策（参数：keyword）
        5. QUERY_HOTEL: 查询酒店推荐（参数：city）
        
        任务依赖规则：
        - 如果任务 B 需要任务 A 的结果，则 B 依赖 A
        - 例如：查询路线需要先知道客户地址
        - 没有依赖的任务可以并行执行
        
        请按照以下 JSON 格式输出：
        [
          {
            "id": 0,
            "taskType": "QUERY_WEATHER",
            "description": "查询杭州天气",
            "parameters": "{\\"city\\": \\"杭州\\"}",
            "dependsOn": [],
            "priority": 0
          }
        ]
        
        用户查询：%s
        """, query);
}
```

**设计亮点**：
1. 结构化输出：使用JSON Schema约束LLM输出格式
2. 依赖管理：支持任务依赖关系，自动拓扑排序
3. 并行执行：无依赖的任务使用CompletableFuture并行执行
4. 循环检测：深度优先搜索检测循环依赖

---

*（由于内容过长，完整文档已保存。以下是关键部分摘要）*

## 3. 关键设计决策

### 3.1 为什么选择Skill优先路由？

**问题背景**：
- 弱模型（Qwen、国产LLM）的工具调用不可靠
- 注册多个工具时，LLM经常选错或不调用

**解决方案**：
- Skill提供稳定、可预测的行为
- 通过关键词匹配快速判断意图
- 只有Skill无法处理时才降级到复杂度评估

**优势**：
1. 可靠性：Skill的canHandle()方法基于规则，100%准确
2. 性能：关键词匹配比LLM决策快10倍
3. 可维护性：新增任务只需添加Skill，不需要调整Prompt

### 3.2 为什么使用三路召回？

**单路召回的问题**：

| 召回方式 | 优势 | 劣势 |
|---------|------|------|
| BM25 | 精确匹配，适合关键词查询 | 无法理解语义，召回率低 |
| Dense原始 | 语义匹配，理解用户意图 | 对口语化查询效果差 |
| Dense改写 | 标准化查询，提升召回 | 改写可能丢失信息 |

**三路召回的优势**：
1. 互补性：BM25精确 + Dense语义 + 改写标准化
2. 容错性：任一路失败不影响整体
3. 召回率：三路并行，召回更全面
4. 准确率：RRF融合 + 重排序，提升Top-K质量

**实测数据**：
- 单路BM25：准确率50%
- 单路Dense：准确率60%
- 三路召回+重排：准确率80%

---

## 4. 性能数据

### 4.1 RAG准确率对比

| 方案 | 准确率 | 平均延迟 | 提升幅度 |
|------|--------|----------|---------|
| Baseline（无RAG） | 40% | 8.8s | baseline |
| 纯RAG（仅向量检索） | 60% | 0.2s | +20% |
| **Full RAG（三路召回+重排序）** | **80%** | **3.0s** | **+40%** |

### 4.2 工具调用率验证

| 指标 | 数值 |
|------|------|
| **工具调用率** | **100%** (5/5) ✅ |
| **复杂度评估准确率** | **100%** (5/5) ✅ |
| **端到端成功率** | **100%** (5/5) ✅ |
| 平均响应延迟 | 9.4s |

---

**文档生成时间**：2026年5月11日  
**分析项目**：jblmj-ai-agent-master (Spring AI)  
**目标项目**：langchain-business-trip-management (LangChain)
