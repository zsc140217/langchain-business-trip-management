# Spring AI项目分析提示词

## 📋 任务目标

请深入分析这个Spring AI企业差旅智能体项目，提取核心架构和实现细节，为后续用LangChain复刻做准备。

---

## 🎯 分析重点

### 1. 核心架构分析

请详细分析以下模块的实现：

#### **工作流编排器（WorkflowOrchestrator）**
- 路由策略：Skill优先 → 复杂度评估降级
- 如何处理SIMPLE/MEDIUM/COMPLEX三种复杂度
- 代码位置：`src/main/java/com/jblmj/aiagent/app/WorkflowOrchestrator.java`

#### **复杂度评估器（ComplexityAssessor）**
- 混合判断机制：80%规则 + 20%LLM
- 如何分类SIMPLE/MEDIUM/COMPLEX
- 关键词匹配逻辑
- 代码位置：`src/main/java/com/jblmj/aiagent/service/ComplexityAssessor.java`

#### **任务分解器（TaskDecomposer）**
- 如何将复杂查询分解为子任务
- JSON格式的子任务结构
- 依赖关系处理
- 代码位置：`src/main/java/com/jblmj/aiagent/service/TaskDecomposer.java`

#### **Skill系统**
- Skill的定义和注册机制
- `@SkillComponent`注解的作用
- Skill如何调用Service和Tool
- 代码位置：`src/main/java/com/jblmj/aiagent/skill/`

#### **三层记忆系统**
- 短期记忆（Layer 1）：文件存储 + 滑动窗口
- 工作记忆（Layer 2）：实体提取 + 意图追踪
- 长期记忆（Layer 3）：用户画像学习
- 代码位置：`src/main/java/com/jblmj/aiagent/chatmemory/`

#### **RAG优化**
- 三路召回：BM25 + Dense原始 + Dense改写
- RRF融合算法
- Cross-Encoder重排序
- 查询重写（口语化→结构化）
- 否定查询处理
- 代码位置：`src/main/java/com/jblmj/aiagent/rag/`

---

### 2. 关键实现细节

请提取以下信息：

#### **工作流编排的决策树**
```
用户查询
  ↓
Skill匹配？
  ├─ 是 → 执行Skill
  └─ 否 → 复杂度评估
           ├─ SIMPLE → 单工具调用
           ├─ MEDIUM → 多次工具调用
           └─ COMPLEX → 任务分解 → 并行执行
```

请详细说明每个分支的判断条件和执行逻辑。

#### **复杂度评估的规则**
- SIMPLE的判断条件（关键词数量、查询长度等）
- MEDIUM的判断条件
- COMPLEX的判断条件
- 何时触发LLM二次确认

#### **任务分解的Prompt模板**
- 如何让LLM生成结构化的子任务JSON
- 子任务的字段定义
- 依赖关系的表示方式

#### **记忆系统的工作流程**
- 对话历史如何存储和检索
- 实体提取的实现方式
- 用户画像如何更新

---

### 3. 代码示例提取

请提取以下关键代码片段：

#### **WorkflowOrchestrator的route方法**
```java
public String route(String query, String chatId) {
    // 请提取完整实现
}
```

#### **ComplexityAssessor的assess方法**
```java
public QueryComplexity assess(String query) {
    // 请提取完整实现
}
```

#### **TaskDecomposer的decompose方法**
```java
public List<SubTask> decompose(String query) {
    // 请提取完整实现
}
```

#### **Skill的注册和匹配逻辑**
```java
// SkillRegistry的关键方法
// Skill的canHandle实现
```

#### **三路召回的实现**
```java
// EnterpriseHybridRetriever的关键方法
// BM25检索
// Dense检索
// RRF融合
```

---

### 4. 配置和数据结构

请提取：

#### **application.yml的关键配置**
- 模型配置
- 向量存储配置
- API Key配置

#### **数据模型定义**
- `QueryComplexity`枚举
- `SubTask`类结构
- `ReActStep`类结构

#### **RAG文档结构**
- `document/`目录下的文档格式
- 元数据标注方式

---

### 5. 测试用例分析

请分析：

#### **RAGEvaluationTest**
- 30个测试用例的分类
- 否定查询的测试方法
- 准确率计算方式

#### **ComplexityFrameworkTest**
- 5个天气查询测试用例
- 工具调用率验证方法

---

## 📊 输出格式

请按以下格式输出分析结果：

### 1. 架构总览
```
[用Mermaid图或文字描述整体架构]
```

### 2. 核心模块详解
```
[每个模块的详细说明，包括：
- 功能描述
- 关键代码片段
- 设计思路
- 与其他模块的交互]
```

### 3. LangChain复刻建议
```
[针对每个模块，说明：
- Spring AI的实现方式
- LangChain应该如何实现
- 需要用到的LangChain组件
- 实现难点和注意事项]
```

### 4. 关键代码对比表
```
| 功能 | Spring AI实现 | LangChain对应组件 | 实现难度 |
|------|--------------|------------------|---------|
| 工作流编排 | WorkflowOrchestrator | ? | ? |
| 复杂度评估 | ComplexityAssessor | ? | ? |
| ... | ... | ... | ... |
```

---

## 🎯 最终目标

分析完成后，我需要能够：

1. **理解Spring AI项目的完整架构**
2. **知道每个功能的实现细节**
3. **清楚如何用LangChain复刻每个功能**
4. **了解两个框架的核心差异**

---

## 💡 额外要求

1. **重点关注工作流编排和复杂度评估**，这是项目的核心创新点
2. **详细分析三层记忆系统**，这是高级特性
3. **提取RAG优化的具体实现**，特别是三路召回和重排序
4. **说明Skill系统的设计理念**，这是架构亮点

---

## 📝 分析完成后

请生成一个完整的分析报告，保存为：
- `SPRING_AI_ANALYSIS.md` - 完整分析报告
- `LANGCHAIN_IMPLEMENTATION_PLAN.md` - LangChain实现计划

这样我就可以基于你的分析，在LangChain项目中实现对应的功能。

---

**开始分析吧！** 🚀
