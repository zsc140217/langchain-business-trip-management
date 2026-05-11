# LangChain版企业出差管理项目

基于LangChain框架的企业出差管理系统，复刻自Spring AI版本。通过对比两个框架的实现方式，深入理解AI应用开发的核心概念。

## 🎯 项目目标

- 学习LangChain框架的核心概念
- 对比Spring AI和LangChain的实现差异
- 掌握RAG（检索增强生成）技术
- 理解AI应用开发的最佳实践

## ✨ 核心功能

### 1. 企业差旅规章问答（RAG）⭐⭐⭐⭐⭐
- 基于FAISS的向量检索
- 智能文档切分和向量化
- 准确回答企业差旅相关问题

### 2. 天气查询工具 ⭐⭐⭐⭐
- 集成和风天气API
- 支持单城市查询和多城市对比
- 展示Function Calling能力

### 3. 流式对话 ⭐⭐⭐
- 实时返回生成内容
- 提升用户体验
- 支持SSE（Server-Sent Events）

### 4. 工作流编排系统 ⭐⭐⭐⭐⭐ **新增**
- **ComplexityAssessor**：混合判断策略（80%规则+20%LLM）
- **TaskDecomposer**：复杂查询自动分解，支持依赖关系
- **WorkflowOrchestrator**：智能路由引擎，根据复杂度选择策略
- 工具调用率：100%（解决弱模型工具调用不可靠问题）

## 🏗️ 项目结构

```
langchain-business-trip-management/
├── src/
│   ├── models/
│   │   └── llm.py              # LLM配置（通义千问）
│   ├── agents/                 # 🆕 Agent系统
│   │   ├── complexity_assessor.py    # 复杂度评估器
│   │   ├── task_decomposer.py        # 任务分解器
│   │   └── workflow_orchestrator.py  # 工作流编排器
│   ├── rag/
│   │   ├── loader.py           # 文档加载和切分
│   │   ├── retriever.py        # 向量存储和检索
│   │   └── chain.py            # RAG链组装
│   ├── tools/
│   │   └── weather.py          # 天气查询工具
│   ├── skills/                 # 🆕 Skill系统（计划中）
│   ├── memory/                 # 🆕 记忆系统（计划中）
│   ├── config.py               # 配置文件
│   └── main.py                 # FastAPI主应用
├── data/
│   └── travel_policy.txt       # 企业差旅规章
├── tests/
│   └── test_rag.py             # RAG功能测试
├── docs/
│   ├── SPRING_AI_VS_LANGCHAIN.md    # 框架对比
│   ├── IMPLEMENTATION_GUIDE.md      # 实现指南
│   └── SPRING_AI_ANALYSIS.md        # 🆕 Spring AI深度分析
├── requirements.txt            # Python依赖
├── .env.example                # 环境变量示例
└── README.md                   # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/zsc140217/langchain-business-trip-management.git
cd langchain-business-trip-management

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API Key

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑.env文件，填入你的API Key
# DASHSCOPE_API_KEY=your_dashscope_api_key_here
# QWEATHER_API_KEY=your_qweather_api_key_here（可选）
```

**获取API Key**：
- 通义千问：https://dashscope.console.aliyun.com/
- 和风天气：https://dev.qweather.com/（可选）

### 3. 测试RAG功能

```bash
# 运行测试
python tests/test_rag.py
```

### 4. 启动服务

```bash
# 启动FastAPI服务
python src/main.py

# 服务将运行在 http://localhost:8000
# API文档：http://localhost:8000/docs
```

## 📡 API接口

### 1. 同步对话

```bash
curl -X POST "http://localhost:8000/api/chat/sync" \
  -H "Content-Type: application/json" \
  -d '{"message": "去上海出差住宿标准是多少？"}'
```

### 2. 流式对话

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我规划去杭州的行程"}'
```

### 3. 天气查询

```bash
curl "http://localhost:8000/api/weather?city=北京"
```

### 4. 天气对比

```bash
curl "http://localhost:8000/api/weather/compare?city1=北京&city2=上海"
```

## 📚 核心概念

### RAG（检索增强生成）

```
用户提问 → 向量检索 → 找到相关文档 → 组合Prompt → LLM生成答案
```

**为什么需要RAG？**
- LLM不知道企业内部规章
- RAG让LLM能查询知识库
- 成本低、更新快

### LangChain核心组件

1. **ChatModel** - 对话模型（通义千问）
2. **VectorStore** - 向量存储（FAISS）
3. **Chain** - 链式组合（RetrievalQA）
4. **Tool** - 工具调用（天气查询）

## 🆚 Spring AI vs LangChain

| 维度 | Spring AI | LangChain |
|------|-----------|-----------|
| **语言** | Java | Python |
| **定位** | 企业级应用 | 快速原型 |
| **架构** | Advisor模式 | Chain组合 |
| **学习曲线** | 陡峭 | 平缓 |
| **社区** | Spring官方 | 开源活跃 |

详细对比见：[docs/SPRING_AI_VS_LANGCHAIN.md](docs/SPRING_AI_VS_LANGCHAIN.md)

## 📖 学习资源

- [实现指南](docs/IMPLEMENTATION_GUIDE.md) - 详细的实现过程和知识点
- [框架对比](docs/SPRING_AI_VS_LANGCHAIN.md) - Spring AI和LangChain的完整对比
- [LangChain官方文档](https://python.langchain.com/)
- [通义千问文档](https://help.aliyun.com/zh/dashscope/)

## 🎓 面试准备

### 如何介绍这个项目？

> "我做了一个企业差旅智能体项目，用LangChain复刻了之前的Spring AI版本。
>
> 核心功能是RAG问答系统，让AI能回答企业差旅规章的问题。我用FAISS做向量检索，通义千问做LLM，FastAPI提供API接口。
>
> 技术亮点是对比了Spring AI和LangChain的实现方式，理解了两个框架的设计理念。
>
> 通过这个项目，我深入理解了RAG的原理、向量检索的机制、以及如何设计AI应用的架构。"

### 常见面试问题

**Q：RAG和微调有什么区别？**
- RAG：检索外部知识，不改变模型
- 微调：训练模型，改变模型参数
- RAG成本低、更新快，微调效果好、成本高

**Q：如何提高RAG的准确率？**
1. 优化文档切分（chunk_size、overlap）
2. 改进检索策略（Top-K、阈值）
3. 优化Prompt模板
4. 使用更好的Embedding模型

## 🔧 技术栈

- **Python 3.10+**
- **LangChain** - AI应用开发框架
- **通义千问API** - 大语言模型
- **FAISS** - 向量数据库
- **FastAPI** - Web框架
- **Uvicorn** - ASGI服务器

## 📝 开发进度

- [x] 项目初始化
- [x] 环境搭建
- [x] LLM配置模块
- [x] RAG文档加载和切分
- [x] 向量存储和检索
- [x] RAG链组装
- [x] 天气查询工具
- [x] FastAPI接口
- [x] 测试文件
- [x] 实现指南文档
- [ ] 会话记忆功能（可选）
- [ ] Agent工作流（可选）
- [ ] 前端界面（可选）

## 🤝 贡献

欢迎提Issue和PR！

## 📄 许可证

MIT License

---

**开始时间**: 2026年5月11日  
**开发者**: Hiro & 主人  
**GitHub**: https://github.com/zsc140217/langchain-business-trip-management
