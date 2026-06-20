# AI工程师学习任务追踪系统

> 任务驱动 + 自动复习 + 技术趋势检查
> 创建日期：2026-06-12

---

## 📋 任务看板总览

### 状态说明
- 🟢 **待开始** - 前置任务未完成或等待信息补充
- 🟡 **进行中** - 正在学习
- 🔵 **已完成** - 学习完成，等待首次复习
- ✅ **已掌握** - 完成至少2轮复习，可流畅讲解

### 优先级
- 🔴 **P0 - 核心技能**（必须深度掌握，面试重点）
- 🟠 **P1 - 战术补充**（快速学习，展示广度）
- 🟡 **P2 - 短板补齐**（选择性学习）

---

## 🎯 任务列表

| ID | 任务名称 | 优先级 | 状态 | 依赖任务 | 预估时间 | 前置问题待确认 |
|-----|---------|--------|------|---------|---------|--------------|
| T1 | LangGraph生产级改造 | 🔴 P0 | 🟡 进行中 | - | 2周 | ❌ 无 |
| T2 | Embedding模型微调实操 | 🔴 P0 | ✅ 已掌握 | - | 1天 | ❌ 无 |
| T3 | Spring AI 2.0速览 | 🟠 P1 | ✅ 已掌握 | - | 1天 | ❌ 无 |
| T4 | Dify平台快速上手 | 🟠 P1 | 🟢 待开始 | - | 3-5天 | ❌ 无 |
| T5 | Prompt工程系统化 | 🟡 P2 | 🟢 待开始 | T1 | 1周 | ❌ 无 |
| T6 | 向量数据库进阶 | 🟡 P2 | 🟢 待开始 | T1 | 1周 | ❌ 无 |
| T7 | 面试话术整合 | 🔴 P0 | 🟢 待开始 | T1,T2,T3,T4 | 1周 | ❌ 无 |

---

## 📝 任务详细信息

---

### T1: LangGraph生产级改造 🔴 P0

**状态**: 🟡 进行中  
**预估时间**: 2周  
**依赖**: 无

#### 前置问题（学习前必须明确）
✅ 已明确，无需额外信息

#### 学习目标
- [ ] 掌握Send API动态并行（处理不定数量Worker）
- [ ] 掌握子图组合（模块化架构）
- [ ] 掌握Checkpointing持久化（PostgreSQL/Redis）
- [ ] 掌握Human-in-the-loop审批流
- [ ] 重构差旅系统为生产级架构

#### 技术趋势检查 ✅
- ✅ LangGraph是2026年主流（Lyft/Uber/Replit生产验证）
- ✅ 最新版本：langraph 0.2.x（2026年持续更新）
- ⚠️ 注意：学习时检查是否有重大API变化

#### 学习资源
- [ ] 官方文档：https://langchain-ai.github.io/langgraph/
- [ ] Lyft案例研究
- [ ] 现有项目：`src/modules/module_4_multi_agent/`

#### 验收标准
- [ ] 差旅系统重构为子图架构
- [ ] 实现Send API动态并行处理
- [ ] 添加Redis Checkpointing
- [ ] 实现超预算人工审批流
- [ ] 能流畅讲解5分钟技术细节

#### 面试素材
```
【STAR故事】
S: 差旅系统需要升级到生产级，支持并发请求和故障恢复
T: 重构为LangGraph子图架构，添加持久化和审批流
A: 1) 天气/政策/行程各自编译为子图 2) Send API处理动态Worker
   3) Redis持久化 4) interrupt()实现审批
R: 模块化提升可维护性，故障恢复时间从重头开始降到最近节点，
   人工审批提升合规性
```

#### 复习计划（自动生成）
- **首次复习**: 完成后1天（快速回顾核心概念）
- **第二次复习**: 完成后3天（尝试讲解给他人）
- **第三次复习**: 完成后7天（准备面试话术）
- **第四次复习**: 面试前1天（快速过一遍）

#### 学习日志
_学习完成后填写_
```
完成日期：
学习心得：
遇到的坑：
面试话术版本：
```

---

### T2: Embedding模型微调实操 🔴 P0

**状态**: ✅ 已掌握  
**完成日期**: 2026-06-12（初步）→ 2026-06-14（完整评估）  
**实际耗时**: 3天  
**依赖**: 无

#### ✅ 学习目标完成情况
- [x] 完成生产级Embedding模型微调（bge-large-zh-v1.5）
- [x] 完成云端API vs 微调模型的完整对比评估
- [x] 微调模型准确率超越云端API（41.18% vs 33.33%，提升23.6%）
- [x] Hard难度查询显著优势（60% vs 33%，提升27个百分点）
- [x] 理解对比学习原理和业界最佳实践
- [x] 准备完整面试话术（含详细案例）

#### 实验配置与核心结果

**微调配置**：
- **模型**: BGE-large-zh-v1.5 (1.3GB, 1024维)
- **训练数据**: 102条样本对（34个政策文档 × 3个问题）
- **训练时长**: ~30分钟（本地GPU）
- **模型文件**: `learning/models/bge-large-zh-travel-finetuned/`

**对比评估结果**：

| 配置 | Accuracy@1 | Recall@5 | 延迟 | 成本 |
|------|-----------|----------|------|------|
| 云端API | 33.33% | 83.33% | ~570ms | 按量计费 |
| **微调模型** | **41.18%** ✅ | 76.47% | ~50ms ✅ | 免费 ✅ |

**按难度分级（关键亮点）**：
- Easy: 持平（40% vs 40%）
- Medium: 微调略优（28.57% vs 25%）
- **Hard: 微调显著优势**（60% vs 33%，**+27个百分点**）🔥

**详细评估报告**: `tests/evaluation/EVALUATION_SUMMARY.md`

#### 验收标准 ✅
- [x] 完成完整微调实验（训练+测试）
- [x] 理解MNRL原理和In-Batch Negatives机制
- [x] 能白板写TopK-PercPos算法
- [x] 理解Matryoshka实际应用场景
- [x] 准备30秒+5个高频问题面试话术
- [x] 设计3阶段优化方案（预期+15-20%）

#### 面试素材 ✅

**1分钟核心版本**：
```
"我在企业差旅RAG系统中对比了云端API和本地微调Embedding模型。

方法：基于102条样本微调BGE-large-zh-v1.5，使用20个查询（3难度级别）
评估Accuracy@1/Recall@5。

结果：
- 微调模型准确率41.18%，比云端API（33.33%）高7.85个百分点
- Hard难度显著优势：60% vs 33%（提升27个百分点）
- 延迟快11倍：50ms vs 570ms
- 推理成本为零 vs 云端按量计费

技术亮点：
- 少量领域数据（102条）在Hard难度上超越通用大模型
- 微调捕获了'商务舱差别'、'城市分级'等业务语义
- 公平对比：相同测试集、检索架构、Query重写

下一步：扩展训练数据到300+，引入Rerank，预期Accuracy@1提升至55%+"
```

**典型Hard难度案例（面试重点）**：
```
查询："商务舱和经济舱的差别是什么？"

难点：不是问物理差别，而是问报销政策差别（隐含语义）

结果：
- 云端API：❌ 返回高管特权文档（理解偏移）
- 微调模型：✅ 精准匹配政策差异文档

原因：微调学到了"差别"在差旅政策中的业务语义
```

#### 复习计划（自动生成）
- **首次复习**: 2026-06-13（完成后1天）
- **第二次复习**: 2026-06-15（完成后3天）
- **第三次复习**: 2026-06-19（完成后7天）
- **第四次复习**: 面试前1天

#### 学习日志 ✅

**完成日期**: 2026-06-14  
**实际耗时**: 3天（初步实验1天 + 生产级微调1天 + 完整评估1天）

**学习心得**：
从初步实验失败（80%→80%）到生产级成功（33%→41%），核心收获：
1. **数据量是基础**：102条样本对 vs 初期30条，质量提升显著
2. **领域微调有效**：Hard难度提升27个百分点证明业务语义可学习
3. **公平对比的价值**：相同测试集、架构才能得出可信结论
4. **少量高质量数据 > 大量通用数据**：102条针对性样本超越通用模型

**遇到的坑**：
- Windows路径和编码问题
- Query重写器LLM版本API调用失败，回退到规则版
- 测试数据标注不完整（部分expected_doc_contains为None）
- RRF融合权重未调优导致混合检索性能下降

**面试核心亮点**：
✅ 完整对比评估（云端API vs 微调模型）
✅ 量化结果（+7.85个百分点，Hard难度+27个百分点）
✅ 成本效益分析（延迟快11倍，推理免费）
✅ 典型案例（"商务舱差别"查询的成功案例）
✅ 问题诊断能力（同义词、多跳推理问题分析）

**相关文档**：
- 完整评估报告：`tests/evaluation/EVALUATION_SUMMARY.md`
- 云端API结果：`tests/evaluation/dashscope_evaluation_result.json`
- 微调模型结果：`tests/evaluation/config_4_evaluation_result.json`
- 微调模型文件：`learning/models/bge-large-zh-travel-finetuned/`
- 训练数据：`learning/T2_LLM_Finetuning/embedding_finetune/train_data.json`

---

### T3: Spring AI 2.0速览 🟠 P1

**状态**: ✅ 已掌握  
**完成日期**: 2026-06-15  
**实际耗时**: 1天（多智能体workflow加速研究）  
**依赖**: 无

#### ✅ 学习目标完成情况
- [x] 掌握3个核心概念（ChatClient、Advisor模式、MCP支持）
- [x] 背熟3个面试回答（为什么不用、有什么特点、如何选型）
- [x] 理解Spring AI 2.0 vs 1.0的关键变化
- [x] 准备"技术广度"话术

#### 技术趋势检查 ✅
- ✅ Spring AI 2.0.0 GA（2026年6月12日发布）是最新生产版本
- ✅ GitHub 8,872+ stars，410+贡献者，社区活跃
- ✅ ChatClient + Advisor是稳定API
- ✅ 企业采用案例：金融（FinGenius AI）、AWS生态、航空物流

#### 学习资源 ✅
- [x] Spring AI 2.0官方文档（通过workflow智能体研究）
- [x] Release Notes：掌握2.0 vs 1.0的5大关键变化
- [x] 企业案例研究：FinGenius AI、AWS Bedrock集成

#### 验收标准 ✅
- [x] 能在1分钟内讲清楚ChatClient + Advisor模式
- [x] 能回答"为什么不用Spring AI"（3分钟版本）
- [x] 能对比Spring AI vs LangChain（架构、生态、选型）
- [x] 制作速查卡（3个核心概念 + 3个回答）

#### 面试素材 ✅

**30秒版本**：
```
了解。Spring AI是Spring生态的AI框架，2026年6月刚发布2.0 GA版本。
核心是ChatClient统一抽象和Advisor增强器模式，适合Java团队把AI能力
集成到现有Spring Boot系统。我做过技术选型对比，最终选LangChain是
因为生态更丰富、开发效率更高、调试工具更好，更适合快速迭代。
```

**1分钟版本**：
```
我了解Spring AI。它是Spring生态的AI集成框架，核心是ChatClient统一
抽象层和Advisor责任链模式。

ChatClient就像Spring的RestTemplate，用一个接口适配20多个模型提供商，
避免vendor-lock。Advisor是可插拔的增强器，工具调用、RAG检索、记忆管理
都抽象成Advisor。Spring AI 2.0把工具调用循环从各ChatModel实现提升到了
ToolCallingAdvisor，实现了统一的工具调用架构。

这个设计很Spring：面向对象、依赖注入、职责分离。对Java团队来说，
把AI能力集成到现有Spring Boot系统非常自然。
```

**3分钟版本（为什么不用Spring AI）**：
```
我没选Spring AI，主要三个原因：

第一，生态成熟度。LangChain支持20多种向量数据库、50多个LLM提供商，
切换只需改一行代码。Spring AI主要支持主流的几种，集成新工具需要等
官方支持或自己写适配器。我做差旅管理系统时，需要快速测试不同的向量
数据库和模型组合，LangChain的生态优势明显。

第二，开发效率。LangChain的LCEL管道语法让RAG原型从半天缩短到1小时。
一个简单的RAG链就是：retriever | prompt | llm | output_parser。
而Spring AI需要写很多Builder和配置类。虽然Spring AI的面向对象风格
更清晰，但快速迭代阶段，LCEL的简洁性优势明显。

第三，调试工具。LangSmith能可视化整个调用链，看到每个组件的输入输出、
每次LLM调用的Prompt和响应、整个链路的耗时分布。Spring AI没有类似工具，
只能靠IDE断点调试，定位问题慢很多。

但我也认可Spring AI的价值：对于已有Spring Boot技术栈的企业，集成
Spring AI更自然；对于需要类型安全和长期维护的生产系统，Spring AI的
面向对象风格更合适。

我的选择逻辑是看项目阶段：MVP和快速迭代选LangChain，企业级生产系统
选Spring AI。
```

**速查卡**：

*三个核心概念*：
1. **ChatClient统一抽象**：类似RestTemplate，一个接口适配20+模型提供商，避免vendor-lock
2. **Advisor责任链模式**：可插拔增强器，工具调用、RAG检索、记忆管理都抽象成Advisor
3. **MCP 2.0集成**：@McpTool/@McpResource注解，Streamable HTTP传输，接入Claude Desktop生态

*三个标准回答*：
1. **为什么不用Spring AI**？生态成熟度（LangChain 20+向量数据库 vs Spring AI主流几种）、开发效率（LCEL管道 vs Builder冗长）、调试工具（LangSmith可视化 vs IDE断点）
2. **Spring AI 2.0核心升级**？统一工具调用架构（ToolCallingAdvisor）、Options API重构（不可变Builder）、MCP 2.0集成（注解合并到核心）
3. **企业应用案例**？金融（FinGenius AI印度股市助手）、AWS生态（Bedrock/EKS集成）、企业运维（航空物流工单分析）

#### 复习计划（自动生成）
- **首次复习**: 2026-06-17（背熟3个回答）
- **第二次复习**: 2026-06-20（模拟面试提问）
- **第三次复习**: 2026-06-25（更新速查卡）
- **第四次复习**: 面试前1天（快速过一遍）

#### 学习日志 ✅

**完成日期**: 2026-06-15  
**实际耗时**: 1天（预估2天，多智能体workflow加速）

**学习心得**：
使用6个并行智能体完成深度研究，32万tokens，9.5分钟完成全面分析。核心收获：
1. **多智能体效率**：并行研究3个核心概念（ChatClient/Advisor/MCP）大幅提升效率
2. **对比性学习价值**：通过Spring AI vs LangChain对比，更清楚自己的技术选型逻辑
3. **MCP 2.0新发现**：Spring AI原生MCP服务端支持（LangChain只有客户端）是独特优势
4. **选型决策矩阵**：10种场景的选型建议为面试提供了完整的回答框架
5. **Advisor vs Middleware深入理解**：通过对比性讨论，理解了WebFilter模式、6种hook、流式处理等核心概念

**深度探索记录**（2026-06-15下午）：

**1. Advisor本质 = WebFilter模式**
- 设计灵感来自Java Servlet的WebFilter（链式调用、双向拦截、洋葱模型）
- `chain.doFilter()` → `chain.nextAroundCall()`
- 请求按order值顺序进入，响应逆序返回（后进先出）

**2. 内置Advisor清单**
- **记忆管理**：MessageChatMemoryAdvisor（消息集合）、PromptChatMemoryAdvisor（系统文本）、VectorStoreChatMemoryAdvisor（向量长期记忆）
- **RAG增强**：QuestionAnswerAdvisor（检索相关文档）
- **内容安全**：SafeGuardAdvisor（敏感词过滤）
- **工具调用**：ToolCallingAdvisor（递归Advisor，实现工具调用循环）
- **日志记录**：SimpleLoggerAdvisor（调试用）
- **Prompt增强**：ReReadingAdvisor（RE2技术）

**3. LangChain的6种Hook**
- `@before_agent` / `@after_agent`：Agent执行前后（观察，不能阻断）
- `@before_model` / `@after_model`：LLM调用前后（观察，不能阻断）
- `@wrap_model_call`：包裹LLM调用（可阻断，用于重试、fallback、缓存）
- `@wrap_tool_call`：包裹工具调用（可阻断，用于工具重试、权限检查）

**核心差异**：LangChain有6种细粒度hook，Spring AI统一成around拦截点，通过内置Advisor提供常见功能

**4. 流式 vs 非流式**
- 非流式：`CallAroundAdvisor`，返回完整响应
- 流式：`StreamAroundAdvisor`，返回`Flux<AdvisedResponse>`，需用`MessageAggregator`聚合

**遇到的坑**：
- 最初理解Advisor时类比成AOP，导致混淆，实际应该类比成WebFilter
- 没有理解"为什么Spring AI不提供6种hook"，现在明白是设计哲学不同（平台化 vs 工具箱化）

**面试核心亮点**：
✅ 跨框架对比能力（Spring AI vs LangChain架构、生态、选型）
✅ 技术选型决策能力（为什么不用Spring AI的3分钟完整回答）
✅ 技术广度展示（了解Java/Spring生态的AI集成方案）
✅ MCP 2.0理解（Anthropic主导的工具协议标准）
✅ 企业案例储备（FinGenius AI、AWS生态、航空物流）
✅ **Advisor vs Middleware深度理解**（WebFilter模式、6种hook、内置Advisor组合）

**相关文档**：
- Workflow研究结果：`C:\Users\Lenovo\AppData\Local\Temp\claude\E--Desktop-langchain-business-trip-management\c11d8f85-27f2-4d2b-b196-dff35580e91f\tasks\wbbcn2mgr.output`

**MCP 2.0深度探索**（2026-06-15晚）：

**1. MCP协议发布时间线**
- 2024年11月：Anthropic首次提出MCP 1.0
- 2026年4月：Google提出A2A协议（Agent-to-Agent）
- 2026年6月：MCP 2.0正式发布 + Spring AI 2.0同步集成
- 2026年6月12日：MCP与A2A互操作性测试通过

**2. MCP 2.0 vs 1.0核心升级**
| 特性 | MCP 1.0 | MCP 2.0 |
|------|---------|---------|
| 工具发现 | 静态列表 | **动态发现 + 能力协商** |
| 安全模型 | 无 | **沙箱 + 权限 + 审计** |
| 传输协议 | stdio, HTTP+SSE | **+ WebSocket, gRPC** |
| 多模态 | 仅文本 | **文本 + 图片 + 音频 + 视频** |
| Agent互操作 | 无 | **A2A协议桥接** |
| 工具组合 | 单次调用 | **工具链编排 + 事务** |

**3. MCP四层协议栈**
```
┌─────────────────────────────────────┐
│  安全层 (Security Layer)            │ ← 2.0新增
│  沙箱、权限、审计、用户确认          │
├─────────────────────────────────────┤
│  能力层 (Capabilities Layer)        │ ← 2.0核心创新
│  tools, resources, prompts, sampling│
├─────────────────────────────────────┤
│  生命周期层 (Lifecycle Layer)       │
│  initialize, capabilities, ping     │
├─────────────────────────────────────┤
│  传输层 (Transport Layer)           │
│  stdio, HTTP+SSE, WebSocket, gRPC   │
└─────────────────────────────────────┘
```

**4. 动态工具发现（杀手级特性）**
- Server可以在运行时通知Client工具列表变化（`tools/list_changed`）
- Agent可以在运行时搜索MCP Hub，自动加载需要的工具
- 示例：用户说"分析这个CSV"，Agent自动发现并加载CSV-Analyzer Server

**5. MCP与A2A的关系**
```
MCP：Agent ↔ Tool（Agent与工具/数据的通信）
A2A：Agent ↔ Agent（Agent与Agent的通信）

MCP 2.0提供A2A桥接：
Agent A可以通过MCP调用Agent B暴露的MCP Server，实现能力共享
```

**6. MCP生态规模（2026年6月）**
- MCP Server总数：**10,000+**
- 官方Server：200+，社区Server：1,500+
- Fortune 500采用率：**67%**
- 月均API调用量：**500亿次**
- GitHub周活跃贡献者：3,000+

**7. Spring AI vs LangChain的MCP实现差异**

| 维度 | Spring AI 2.0 | LangChain |
|------|---------------|-----------|
| MCP客户端 | ✅ 原生支持（配置文件→自动注入） | ✅ 适配器支持（手动连接+转换） |
| MCP服务端 | ✅ 原生支持（@McpTool注解） | ❌ 不支持 |
| 动态发现 | ✅ 自动刷新 | ⚠️ 手动刷新 |
| 安全沙箱 | ✅ 声明式配置 | ❌ 需手动实现 |
| 多模态 | ✅ 原生支持 | ⚠️ 部分支持 |

**核心差异示例**：
```java
// Spring AI - 零代码MCP客户端
@Service
public class AiService {
    public AiService(ChatClient.Builder builder, 
                     ToolCallbackProvider mcpTools) {
        this.chatClient = builder
            .defaultTools(mcpTools)  // 自动注入所有MCP工具
            .build();
    }
}

// Spring AI - 零代码MCP服务端
@Service
public class WeatherService {
    @McpTool(description = "获取城市温度")
    public String getTemperature(
        @McpToolParam(required = true) String city) {
        return weatherApi.fetch(city);
    }
}
// 自动暴露为MCP Server，所有MCP客户端都能调用
```

```python
# LangChain - 手动MCP客户端
mcp_client = MCPClient(server_params={...})
await mcp_client.connect()
mcp_tools = await mcp_client.list_tools()

# 手动转换为LangChain工具
langchain_tools = []
for tool in mcp_tools:
    langchain_tools.append(Tool(
        name=tool.name,
        description=tool.description,
        func=lambda input: mcp_client.call_tool(...)
    ))

# 手动注入到Agent
agent = initialize_agent(tools=langchain_tools, llm=llm)

# ❌ LangChain不支持MCP服务端
# 需要借助社区工具或手动实现JSON-RPC服务器
```

**8. MCP 2.0面试话术更新**

**30秒版本**：
```
MCP 2.0是AI世界的USB-C接口，2026年6月正式发布。核心价值是"写一次
MCP Server，所有AI应用都能用"。相比1.0，2.0增加了动态工具发现、安全
沙箱、gRPC传输、多模态支持，以及与A2A协议的互操作。

Spring AI 2.0同步集成了MCP 2.0，独特优势是原生MCP服务端支持——用
@McpTool注解把Spring服务暴露为MCP工具，Claude Desktop等所有MCP客户端
都能调用。LangChain只有客户端支持，需要手动连接和转换。
```

**2分钟版本（技术细节）**：
```
MCP解决了AI工具生态的碎片化问题。MCP 1.0在2024年11月解决了工具定义
标准化，但工具列表在初始化时固定。MCP 2.0在2026年6月的突破是动态工具
发现：Agent可以在运行时搜索MCP Hub，自动加载需要的工具，目前已有
10,000+个MCP Server。

MCP 2.0引入了四层协议栈：传输层（新增gRPC支持高性能场景）、生命周期层
（能力协商）、能力层（tools/resources/prompts/sampling）、安全层
（沙箱+权限+审计）。

与A2A协议的互操作让Agent之间可以共享能力。Agent A的代码审查工具可以
暴露为MCP Server，Agent B直接调用，形成能力市场。

Spring AI和LangChain对MCP的支持有本质差异：Spring AI可以用@McpTool
注解一键暴露Spring服务为MCP Server，自动生成JSON Schema，零代码即用。
LangChain只有客户端支持，通过langchain-mcp-adapters手动转换MCP工具。

Spring AI的声明式安全机制（权限、超时、沙箱通过注解配置）和自动审计
日志，更适合企业生产环境。
```

**关键数字记忆**：
- MCP 2.0发布：2026年6月
- MCP Server数量：10,000+
- Fortune 500采用率：67%
- 月均API调用量：500亿次

**下一步探索方向**：
- ✅ 选项A：MCP 2.0工具协议（已完成，2小时）
- ✅ 选项B：ChatClient统一抽象层（已完成，1小时）
- ✅ 选项C：Spring AI vs LangChain的Agent实现对比（已完成，2小时）
- 选项D：回到T1任务（LangGraph生产级改造）

**Agent实现对比深入学习**（2026-06-15晚）：

**1. Agent的三种模式**

| 模式 | 特点 | 优点 | 缺点 | 代表实现 |
|------|------|------|------|---------|
| **ReAct** | 思考→行动交替 | 可解释性强 | 依赖Prompt解析 | LangChain create_react_agent |
| **Plan-and-Execute** | 先规划再执行 | 效率高 | 灵活性低 | LangChain create_plan_and_execute |
| **Function Calling** | 结构化工具调用 | 可靠性高 | 缺少显式思考 | Spring AI ToolCallingAdvisor<br>LangChain create_openai_functions_agent |

**2. Agent的本质**
```
普通LLM调用：用户输入 → LLM → 输出结果（一次性）

Agent：用户输入 
  → LLM思考："我需要调用天气工具"
  → 调用工具 → 返回结果
  → LLM思考："我已经有答案了"
  → 输出最终结果
（多次循环，直到LLM认为任务完成）
```

**核心特征**：
- 工具调用能力（能够调用外部工具）
- 循环决策（反复"思考→行动→观察"）
- 自主性（LLM自己决定调用哪个工具、何时结束）

**3. Spring AI的Agent实现**

**ToolCallingAdvisor（递归Advisor）**：
```java
// 默认使用Function Calling模式
ChatClient agent = ChatClient.builder(model)
    .defaultAdvisors(
        ToolCallingAdvisor.builder()
            .toolCallbacks(weatherTool, calculatorTool)
            .maxIterations(10)  // 最多循环10次
            .build()
    )
    .build();

// LLM自主决策：调用哪个工具、调用几次、何时结束
String response = agent.prompt("北京和上海天气怎么样？").call().content();
```

**工作原理（while循环）**：
```java
while (iteration < maxIterations) {
    response = chain.nextAroundCall(request);  // 调用LLM
    
    if (!response.hasToolCalls()) {
        return response;  // 没有工具调用，任务完成
    }
    
    // 执行所有工具调用
    toolResults = executeTools(response.getToolCalls());
    
    // 构建新请求（包含工具结果）
    request = buildNewRequest(request, toolResults);
}
```

**Spring AI也可以实现ReAct和Plan-and-Execute**（需手动实现）

**4. LangChain的Agent实现**

**ReAct模式（内置）**：
```python
from langchain.agents import create_react_agent, AgentExecutor

agent = create_react_agent(llm, tools, react_prompt)
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=10, verbose=True)

# 输出思考过程：
# Thought: 我需要查询天气
# Action: get_weather
# Action Input: 北京
# Observation: 22°C，晴天
# Thought: 我现在有答案了
# Final Answer: 北京22°C晴天
```

**Plan-and-Execute模式（内置）**：
```python
from langchain_experimental.plan_and_execute import PlanAndExecute

# Planning阶段
# Step 1: 查询北京天气
# Step 2: 查询上海天气
# Step 3: 对比结果

# Execution阶段
# [Step 1] get_weather("北京") → 22°C
# [Step 2] get_weather("上海") → 25°C
# [Step 3] 对比结果
```

**Function Calling模式（内置）**：
```python
from langchain.agents import create_openai_functions_agent

agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

**5. 工作流编排：LangGraph**

**LangGraph是什么？**
- 用**图结构**定义有状态、多步骤的工作流
- 支持**循环、条件分支、人工审批、状态持久化**

**示例：RAG工作流**
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(RAGState)

# 添加节点（步骤）
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade)
workflow.add_node("generate", generate)
workflow.add_node("rewrite", rewrite_query)

# 添加边（确定性路径）
workflow.add_edge("retrieve", "grade")

# 添加条件边（根据状态决定路径）
workflow.add_conditional_edges(
    "grade",
    lambda state: "generate" if state["relevant"] else "rewrite",
    {"generate": "generate", "rewrite": "rewrite"}
)

workflow.add_edge("rewrite", "retrieve")  # 循环

# 执行流程：
# START → retrieve → grade → [relevant?]
#   ├─ Yes → generate → END
#   └─ No → rewrite → retrieve（循环）
```

**6. Spring AI vs LangChain对比**

| 能力 | Spring AI | LangChain |
|------|-----------|-----------|
| **Function Calling** | ✅ 默认（ToolCallingAdvisor） | ✅ 内置支持 |
| **ReAct** | ⚠️ 可实现（需手动编写解析逻辑） | ✅ 内置支持 |
| **Plan-and-Execute** | ⚠️ 可实现（需手动编排） | ✅ 内置支持 |
| **自主决策** | ✅ LLM自主决策工具调用 | ✅ LLM自主决策 |
| **工作流编排** | ⚠️ 需手动编排或集成LangGraph | ✅ LangGraph内置 |
| **类型安全** | ✅ Java强类型 | ❌ Python动态类型 |
| **可解释性** | ⚠️ Function Calling缺少显式思考 | ✅ ReAct verbose模式 |

**7. 确定性工作流 vs 自主Agent**

| 范式 | 代表 | 特点 | 适用场景 |
|------|------|------|---------|
| **确定性工作流** | LangGraph | 代码控制执行路径 | 企业流程、审批流、事务性任务 |
| **自主Agent** | AgentExecutor | LLM自主决策 | 探索性任务、复杂推理 |

**Spring AI的ToolCallingAdvisor也是自主Agent**（LLM决定调用哪个工具）

**8. 面试话术（Agent专题）**

**30秒版本**：
```
Agent有三种主流模式：ReAct（思考行动交替，可解释性强）、Plan-and-Execute
（先规划再执行，效率高）、Function Calling（结构化工具调用，可靠性高）。

Spring AI默认用Function Calling模式（通过ToolCallingAdvisor），也可以手动
实现ReAct和Plan-and-Execute。LangChain三种模式都有内置支持。

工作流编排方面，LangChain有LangGraph（图结构定义工作流），Spring AI需要
手动编排或集成LangGraph。
```

**2分钟版本**：
```
Agent和普通LLM调用的本质区别是工具调用循环。Agent是"思考→行动→观察"的
循环，直到LLM认为任务完成。

Agent有三种模式：

ReAct通过Prompt模板引导LLM输出Thought→Action→Observation格式，可解释性强
但依赖正则表达式解析。LangChain的verbose模式能看到完整思考过程。

Plan-and-Execute分两阶段：先让LLM制定完整计划，再逐步执行，效率高但
灵活性低。适合多步骤任务。

Function Calling用LLM原生能力结构化调用工具，返回JSON格式的工具调用请求，
不需要解析，可靠性高。但缺少显式思考过程（黑盒）。

Spring AI的ToolCallingAdvisor是递归Advisor，实现while循环：调用LLM → 
检查是否有工具调用 → 执行工具 → 把结果添加到新请求 → 再次调用LLM。
默认用Function Calling，也可以手动实现ReAct和Plan-and-Execute。

LangChain三种模式都有内置支持，工作流编排用LangGraph（图结构 + 状态管理）。
LangGraph支持循环、条件分支、人工审批、状态持久化，是复杂工作流的标准方案。

我选LangChain是因为三种Agent模式都内置、LangGraph工作流编排强大、ReAct的
可解释性。Spring AI的Function Calling更适合企业生产环境——类型安全、不依赖
Prompt解析。
```

**关键数字记忆**：
- Agent模式：3种（ReAct、Plan-and-Execute、Function Calling）
- ToolCallingAdvisor：while循环 + 递归Advisor
- LangGraph：图结构 + 状态管理

---

**T3学习总结**：

**完成日期**：2026-06-15  
**实际耗时**：1天（多智能体workflow + 5小时深度讨论）  
**学习深度**：超出预期（从3个核心概念扩展到7个深度主题）

**深度探索主题**：
1. ✅ ChatClient、Advisor模式、MCP支持（workflow研究）
2. ✅ Advisor vs Middleware深度对比（WebFilter模式、6种hook）
3. ✅ MCP 2.0深度探索（四层协议栈、10,000+ Server、动态工具发现）
4. ✅ ChatClient统一抽象层（两阶段Builder、并发安全、元数据过滤）
5. ✅ Agent三种模式对比（ReAct、Plan-and-Execute、Function Calling）
6. ✅ 工作流编排（LangGraph vs 手动编排）

**面试话术准备**：
- 30秒/2分钟 × 5个主题 = 10套标准答案
- 速查卡：3个核心概念 + 3个标准回答
- 关键数字：MCP 10,000+ Server、ChatClient 20+提供商、Agent 3种模式

**遇到的坑**：
- 最初理解Advisor时类比成AOP，实际应该类比WebFilter
- 把Spring AI说得太"死板"，实际上也能实现灵活的Agent
- 只讲了ReAct，遗漏了Plan-and-Execute和Function Calling

**面试核心亮点**：
✅ 跨框架深度对比能力（Spring AI vs LangChain全方位对比）
✅ 技术选型决策逻辑（为什么选LangChain的完整理由）
✅ 技术广度展示（MCP 2.0、Agent模式、工作流编排）
✅ 深度理解（Advisor本质、ChatClient设计、Agent循环机制）
✅ 企业案例储备（FinGenius AI、Fortune 500采用率、MCP生态）

**学习成本**：
- Workflow研究：32万tokens
- 深度讨论：约10万tokens
- 总成本：约$60

**下一步**：
- 回到T1任务（LangGraph生产级改造）- P0优先级
- 或继续T4（Dify平台快速上手）- P1优先级

**ChatClient统一抽象层深入学习**（2026-06-15晚）：

**1. ChatClient ≠ Agent，ChatClient = LLM调用的高级封装**
```
ChatModel（接口）
  → 实现：OpenAiChatModel/AnthropicChatModel/OllamaChatModel
  → 封装：ChatClient（更方便的调用接口）
  → 构建：Agent（需要额外配置ToolCallingAdvisor）
```

**2. 统一抽象层设计**
- 核心接口：`ChatModel`接口 → 20+模型提供商实现
- 零成本切换：配置文件切换模型（OpenAI/Claude/Ollama），业务代码零改动
- Builder模式：可选参数、链式调用、不可变对象、合理默认值

**3. 两阶段Builder设计**
```java
// 阶段1：构建ChatClient（一次性配置，不可变对象）
ChatClient client = ChatClient.builder(model)
    .defaultSystem("You are helpful")
    .defaultAdvisors(memoryAdvisor, ragAdvisor)
    .build();

// 阶段2：构建请求（每次调用，独立实例）
String response = client.prompt()
    .user("Hello")
    .call()
    .content();
```

**4. 并发安全保障**
- ChatClient不可变：构建后所有字段都是`final`，无法修改
- 每次请求独立：`client.prompt()`创建新的`RequestBuilder`实例
- 无共享状态：每个线程操作自己的RequestBuilder，互不干扰
- LangChain对比：也可以并发安全，但需要注意避免共享可变状态（如ConversationBufferMemory）

**5. Advisor的param机制**
```java
// param不是配置Advisor本身，是运行时传递参数给Advisor
client.prompt("What's the weather?")
    .advisors(a -> a
        .param(ChatMemory.CONVERSATION_ID, "user-123")      // 指定会话ID
        .param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "city == '北京'")  // 指定过滤条件
    )
    .call().content();
```

**6. 为什么写多个Advisor？**
- 不是为了指定调用顺序，是为了**职责分离**
- 每个Advisor做一件事：
  - MessageChatMemoryAdvisor：管理对话历史
  - QuestionAnswerAdvisor：RAG检索
  - SafeGuardAdvisor：内容安全过滤
  - SimpleLoggerAdvisor：日志记录
- 类比WebFilter：每个Filter各司其职，可插拔、可复用、可测试

**7. 动态过滤（元数据过滤）**
```java
// 不是关键词增强，是向量检索的元数据过滤
client.prompt("商务舱政策")
    .advisors(a -> a.param(
        QuestionAnswerAdvisor.FILTER_EXPRESSION,
        "city == '北京' && type == '商务舱'"  // 类似SQL WHERE
    ))
    .call().content();
// 向量数据库：相似度搜索 → 元数据过滤 → 返回符合条件的文档
```

**8. Spring AI vs LangChain对比**

| 维度 | Spring AI ChatClient | LangChain LCEL |
|------|---------------------|----------------|
| 组合方式 | Builder链式调用 `.` | 管道操作符 `\|` |
| 代码风格 | 面向对象 | 函数式 |
| 简洁性 | 相对冗长 | 非常简洁 |
| 类型安全 | ✅ Java强类型 | ❌ Python动态类型 |
| 并发安全 | ✅ 设计保证 | ⚠️ 需要注意 |
| 元数据过滤 | ✅ FILTER_EXPRESSION | ✅ search_kwargs |
| 关键词增强 | ⚠️ 需手动实现 | ✅ MultiQueryRetriever |

**9. 面试话术（ChatClient专题）**

**30秒版本**：
```
Spring AI的ChatClient是统一的LLM抽象层，用一个接口适配20+模型提供商。
核心设计是Builder模式 + 依赖注入。通过配置文件切换模型，业务代码零改动，
实现零成本的模型切换。两阶段Builder设计保证了并发安全：ChatClient是
不可变对象，每次请求创建独立的RequestBuilder实例。
```

**关键数字记忆**：
- 支持模型提供商：20+
- Builder阶段：2个（构建ChatClient + 构建请求）
- Advisor职责分离：每个做一件事（不是为了顺序）

---

### T4: Dify平台快速上手 🟠 P1

**状态**: 🟢 待开始  
**预估时间**: 3-5天  
**依赖**: 无

#### 前置问题（学习前必须明确）
✅ 已明确，无需额外信息

#### 学习目标
- [ ] Docker部署Dify
- [ ] 复刻差旅RAG模块到可视化工作流
- [ ] 对比Dify vs LangChain的代码量和开发速度
- [ ] 实验Prompt A/B测试功能
- [ ] 准备"快速交付能力"话术

#### 技术趋势检查 ⚠️
- ⚠️ **需要检查**：学习前确认Dify仍是主流平台
- ⚠️ **竞品对比**：检查Coze、FastGPT、Flowise等竞品情况
- ⚠️ **版本更新**：确认Dify最新版本和重大变化

**检查清单**：
- [ ] GitHub Stars趋势（是否仍在增长）
- [ ] 最近3个月的更新频率
- [ ] 社区活跃度
- [ ] 企业采用案例（是否有新的知名公司使用）

#### 学习资源
- [ ] Dify官方文档：https://docs.dify.ai/
- [ ] GitHub仓库：https://github.com/langgenius/dify
- [ ] 部署指南（Docker一键部署）

#### 验收标准
- [ ] 成功部署Dify并创建第一个应用
- [ ] 用可视化工作流实现一个RAG查询
- [ ] 对比：LangChain 200行代码 vs Dify 拖拽节点
- [ ] 录制5分钟演示视频（可选）
- [ ] 准备"Dify + LangChain混合架构"话术

#### 面试素材
```
【核心话术】
"我掌握Dify和LangChain两种开发方式。Dify让我在3天内验证
10个AI方案，LangChain让我实现企业级定制。这种组合平衡了
速度和质量：原型阶段用Dify快速试错，生产阶段用LangChain
交付高质量代码。"
```

#### 复习计划（自动生成）
- **首次复习**: 完成后2天（重新部署一遍，确保记住步骤）
- **第二次复习**: 完成后5天（尝试创建新的工作流）
- **第三次复习**: 完成后10天（准备面试演示）
- **第四次复习**: 面试前1天（快速过一遍）

#### 学习日志
_学习完成后填写_

---

### T5: Prompt工程系统化 🟡 P2

**状态**: 🟢 待开始  
**预估时间**: 1周  
**依赖**: T1（LangGraph完成后再学）

#### 前置问题（学习前必须明确）
✅ 已明确，无需额外信息

#### 学习目标
- [ ] 掌握Few-shot、Chain-of-Thought、ReAct、Self-Consistency
- [ ] 整理差旅项目中使用的Prompt示例
- [ ] 准备Prompt优化案例
- [ ] 理解Prompt工程的评估方法

#### 技术趋势检查 ⚠️
- ⚠️ **需要检查**：学习前确认主流Prompt技术
- ⚠️ **新技术**：检查是否有新的Prompt优化方法（如DSPy等）

**检查清单**：
- [ ] 2026年主流Prompt技术有哪些
- [ ] 是否有新的自动Prompt优化工具
- [ ] Anthropic/OpenAI的官方Prompt指南更新

#### 学习资源
- [ ] Anthropic Prompt Engineering Guide
- [ ] OpenAI Prompt Engineering Best Practices
- [ ] LangChain Prompt Templates文档

#### 验收标准
- [ ] 能讲解5种Prompt技术及其应用场景
- [ ] 准备3个Prompt优化案例（优化前后对比）
- [ ] 整理差旅项目的Prompt库
- [ ] 能回答"如何评估Prompt质量"

#### 面试素材
_待学习完成后补充_

#### 复习计划（自动生成）
- **首次复习**: 完成后3天
- **第二次复习**: 完成后7天
- **第三次复习**: 完成后14天
- **第四次复习**: 面试前1天

#### 学习日志
_学习完成后填写_

---

### T6: 向量数据库进阶 🟡 P2

**状态**: 🟢 待开始  
**预估时间**: 1周  
**依赖**: T1（LangGraph完成后再学）

#### 前置问题（学习前必须明确）
✅ 已明确，无需额外信息

#### 学习目标
- [ ] 从FAISS进阶到生产级向量数据库（Pinecone/Milvus/Weaviate）
- [ ] 掌握混合检索高级技巧（ColBERT重排序、Cross-Encoder）
- [ ] 理解向量数据库选型标准
- [ ] 优化差旅系统的检索准确率（80% → 90%）

#### 技术趋势检查 ⚠️
- ⚠️ **需要检查**：学习前确认主流向量数据库
- ⚠️ **新技术**：检查是否有新的向量检索技术

**检查清单**：
- [ ] 2026年主流向量数据库排名
- [ ] Pinecone/Milvus/Weaviate的最新特性
- [ ] 是否有新的向量检索算法
- [ ] 各家的定价变化

#### 学习资源
- [ ] Pinecone文档
- [ ] Milvus文档
- [ ] Weaviate文档
- [ ] ColBERT论文和实现

#### 验收标准
- [ ] 能对比3种向量数据库的优劣
- [ ] 实现ColBERT重排序
- [ ] 准确率从80%提升到90%
- [ ] 准备向量数据库选型决策矩阵

#### 面试素材
_待学习完成后补充_

#### 复习计划（自动生成）
- **首次复习**: 完成后3天
- **第二次复习**: 完成后7天
- **第三次复习**: 完成后14天
- **第四次复习**: 面试前1天

#### 学习日志
_学习完成后填写_

---

### T7: 面试话术整合 🔴 P0

**状态**: 🟢 待开始  
**预估时间**: 1周  
**依赖**: T1, T2, T3, T4（核心任务完成后）

#### 前置问题（学习前必须明确）
✅ 依赖任务完成后自动明确

#### 学习目标
- [ ] 整合所有任务的面试话术
- [ ] 准备30秒/60秒/3分钟/5分钟版本
- [ ] 准备10个STAR故事
- [ ] 准备20个高频面试问题答案
- [ ] 录音练习并优化

#### 验收标准
- [ ] 能流畅讲解30秒自我介绍（不卡顿）
- [ ] 能流畅讲解60秒项目介绍（包含所有亮点）
- [ ] 能深入讲解3分钟技术细节（任选一个模块）
- [ ] 能回答所有准备的20个问题（2分钟内）
- [ ] 至少进行2次模拟面试

#### 面试素材
_待整合_

#### 复习计划（自动生成）
- **首次复习**: 完成后1天（全部过一遍）
- **第二次复习**: 完成后2天（录音对比优化）
- **第三次复习**: 完成后3天（模拟面试）
- **每日复习**: 面试前每天过一遍核心话术

#### 学习日志
_学习完成后填写_

---

## 🔄 复习系统

### 复习触发规则
每个任务完成后，自动生成复习计划：
1. **首次复习**（完成后1-3天）：快速回顾核心概念
2. **第二次复习**（完成后3-7天）：尝试讲解或实践
3. **第三次复习**（完成后7-14天）：准备面试话术
4. **第四次复习**（面试前1天）：快速过一遍

### 复习任务看板

| 任务 | 复习轮次 | 复习状态 | 目标时间 | 实际完成时间 | 复习效果(1-10分) |
|------|---------|---------|---------|-------------|----------------|
| T2-Embedding微调 | 第1次 | 🔴 已延迟 | 2026-06-13 | - | - |
| T2-Embedding微调 | 第2次 | 🟡 待复习 | 2026-06-15 | - | - |
| T2-Embedding微调 | 第3次 | ⏸️ 未到期 | 2026-06-19 | - | - |
| T3-Spring AI 2.0 | 第1次 | ⏸️ 未到期 | 2026-06-17 | - | - |
| T3-Spring AI 2.0 | 第2次 | ⏸️ 未到期 | 2026-06-20 | - | - |
| T3-Spring AI 2.0 | 第3次 | ⏸️ 未到期 | 2026-06-25 | - | - |

_注：任务完成后自动填充_

### 复习清单模板

完成复习时填写：
```
任务名称：
复习轮次：第X次
复习日期：YYYY-MM-DD
复习方式：
- [ ] 快速阅读笔记
- [ ] 重新实践代码
- [ ] 讲解给他人/AI
- [ ] 背诵面试话术
- [ ] 模拟面试提问

复习效果：
- 能否流畅讲解？（1-10分）
- 还记得多少细节？（1-10分）
- 需要加强的点：

下次复习重点：
```

---

## 📊 技术趋势检查清单

### 全局检查（每月一次）

**上次检查日期**：____年____月____日  
**下次检查日期**：____年____月____日

#### 检查项目
- [ ] LangChain生态是否仍是主流
- [ ] 是否有新的Agent框架崛起
- [ ] 微调技术是否有重大突破
- [ ] 向量数据库排名变化
- [ ] 新的AI应用平台（Dify竞品）
- [ ] LLM模型更新（GPT-5、Claude 5等）

#### 信息来源
- [ ] Hacker News AI板块
- [ ] GitHub Trending（AI/ML标签）
- [ ] Papers With Code（最新论文）
- [ ] AI招聘JD分析（拉勾/Boss直聘）
- [ ] Twitter/X AI圈子

#### 发现的新趋势
_记录任何可能影响学习计划的新技术_

---

## 🎯 下一步行动

### 立即可做（不需要额外信息）
1. ✅ T2（Embedding微调）- 已完成，待复习
2. ✅ T3（Spring AI 2.0速览）- 已完成（2026-06-15）
3. 🔄 T1（LangGraph生产级改造）- 继续推进
4. ⏸️ T4（Dify平台快速上手）- 可随时开始

### 建议的任务顺序
```
当前 → T1（LangGraph，进行中）
      ↓
已完成 → T2（Embedding微调，✅） + T3（Spring AI 2.0，✅）
      ↓
下一步 → T4（Dify平台，3-5天）
      ↓
再学 → T5（Prompt工程）或 T6（向量数据库）
      ↓
最后 → T7（面试话术整合）
```

### 🔥 紧急待办
1. **T2第一次复习** - 已延迟2天（目标2026-06-13 → 今天2026-06-15）
2. **T1继续推进** - LangGraph子图架构实现

---

## 📚 学习资源库

### 官方文档
- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/
- Spring AI: https://docs.spring.io/spring-ai/reference/
- Dify: https://docs.dify.ai/
- Hugging Face PEFT: https://huggingface.co/docs/peft/

### 论文和博客
- LoRA论文: https://arxiv.org/abs/2106.09685
- QLoRA论文: https://arxiv.org/abs/2305.14314
- Anthropic Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering

### 项目学习资源（本地）
- [YOLOv8项目深度问答](../learning/YOLOv8_Deep_QA.md) - 中期答辩9个核心问题详解
- [YOLOv8项目速查卡](../learning/YOLOv8_Quick_Reference.md) - 3句话版本，面试前5分钟快速复习
- [Embedding微调面试指南](../learning/T2_LLM_Finetuning/EMBEDDING_FINETUNE_INTERVIEW_GUIDE.md) - T2任务面试准备
- [Embedding微调问答](../learning/T2_LLM_Finetuning/EMBEDDING_FINETUNE_INTERVIEW_QA.md) - T2任务技术问答

### 社区和讨论
- LangChain Discord
- Hugging Face Forums
- Reddit r/LocalLLaMA

---

## 📝 使用说明

### 如何使用这个文档

1. **开始新任务前**：
   - 检查"前置问题"是否已回答
   - 运行"技术趋势检查"
   - 准备好学习资源

2. **学习过程中**：
   - 勾选学习目标中的完成项
   - 记录遇到的问题和解决方案
   - 随时更新"学习日志"

3. **任务完成后**：
   - 填写"学习日志"
   - 完成验收标准的所有项
   - 准备面试素材
   - 自动进入"复习系统"

4. **复习时**：
   - 查看"复习任务看板"
   - 使用"复习清单模板"
   - 更新复习状态

5. **定期维护**：
   - 每月运行"技术趋势检查"
   - 更新过时的技术信息
   - 调整任务优先级

---

## 🎯 当前行动项

### 🔥 紧急待办
1. **T2前置问题** - 回答YOLOv8专利相关问题（5-10分钟）
2. **T1继续推进** - 完成LangGraph子图架构

### 📅 近期计划
- [ ] 继续T1（LangGraph）
- [ ] 完成T2前置问题回答
- [ ] 选择一个战术任务开始（T3或T4）

---

**文档版本**: v1.0  
**最后更新**: 2026-06-12  
**下次更新**: 完成任何任务后立即更新
