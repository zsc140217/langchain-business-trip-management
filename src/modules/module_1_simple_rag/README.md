# Module 1: Simple RAG - 简单检索增强生成

## 概述

实现基础的RAG（Retrieval-Augmented Generation）系统，使用LangChain Expression Language (LCEL)构建问答链。

## 核心概念

### RAG工作流程

```
用户问题
   ↓
检索器（Retriever）→ 从向量数据库检索相关文档
   ↓
格式化文档 → 组合成上下文
   ↓
Prompt模板 → 生成包含上下文和问题的Prompt
   ↓
LLM → 生成答案
   ↓
输出解析器 → 返回最终答案
```

### LCEL语法

LCEL (LangChain Expression Language) 使用管道符 `|` 连接组件：

```python
chain = retriever | prompt | llm | output_parser
```

优势：
- 声明式语法，清晰易懂
- 自动处理数据流转
- 支持流式输出
- 易于组合和扩展

## 文件结构

```
module_1_simple_rag/
├── loader.py              # 文档加载和切分
├── retriever.py           # FAISS向量检索器
├── chain.py               # RAG链（LCEL）
├── example.py             # 完整示例
├── test_simple_rag.py     # 单元测试
└── README.md              # 本文档
```

## 组件说明

### 1. loader.py - 文档加载器

**功能：**
- 加载文本文档
- 使用RecursiveCharacterTextSplitter切分文档
- 返回Document对象列表

**核心函数：**
```python
load_and_split_documents(file_path, chunk_size=500, chunk_overlap=50)
load_documents_from_text(text, chunk_size=500, chunk_overlap=50)
```

**参数说明：**
- `chunk_size`: 每个块的最大字符数（推荐500-1000）
- `chunk_overlap`: 相邻块的重叠字符数（推荐10-20%的chunk_size）

**为什么要切分文档？**
- 向量检索需要合适粒度的文档块
- 太大：检索不精确，包含太多无关信息
- 太小：上下文不完整，语义信息丢失

### 2. retriever.py - 向量检索器

**功能：**
- 创建FAISS向量存储
- 提供Top-K相似度检索
- 支持向量存储持久化

**核心函数：**
```python
create_faiss_vectorstore(documents, embedding_model="text-embedding-v1")
create_retriever(vectorstore, k=5, score_threshold=None)
save_vectorstore(vectorstore, path)
load_vectorstore(path, embedding_model="text-embedding-v1")
```

**FAISS vs 其他向量数据库：**
- **FAISS**: Facebook开源，本地运行，速度快
- **Chroma**: 更现代，支持持久化
- **Pinecone**: 云服务，适合生产环境
- **Milvus**: 分布式，适合大规模

### 3. chain.py - RAG链

**功能：**
- 使用LCEL构建RAG链
- 支持基础问答和带来源文档的问答

**核心函数：**
```python
create_rag_chain_lcel(retriever, llm=None)
create_rag_chain_with_sources(retriever, llm=None)
```

**LCEL架构：**
```python
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

## 快速开始

### 1. 安装依赖

```bash
# 在项目根目录
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 创建.env文件
DASHSCOPE_API_KEY=你的通义千问API Key
```

### 3. 运行示例

```bash
# 进入模块目录
cd src/modules/module_1_simple_rag

# 测试各个组件
python loader.py        # 测试文档加载
python retriever.py     # 测试向量检索
python chain.py         # 测试RAG链

# 运行完整示例
python example.py

# 运行单元测试
python test_simple_rag.py
```

## 使用示例

### 基础用法

```python
from loader import load_documents_from_text
from retriever import create_faiss_vectorstore, create_retriever
from chain import create_rag_chain_lcel

# 1. 加载文档
text = "企业差旅管理规章..."
docs = load_documents_from_text(text, chunk_size=500)

# 2. 创建向量存储
vectorstore = create_faiss_vectorstore(docs)

# 3. 创建检索器
retriever = create_retriever(vectorstore, k=5)

# 4. 创建RAG链
rag_chain = create_rag_chain_lcel(retriever)

# 5. 问答
answer = rag_chain.invoke("去上海出差住宿能报多少钱？")
print(answer)
```

### 带来源文档

```python
from chain import create_rag_chain_with_sources

# 创建带来源的RAG链
rag_chain = create_rag_chain_with_sources(retriever)

# 问答
result = rag_chain.invoke("二线城市住宿标准是多少？")

print("答案：", result['answer'])
print("来源文档数：", len(result['source_documents']))

for doc in result['source_documents']:
    print(doc.page_content)
```

### 向量存储持久化

```python
from retriever import save_vectorstore, load_vectorstore

# 保存向量存储
save_vectorstore(vectorstore, "./vectorstore_cache")

# 加载向量存储
loaded_vectorstore = load_vectorstore("./vectorstore_cache")
```

## 核心技术点

### 1. 文档切分策略

使用RecursiveCharacterTextSplitter的递归切分：

```python
separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
```

优先级：段落 > 句子 > 标点 > 空格

### 2. 向量化

使用DashScope Embeddings (text-embedding-v1)：
- 将文本转换为768维向量
- 相似的文本生成相似的向量
- 通过向量相似度进行检索

### 3. Top-K检索

从向量数据库检索最相似的K个文档：
- K值通常设为3-5
- 可选相似度阈值过滤
- 基于余弦相似度

### 4. Prompt工程

RAG Prompt模板：
```
你是一个企业差旅助手。请根据以下企业差旅规章准确回答用户的问题。

企业差旅规章：
{context}

用户问题：{question}

请基于上述规章给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
```

## 对比Spring AI

| 维度 | LangChain (本模块) | Spring AI |
|------|-------------------|-----------|
| **文档加载** | `RecursiveCharacterTextSplitter` | `TextSplitter` |
| **向量存储** | `FAISS.from_documents()` | `SimpleVectorStore` |
| **检索器** | `vectorstore.as_retriever()` | `vectorStore.similaritySearch()` |
| **RAG链** | LCEL管道: `retriever \| prompt \| llm` | Advisor模式: `QuestionAnswerAdvisor` |
| **语法风格** | 函数式、声明式 | 面向对象、Builder模式 |

## 性能优化建议

### 1. 合理设置chunk_size

- 短文档（500-800字）：chunk_size=200-300
- 中文档（1000-3000字）：chunk_size=500-800
- 长文档（>3000字）：chunk_size=800-1000

### 2. 调整Top-K

- 精确查询：k=3
- 广泛查询：k=5-10
- 需要更多上下文：增大k值

### 3. 向量存储持久化

避免每次启动都重新生成向量：
```python
# 首次运行：创建并保存
vectorstore = create_faiss_vectorstore(docs)
save_vectorstore(vectorstore, "./cache")

# 后续运行：直接加载
vectorstore = load_vectorstore("./cache")
```

### 4. LLM温度设置

- RAG场景：temperature=0.1-0.3（更准确）
- 创意生成：temperature=0.7-0.9（更多样）

## 常见问题

### Q1: 为什么检索结果不准确？

**可能原因：**
1. chunk_size设置不合理
2. 文档切分破坏了语义完整性
3. Top-K值过小
4. Embedding模型不适合当前领域

**解决方案：**
1. 调整chunk_size和chunk_overlap
2. 使用更智能的切分策略（按段落、章节）
3. 增大k值
4. 尝试不同的Embedding模型

### Q2: 如何处理中英文混合文档？

```python
# 使用多语言友好的分隔符
separators=["\n\n", "\n", "。", ".", "！", "!", "？", "?", " "]
```

### Q3: 如何提高检索速度？

1. 使用向量存储持久化
2. 减小chunk数量（增大chunk_size）
3. 使用FAISS的GPU版本（如果有GPU）
4. 对于大规模数据，考虑使用专业向量数据库（Milvus、Pinecone）

## 测试覆盖率

- ✅ 文档加载和切分
- ✅ 向量存储创建
- ✅ 检索器功能
- ✅ RAG链问答
- ✅ 带来源文档的问答
- ✅ 向量存储持久化

目标覆盖率：**80%+**

## 下一步

学习完Module 1后，可以继续：

- **Module 2**: Advanced RAG - 混合检索、查询改写、重排序
- **Module 3**: ReAct Agent - 工具调用和推理
- **Module 4**: Multi-Agent - 多智能体协作

## 参考资料

- [LangChain官方文档](https://python.langchain.com/)
- [FAISS官方文档](https://github.com/facebookresearch/faiss)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)
- [RAG最佳实践](https://python.langchain.com/docs/use_cases/question_answering/)

## License

MIT License
