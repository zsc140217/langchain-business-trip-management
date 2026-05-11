# LangChain复刻Spring AI项目 - 完整提示词

## 📋 项目背景

我有一个基于Spring AI的企业差旅智能体项目，现在想用LangChain复刻它，用于学习和对比两个框架的差异。

**原项目地址**：`E:\Desktop\ai-agent\jblmj-ai-agent-master`  
**新项目地址**：`E:\Desktop\langchain-business-trip-management`  
**GitHub仓库**：https://github.com/zsc140217/langchain-business-trip-management

---

## 🎯 项目需求

### 核心功能（按优先级）

1. **企业差旅规章问答（RAG）** ⭐⭐⭐⭐⭐ 最重要
   - 加载企业差旅规章文档
   - 实现向量检索
   - 支持查询重写
   - 返回准确答案

2. **天气查询工具** ⭐⭐⭐⭐
   - 调用和风天气API
   - 支持单城市查询
   - 支持多城市对比

3. **简单对话** ⭐⭐⭐
   - 基础对话功能
   - 支持流式输出
   - 支持会话记忆

4. **工作流编排（可选）** ⭐⭐
   - 复杂度评估
   - 任务分解
   - 工具自动调用

---

## 📚 技术要求

### 技术栈
- **Python 3.10+**
- **LangChain** (最新版本)
- **通义千问API** (DashScope)
- **向量数据库**：FAISS（本地）或Chroma
- **Web框架**：FastAPI（提供API接口）

### 项目结构
```
langchain-business-trip-management/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置文件
│   ├── models/
│   │   ├── __init__.py
│   │   └── llm.py              # LLM配置
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py           # 文档加载
│   │   ├── retriever.py        # 检索器
│   │   └── chain.py            # RAG链
│   ├── tools/
│   │   ├── __init__.py
│   │   └── weather.py          # 天气工具
│   ├── agents/
│   │   ├── __init__.py
│   │   └── orchestrator.py     # 工作流编排
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # 工具函数
├── data/
│   └── travel_policy.txt       # 企业差旅规章（示例）
├── tests/
│   └── test_rag.py             # 测试文件
├── requirements.txt            # 依赖
├── .env.example                # 环境变量示例
├── README.md                   # 项目说明
└── docs/
    ├── SPRING_AI_VS_LANGCHAIN.md  # 已有
    ├── IMPLEMENTATION_GUIDE.md    # 实现指南
    └── API_DOCS.md                # API文档
```

---

## 🔧 具体实现要求

### 1. 环境配置

**requirements.txt**：
```txt
langchain>=0.1.0
langchain-community>=0.0.20
langchain-openai>=0.0.5
faiss-cpu>=1.7.4
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
dashscope>=1.14.0
pydantic>=2.5.0
```

**.env.example**：
```env
# 通义千问API Key
DASHSCOPE_API_KEY=your_api_key_here

# 和风天气API Key（可选）
QWEATHER_API_KEY=your_weather_api_key_here

# 服务配置
HOST=0.0.0.0
PORT=8000
```

---

### 2. LLM配置（对应Spring AI的ChatClient）

**src/models/llm.py**：
```python
from langchain_community.chat_models import ChatTongyi
from langchain.schema import HumanMessage, SystemMessage
import os

def get_llm(model_name="qwen-plus", temperature=0.7, streaming=False):
    """
    获取通义千问LLM实例
    
    对应Spring AI的：
    @Resource
    private ChatClient chatClient;
    """
    return ChatTongyi(
        model_name=model_name,
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=temperature,
        streaming=streaming
    )

# 使用示例
if __name__ == "__main__":
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content="你是一个企业差旅助手"),
        HumanMessage(content="你好")
    ])
    print(response.content)
```

---

### 3. RAG实现（对应Spring AI的VectorStore + QuestionAnswerAdvisor）

**src/rag/loader.py**：
```python
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_documents(file_path: str):
    """
    加载企业差旅规章文档
    
    对应Spring AI的：
    Resource resource = new ClassPathResource("data/travel_policy.txt");
    """
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()
    
    # 文档切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    
    return text_splitter.split_documents(documents)
```

**src/rag/retriever.py**：
```python
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
import os

def create_vectorstore(documents):
    """
    创建向量存储
    
    对应Spring AI的：
    @Bean
    public VectorStore vectorStore(EmbeddingModel embeddingModel) {
        return new SimpleVectorStore(embeddingModel);
    }
    """
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

def get_retriever(vectorstore, k=5):
    """
    获取检索器
    
    对应Spring AI的：
    vectorStore.similaritySearch(SearchRequest.query("住宿标准").withTopK(5))
    """
    return vectorstore.as_retriever(search_kwargs={"k": k})
```

**src/rag/chain.py**：
```python
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def create_rag_chain(llm, retriever):
    """
    创建RAG链
    
    对应Spring AI的：
    chatClient.prompt()
        .user("根据以下内容回答：\n" + context + "\n问题：住宿标准")
        .call()
        .content()
    """
    
    # 自定义Prompt模板
    template = """你是一个企业差旅助手。请根据以下企业差旅规章回答用户的问题。

规章内容：
{context}

用户问题：{question}

请给出准确、详细的回答。如果规章中没有相关信息，请明确告知用户。
"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return qa_chain
```

---

### 4. 天气工具（对应Spring AI的FunctionCallback）

**src/tools/weather.py**：
```python
from langchain.tools import tool
import requests
import os

@tool
def query_weather(city: str) -> str:
    """
    查询指定城市的天气信息
    
    对应Spring AI的：
    @Bean
    public FunctionCallback weatherTool() {
        return FunctionCallback.builder()
            .function("queryWeather", (String city) -> {...})
            .build();
    }
    
    Args:
        city: 城市名称，如"北京"、"上海"
    
    Returns:
        天气信息字符串
    """
    api_key = os.getenv("QWEATHER_API_KEY")
    
    if not api_key:
        return f"{city}的天气信息：晴天，25°C（模拟数据）"
    
    # 调用和风天气API
    try:
        # 1. 获取城市ID
        location_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}"
        location_response = requests.get(location_url, timeout=5)
        location_data = location_response.json()
        
        if location_data["code"] != "200":
            return f"无法找到城市：{city}"
        
        location_id = location_data["location"][0]["id"]
        
        # 2. 获取天气
        weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()
        
        if weather_data["code"] != "200":
            return f"无法获取{city}的天气信息"
        
        now = weather_data["now"]
        return f"{city}：{now['text']}，温度{now['temp']}°C，体感温度{now['feelsLike']}°C"
        
    except Exception as e:
        return f"查询{city}天气时出错：{str(e)}"

@tool
def compare_weather(city1: str, city2: str) -> str:
    """
    对比两个城市的天气
    
    Args:
        city1: 第一个城市
        city2: 第二个城市
    
    Returns:
        对比结果
    """
    weather1 = query_weather.invoke(city1)
    weather2 = query_weather.invoke(city2)
    
    return f"天气对比：\n{weather1}\n{weather2}"
```

---

### 5. FastAPI接口（对应Spring Boot的Controller）

**src/main.py**：
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json

from src.models.llm import get_llm
from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.rag.chain import create_rag_chain
from src.tools.weather import query_weather, compare_weather

app = FastAPI(title="LangChain企业差旅智能体")

# 初始化RAG
documents = load_documents("data/travel_policy.txt")
vectorstore = create_vectorstore(documents)
retriever = get_retriever(vectorstore)
llm = get_llm()
rag_chain = create_rag_chain(llm, retriever)

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = "default"

@app.post("/api/chat/sync")
async def chat_sync(request: ChatRequest):
    """
    同步对话接口
    
    对应Spring AI的：
    @GetMapping("/chat/sync")
    public String chatSync(@RequestParam String message)
    """
    try:
        result = rag_chain.invoke({"query": request.message})
        return {
            "answer": result["result"],
            "sources": [doc.page_content for doc in result["source_documents"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话接口
    
    对应Spring AI的：
    @GetMapping("/chat/sse")
    public Flux<String> chatSSE(@RequestParam String message)
    """
    async def generate():
        try:
            llm_stream = get_llm(streaming=True)
            
            # 先检索相关文档
            docs = retriever.get_relevant_documents(request.message)
            context = "\n".join([doc.page_content for doc in docs])
            
            # 构建Prompt
            prompt = f"""你是一个企业差旅助手。请根据以下企业差旅规章回答用户的问题。

规章内容：
{context}

用户问题：{request.message}

请给出准确、详细的回答。"""
            
            # 流式生成
            for chunk in llm_stream.stream(prompt):
                yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/weather")
async def get_weather(city: str):
    """
    天气查询接口
    
    对应Spring AI的：
    @GetMapping("/weather")
    public String queryWeather(@RequestParam String city)
    """
    try:
        result = query_weather.invoke(city)
        return {"city": city, "weather": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### 6. 测试文件

**tests/test_rag.py**：
```python
import pytest
from src.rag.loader import load_documents
from src.rag.retriever import create_vectorstore, get_retriever
from src.rag.chain import create_rag_chain
from src.models.llm import get_llm

def test_rag_pipeline():
    """测试RAG完整流程"""
    # 1. 加载文档
    documents = load_documents("data/travel_policy.txt")
    assert len(documents) > 0
    
    # 2. 创建向量存储
    vectorstore = create_vectorstore(documents)
    assert vectorstore is not None
    
    # 3. 创建检索器
    retriever = get_retriever(vectorstore)
    docs = retriever.get_relevant_documents("住宿标准")
    assert len(docs) > 0
    
    # 4. 创建RAG链
    llm = get_llm()
    rag_chain = create_rag_chain(llm, retriever)
    
    # 5. 测试查询
    result = rag_chain.invoke({"query": "去上海出差住宿能报多少"})
    assert "result" in result
    print(f"回答：{result['result']}")

if __name__ == "__main__":
    test_rag_pipeline()
```

---

### 7. 示例数据

**data/travel_policy.txt**：
```txt
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离≥500公里：飞机经济舱
3. 出租车：仅限机场、火车站往返酒店

第三章 餐饮补贴
1. 早餐：30元/天
2. 午餐：50元/天
3. 晚餐：50元/天
4. 总计：130元/天

第四章 其他规定
1. 出差需提前3天申请
2. 出差结束后7天内提交报销
3. 超标部分自行承担
```

---

## 📝 实现步骤

### Step 1：环境搭建
```bash
cd E:\Desktop\langchain-business-trip-management

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑.env，填入API Key
```

### Step 2：测试RAG
```bash
python tests/test_rag.py
```

### Step 3：启动服务
```bash
python src/main.py
```

### Step 4：测试接口
```bash
# 同步对话
curl "http://localhost:8000/api/chat/sync" -X POST -H "Content-Type: application/json" -d "{\"message\":\"去上海出差住宿标准\"}"

# 流式对话
curl "http://localhost:8000/api/chat/stream" -X POST -H "Content-Type: application/json" -d "{\"message\":\"帮我规划去杭州的行程\"}"

# 天气查询
curl "http://localhost:8000/api/weather?city=北京"
```

---

## 📊 对比文档要求

在实现过程中，请在`docs/IMPLEMENTATION_GUIDE.md`中记录：

1. **每个功能的实现对比**
   - Spring AI怎么实现的
   - LangChain怎么实现的
   - 代码对比
   - 优缺点分析

2. **遇到的问题和解决方案**
   - 什么问题
   - 怎么解决的
   - 学到了什么

3. **性能对比**
   - 响应延迟
   - 准确率
   - 资源占用

---

## 🎯 交付要求

### 必须完成
- [x] 基础环境搭建
- [x] RAG功能（企业差旅规章问答）
- [x] 天气查询工具
- [x] FastAPI接口
- [x] 测试文件
- [x] 完整的README
- [x] 实现指南文档

### 可选完成
- [ ] 工作流编排（复杂度评估）
- [ ] 前端界面
- [ ] Docker部署
- [ ] 性能优化

---

## 💡 注意事项

1. **代码风格**：
   - 遵循PEP 8规范
   - 添加详细的注释
   - 每个函数都要有docstring

2. **错误处理**：
   - 所有API调用都要try-except
   - 返回友好的错误信息
   - 记录日志

3. **对比说明**：
   - 每个关键函数都要注释"对应Spring AI的XXX"
   - 在文档中详细对比实现方式
   - 说明为什么这样设计

4. **测试验证**：
   - 确保所有功能都能正常运行
   - 提供测试用例
   - 记录测试结果

---

## 🚀 开始实现

请按照以上要求，完整实现LangChain版本的企业差旅智能体项目。

重点关注：
1. **RAG功能的准确性**
2. **代码的可读性和可维护性**
3. **与Spring AI版本的对比分析**
4. **完整的文档和注释**

祝顺利！🎉
