# LangChain实现指南

## 📋 目录

1. [项目概述](#项目概述)
2. [核心功能实现](#核心功能实现)
3. [Spring AI vs LangChain对比](#spring-ai-vs-langchain对比)
4. [关键知识点](#关键知识点)
5. [遇到的问题](#遇到的问题)

---

## 项目概述

这是一个基于LangChain的企业差旅智能体项目，复刻自Spring AI版本。通过对比两个框架的实现方式，深入理解AI应用开发的核心概念。

### 技术栈

- **Python 3.10+**
- **LangChain** - AI应用开发框架
- **通义千问API** - 大语言模型
- **FAISS** - 向量数据库
- **FastAPI** - Web框架

---

## 核心功能实现

### 1. LLM配置

#### Spring AI实现

```java
@Resource
private ChatClient chatClient;

String response = chatClient.prompt()
    .system("你是一个企业差旅助手")
    .user("你好")
    .call()
    .content();
```

#### LangChain实现

```python
from langchain_community.chat_models import ChatTongyi

llm = ChatTongyi(
    model_name="qwen-plus",
    dashscope_api_key=api_key,
    temperature=0.7
)

response = llm.invoke([
    SystemMessage(content="你是一个企业差旅助手"),
    HumanMessage(content="你好")
])
```

#### 对比分析

| 维度 | Spring AI | LangChain |
|------|-----------|-----------|
| **API风格** | Builder模式，链式调用 | 函数式，直接调用 |
| **消息格式** | .system().user() | 消息列表 |
| **类型安全** | 强类型（Java） | 弱类型（Python） |
| **灵活性** | 中等 | 高 |

**关键知识点**：
- LangChain使用消息列表（Message List）的方式更灵活
- Spring AI的Builder模式更符合Java习惯
- 两者都支持流式输出和温度控制

---

### 2. RAG（检索增强生成）

#### Spring AI实现

```java
// 1. 创建向量存储
@Bean
public VectorStore vectorStore(EmbeddingModel embeddingModel) {
    return new SimpleVectorStore(embeddingModel);
}

// 2. 检索
List<Document> docs = vectorStore.similaritySearch(
    SearchRequest.query("住宿标准").withTopK(5)
);

// 3. 手动组装Prompt
String context = docs.stream()
    .map(Document::getContent)
    .collect(Collectors.joining("\n"));

String response = chatClient.prompt()
    .user("根据以下内容回答：\n" + context + "\n问题：住宿标准")
    .call()
    .content();
```

#### LangChain实现

```python
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# 1. 创建向量存储
embeddings = DashScopeEmbeddings(model="text-embedding-v1")
vectorstore = FAISS.from_documents(documents, embeddings)

# 2. 创建RAG链（自动检索+生成）
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# 3. 一步查询
result = qa_chain.invoke({"query": "住宿标准"})
```

#### 对比分析

| 维度 | Spring AI | LangChain |
|------|-----------|-----------|
| **实现方式** | 手动组装 | 现成的Chain |
| **代码量** | 较多 | 较少 |
| **灵活性** | 高（完全控制） | 中（封装好的） |
| **易用性** | 需要理解细节 | 开箱即用 |

**关键知识点**：
- **RAG三步骤**：文档切分 → 向量化 → 检索+生成
- **LangChain的Chain概念**：把多个组件串联成流水线
- **FAISS vs SimpleVectorStore**：FAISS更强大，支持多种索引算法

**为什么需要RAG？**
- LLM的知识有限（训练数据截止日期）
- 企业内部数据LLM不知道
- RAG让LLM能访问外部知识库

---

### 3. 文档切分

#### 为什么要切分文档？

```
原始文档（5000字）
    ↓ 切分
文档块1（500字）+ 文档块2（500字）+ ... + 文档块10（500字）
    ↓ 向量化
向量1 + 向量2 + ... + 向量10
    ↓ 检索
找到最相关的3个向量 → 对应的3个文档块
```

**原因**：
- 向量数据库对每个块生成一个向量
- 太大的块：检索不精确（一个块包含太多主题）
- 太小的块：丢失上下文（信息不完整）
- **最佳实践**：500-1000字符

#### LangChain实现

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每块最大字符数
    chunk_overlap=50,      # 相邻块重叠字符数
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
)

split_docs = text_splitter.split_documents(documents)
```

**关键参数**：
- `chunk_size`：块大小，影响检索精度
- `chunk_overlap`：重叠部分，避免信息断裂
- `separators`：分隔符优先级（段落 > 句子 > 标点）

---

### 4. 向量检索原理

#### 什么是向量？

```
文本："去上海出差住宿标准"
  ↓ Embedding模型
向量：[0.23, -0.45, 0.67, ..., 0.12]  (1536维)
```

#### 相似度计算

```
查询向量：[0.23, -0.45, 0.67, ...]
文档1向量：[0.25, -0.43, 0.65, ...]  → 相似度：0.95 ✅
文档2向量：[0.10, 0.80, -0.30, ...]  → 相似度：0.32
文档3向量：[0.22, -0.46, 0.68, ...]  → 相似度：0.98 ✅
```

**Top-K检索**：返回相似度最高的K个文档

#### FAISS的优势

- **速度快**：Facebook优化的C++实现
- **算法多**：支持多种索引算法（Flat、IVF、HNSW）
- **可扩展**：支持百万级文档

---

### 5. Function Calling（工具调用）

#### Spring AI实现

```java
@Bean
public FunctionCallback weatherTool() {
    return FunctionCallback.builder()
        .function("queryWeather", (String city) -> {
            return "北京：晴天，25°C";
        })
        .description("查询天气")
        .inputType(String.class)
        .build();
}

ChatResponse response = chatClient.prompt()
    .user("北京天气怎么样")
    .functions("queryWeather")
    .call()
    .chatResponse();
```

#### LangChain实现

```python
from langchain.tools import tool

@tool
def query_weather(city: str) -> str:
    """查询指定城市的天气信息"""
    return f"{city}：晴天，25°C"

# 使用Agent自动调用工具
from langchain.agents import create_react_agent

tools = [query_weather]
agent = create_react_agent(llm, tools)
response = agent.invoke({"input": "北京天气怎么样"})
```

#### 工作流程

```
用户："北京天气怎么样？"
  ↓
LLM分析：需要调用query_weather工具
  ↓
提取参数：city="北京"
  ↓
调用工具：query_weather("北京")
  ↓
工具返回："北京：晴天，25°C"
  ↓
LLM生成回答："北京今天是晴天，温度25°C"
```

**关键知识点**：
- `@tool`装饰器自动提取函数签名和文档
- LLM根据工具描述决定是否调用
- Agent可以自动规划多步骤任务

---

### 6. 流式输出

#### 为什么需要流式输出？

**同步方式**：
```
用户提问 → 等待10秒 → 完整回答
```

**流式方式**：
```
用户提问 → 0.1秒后开始显示 → 逐字显示 → 完成
```

**优势**：
- 用户体验更好（不用等待）
- 感觉更快
- 可以提前看到部分答案

#### LangChain实现

```python
# 创建流式LLM
llm_stream = get_llm(streaming=True)

# 逐块生成
for chunk in llm_stream.stream(prompt):
    print(chunk.content, end="", flush=True)
```

#### FastAPI集成

```python
async def generate():
    for chunk in llm_stream.stream(prompt):
        yield f"data: {json.dumps({'content': chunk.content})}\n\n"

return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Spring AI vs LangChain对比

### 架构对比

#### Spring AI架构

```
ChatClient (核心接口)
    ↓
Advisors (增强功能)
├─ MessageChatMemoryAdvisor (记忆)
├─ QuestionAnswerAdvisor (RAG)
└─ ...
    ↓
ChatModel (模型接口)
├─ DashScopeChatModel
├─ OllamaChatModel
└─ ...
```

**特点**：
- 模块化设计（Advisor模式）
- 依赖注入（Spring Bean）
- 企业级特性（事务、监控）

#### LangChain架构

```
Chains (链式组合)
├─ LLMChain
├─ RetrievalQA
├─ ConversationChain
└─ ...
    ↓
Components (组件)
├─ LLM
├─ Memory
├─ VectorStore
├─ Tools
└─ ...
```

**特点**：
- 链式组合（管道模式）
- 函数式编程
- 快速原型开发

### 核心概念映射

| Spring AI | LangChain | 说明 |
|-----------|-----------|------|
| ChatClient | ChatModel | 对话模型 |
| Advisor | Chain | 功能增强 |
| FunctionCallback | Tool | 工具调用 |
| VectorStore | VectorStore | 向量存储 |
| ChatMemory | Memory | 会话记忆 |
| .stream() | .stream() | 流式输出 |

### 优缺点对比

#### Spring AI

**优势**：
- ✅ 类型安全（Java强类型）
- ✅ 企业级特性（Spring生态）
- ✅ 适合大型项目
- ✅ 团队协作友好

**劣势**：
- ❌ 学习曲线陡峭（需要Spring基础）
- ❌ 代码量较多
- ❌ 社区相对较小
- ❌ 迭代速度慢

#### LangChain

**优势**：
- ✅ 简洁易用（Python）
- ✅ 快速开发
- ✅ 社区活跃
- ✅ 生态丰富（工具、集成多）

**劣势**：
- ❌ 类型安全性差
- ❌ 企业级特性少
- ❌ 大型项目维护困难
- ❌ 性能不如Java

---

## 关键知识点

### 1. RAG的核心价值

**问题**：LLM不知道企业内部规章
**解决**：RAG让LLM能查询知识库

**流程**：
```
用户问题 → 向量检索 → 找到相关文档 → 组合Prompt → LLM生成答案
```

### 2. Embedding的作用

**作用**：把文本转换成向量（数字）

**为什么需要？**
- 计算机不理解文字，只理解数字
- 相似的文本，向量也相似
- 可以快速计算相似度

### 3. Chain的概念

**Chain = 组件的流水线**

```python
chain = retriever | format_docs | prompt | llm | parser
```

**优势**：
- 模块化（每个组件独立）
- 可复用（组件可以组合）
- 易测试（单独测试每个组件）

### 4. Agent vs Chain

| 维度 | Chain | Agent |
|------|-------|-------|
| **智能程度** | 固定流程 | 自主决策 |
| **适用场景** | 简单任务 | 复杂任务 |
| **可控性** | 高 | 低 |
| **成本** | 低 | 高 |

**Chain示例**：检索 → 生成（固定）
**Agent示例**：分析问题 → 决定调用哪些工具 → 综合结果（灵活）

---

## 遇到的问题

### 1. 中文文档切分问题

**问题**：英文按空格切分，中文没有空格

**解决**：
```python
separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
```

使用中文标点作为分隔符

### 2. FAISS加载警告

**问题**：`allow_dangerous_deserialization=True`警告

**原因**：FAISS使用pickle序列化，有安全风险

**解决**：
- 开发环境：允许
- 生产环境：使用其他向量数据库（Chroma、Pinecone）

### 3. 流式输出中文乱码

**问题**：SSE返回中文乱码

**解决**：
```python
json.dumps({'content': chunk.content}, ensure_ascii=False)
```

设置`ensure_ascii=False`

---

## 面试准备

### 如何介绍这个项目？

**框架**：
1. 项目背景（为什么做）
2. 技术选型（用了什么）
3. 核心功能（做了什么）
4. 技术亮点（怎么做的）
5. 收获总结（学到了什么）

**示例回答**：

> "我做了一个企业差旅智能体项目，用LangChain复刻了之前的Spring AI版本。
>
> 核心功能是RAG问答系统，让AI能回答企业差旅规章的问题。我用FAISS做向量检索，通义千问做LLM，FastAPI提供API接口。
>
> 技术亮点是对比了Spring AI和LangChain的实现方式，理解了两个框架的设计理念。Spring AI用Advisor模式更模块化，LangChain用Chain组合更灵活。
>
> 通过这个项目，我深入理解了RAG的原理、向量检索的机制、以及如何设计AI应用的架构。"

### 常见面试问题

**Q1：RAG和微调有什么区别？**

A：
- RAG：检索外部知识，不改变模型
- 微调：训练模型，改变模型参数
- RAG成本低、更新快，微调效果好、成本高

**Q2：如何提高RAG的准确率？**

A：
1. 优化文档切分（chunk_size、overlap）
2. 改进检索策略（Top-K、阈值）
3. 优化Prompt模板
4. 使用更好的Embedding模型
5. 添加查询重写（Query Rewriting）

**Q3：LangChain和Spring AI选哪个？**

A：
- 快速原型、个人项目：LangChain
- 企业级、大型项目：Spring AI
- 看团队技术栈：Python用LangChain，Java用Spring AI

---

## 下一步优化

1. **添加会话记忆**：让AI记住上下文
2. **实现Agent**：自动调用多个工具
3. **添加评估指标**：测量RAG准确率
4. **优化检索策略**：混合检索（向量+关键词）
5. **添加缓存**：减少重复查询

---

**最后更新**：2026年5月11日
