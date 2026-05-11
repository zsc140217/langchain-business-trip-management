# Spring AI vs LangChain 完全对比指南

## 🎯 核心定位

| 维度 | Spring AI | LangChain |
|------|-----------|-----------|
| **生态** | Java/Spring生态 | Python生态（主流） |
| **定位** | 企业级Java应用 | 快速原型和研究 |
| **成熟度** | 1.0版本（2024年） | 成熟（2022年起） |
| **社区** | Spring官方支持 | 开源社区活跃 |
| **学习曲线** | 需要Spring基础 | Python即可 |

---

## 📚 核心概念对比

### 1. 对话模型（Chat Model）

**Spring AI**：
```java
@Resource
private ChatClient chatClient;

String response = chatClient.prompt()
    .user("你好")
    .call()
    .content();
```

**LangChain**：
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo")
response = llm.invoke("你好")
```

**对比**：
- Spring AI用Builder模式，链式调用
- LangChain更简洁，直接invoke
- 两者都支持流式输出

---

### 2. Prompt模板

**Spring AI**：
```java
String template = """
    你是{role}。
    用户问题：{question}
    """;

String response = chatClient.prompt()
    .user(u -> u.text(template)
        .param("role", "助手")
        .param("question", "天气怎么样"))
    .call()
    .content();
```

**LangChain**：
```python
from langchain.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "你是{role}"),
    ("user", "{question}")
])

chain = template | llm
response = chain.invoke({
    "role": "助手",
    "question": "天气怎么样"
})
```

**对比**：
- Spring AI用Java的文本块（"""）
- LangChain用管道符（|）组合链
- LangChain的链式组合更灵活

---

### 3. RAG（检索增强生成）

**Spring AI**：
```java
// 1. 创建向量存储
@Bean
public VectorStore vectorStore(EmbeddingModel embeddingModel) {
    return new SimpleVectorStore(embeddingModel);
}

// 2. 添加文档
vectorStore.add(List.of(
    new Document("企业差旅规章...")
));

// 3. 检索
List<Document> docs = vectorStore.similaritySearch(
    SearchRequest.query("住宿标准")
        .withTopK(5)
);

// 4. 生成答案
String context = docs.stream()
    .map(Document::getContent)
    .collect(Collectors.joining("\n"));

String response = chatClient.prompt()
    .user("根据以下内容回答：\n" + context + "\n问题：住宿标准")
    .call()
    .content();
```

**LangChain**：
```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# 1. 创建向量存储
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(
    ["企业差旅规章..."],
    embeddings
)

# 2. 创建检索链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# 3. 查询
response = qa_chain.invoke("住宿标准")
```

**对比**：
- Spring AI需要手动组装RAG流程
- LangChain有现成的RetrievalQA链
- LangChain更简洁，Spring AI更灵活

---

### 4. 工具调用（Function Calling）

**Spring AI**：
```java
// 1. 定义工具
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

// 2. 注册工具
ChatResponse response = chatClient.prompt()
    .user("北京天气怎么样")
    .functions("queryWeather")
    .call()
    .chatResponse();
```

**LangChain**：
```python
from langchain.tools import tool
from langchain.agents import create_react_agent

# 1. 定义工具
@tool
def query_weather(city: str) -> str:
    """查询天气"""
    return f"{city}：晴天，25°C"

# 2. 创建Agent
tools = [query_weather]
agent = create_react_agent(llm, tools)

# 3. 执行
response = agent.invoke({"input": "北京天气怎么样"})
```

**对比**：
- Spring AI用FunctionCallback
- LangChain用@tool装饰器
- LangChain的Agent更智能（ReAct模式）

---

### 5. 记忆（Memory）

**Spring AI**：
```java
// 1. 创建会话记忆
@Bean
public ChatMemory chatMemory() {
    return new InMemoryChatMemory();
}

// 2. 使用记忆
ChatResponse response = chatClient.prompt()
    .user("我叫张三")
    .advisors(new MessageChatMemoryAdvisor(chatMemory))
    .call()
    .chatResponse();

// 下次对话会记住
ChatResponse response2 = chatClient.prompt()
    .user("我叫什么名字")
    .advisors(new MessageChatMemoryAdvisor(chatMemory))
    .call()
    .chatResponse();
```

**LangChain**：
```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# 1. 创建记忆
memory = ConversationBufferMemory()

# 2. 创建对话链
conversation = ConversationChain(
    llm=llm,
    memory=memory
)

# 3. 对话
conversation.invoke("我叫张三")
conversation.invoke("我叫什么名字")  # 会记住
```

**对比**：
- Spring AI用Advisor模式
- LangChain用Memory组件
- LangChain的Memory类型更丰富

---

## 🏗️ 架构对比

### Spring AI架构
```
┌─────────────────────────────────────┐
│         Spring Boot应用              │
├─────────────────────────────────────┤
│  ChatClient (核心接口)               │
│  ↓                                  │
│  Advisors (增强功能)                 │
│  ├─ MessageChatMemoryAdvisor        │
│  ├─ QuestionAnswerAdvisor (RAG)     │
│  └─ ...                             │
│  ↓                                  │
│  ChatModel (模型接口)                │
│  ├─ DashScopeChatModel              │
│  ├─ OllamaChatModel                 │
│  └─ ...                             │
└─────────────────────────────────────┘
```

### LangChain架构
```
┌─────────────────────────────────────┐
│         Python应用                   │
├─────────────────────────────────────┤
│  Chains (链式组合)                   │
│  ├─ LLMChain                        │
│  ├─ RetrievalQA                     │
│  ├─ ConversationChain               │
│  └─ ...                             │
│  ↓                                  │
│  Components (组件)                   │
│  ├─ LLM                             │
│  ├─ Memory                          │
│  ├─ VectorStore                     │
│  ├─ Tools                           │
│  └─ ...                             │
└─────────────────────────────────────┘
```

**对比**：
- Spring AI更模块化（Advisor模式）
- LangChain更链式（管道组合）
- Spring AI适合企业级，LangChain适合快速开发

---

## 💡 你的项目功能对应关系

| 功能 | Spring AI实现 | LangChain实现 |
|------|--------------|--------------|
| **对话** | ChatClient | ChatOpenAI |
| **RAG** | VectorStore + QuestionAnswerAdvisor | RetrievalQA |
| **工具调用** | FunctionCallback | @tool + Agent |
| **记忆** | MessageChatMemoryAdvisor | ConversationBufferMemory |
| **流式输出** | .stream() | .stream() |
| **复杂度评估** | 自研WorkflowOrchestrator | LangGraph（状态机） |

---

## 🎯 学习路径建议

### 如果你熟悉Spring AI，学LangChain要注意：

1. **思维转换**：
   - Spring AI：面向对象，Builder模式
   - LangChain：函数式，管道组合

2. **核心概念**：
   - Advisor → Chain
   - FunctionCallback → Tool
   - ChatMemory → Memory

3. **优势**：
   - LangChain的Chain更灵活
   - LangChain的Agent更智能
   - LangChain的生态更丰富

4. **劣势**：
   - LangChain的类型安全性差（Python）
   - LangChain的企业级特性少
   - LangChain的Spring集成弱

---

## 📊 面试时怎么讲

### 回答"你了解Spring AI和LangChain吗？"

**框架**：
```
1. 说出两者的定位
2. 对比核心概念
3. 说出你的实践经验
4. 展示你的理解
```

**示例回答**：
```
"我用过Spring AI和LangChain。

Spring AI是Spring官方的AI框架，
适合企业级Java应用。
我用它做了企业差旅智能体项目。

LangChain是Python生态的主流框架，
更适合快速原型和研究。
我正在用它复刻我的Spring AI项目。

核心区别是：
- Spring AI用Advisor模式，更模块化
- LangChain用Chain组合，更灵活
- Spring AI适合生产环境，LangChain适合快速开发

通过对比两者，我理解了：
- RAG的核心流程（检索→生成）
- Agent的工作原理（ReAct模式）
- 工具调用的实现方式
- 记忆系统的设计思路

这让我对AI应用开发有了更深的理解。"
```

---

## 🚀 下一步

现在你已经理解了Spring AI和LangChain的区别。

接下来我会：
1. 搭建LangChain环境
2. 复刻你的Spring AI项目
3. 边做边讲解每个功能
4. 对比两者的实现方式

让你对LangChain不再害怕！💪

---

**最后更新**：2026年5月11日 20:55
