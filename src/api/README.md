# LangServe API - 企业差旅管理系统

基于LangChain和LangServe的生产级REST API，自动部署7个LangChain模块为可调用的Web服务。

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env，填写API密钥
# DASHSCOPE_API_KEY=your_key_here
```

### 2. 安装依赖

```bash
pip install -r requirements_api.txt
```

### 3. 启动服务

```bash
# 方式1: 直接运行
cd src
python -m api.main

# 方式2: 使用uvicorn（开发模式）
uvicorn api.main:app --reload --port 8000

# 方式3: 使用Docker
cd src/api
docker-compose up -d
```

### 4. 访问API

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **模块列表**: http://localhost:8000/modules

## 📦 已部署的模块

LangServe自动为每个模块生成3个端点：

| 模块 | invoke端点 | stream端点 | playground |
|------|-----------|-----------|------------|
| **Module 1: Simple RAG** | `/simple-rag/invoke` | `/simple-rag/stream` | `/simple-rag/playground` |
| **Module 2: Advanced RAG** | `/advanced-rag/invoke` | `/advanced-rag/stream` | `/advanced-rag/playground` |
| **Module 3: ReAct Agent** | `/react-agent/invoke` | `/react-agent/stream` | `/react-agent/playground` |
| **Module 4: Multi-Agent** | `/multi-agent/invoke` | `/multi-agent/stream` | `/multi-agent/playground` |
| **Module 5: Sequential Chain** | `/sequential-chain/invoke` | `/sequential-chain/stream` | `/sequential-chain/playground` |
| **Module 5: Parallel Chain** | `/parallel-chain/invoke` | `/parallel-chain/stream` | `/parallel-chain/playground` |
| **Module 6: Memory System** | `/memory-chain/invoke` | `/memory-chain/stream` | `/memory-chain/playground` |

## 🔧 API使用指南

### Module 1: Simple RAG - 简单检索增强生成

基于FAISS的文档检索问答系统。

**invoke调用 (同步)**
```bash
curl -X POST "http://localhost:8000/simple-rag/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "去上海出差住宿能报多少钱？"
     }'
```

**stream调用 (流式)**
```bash
curl -X POST "http://localhost:8000/simple-rag/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "去上海出差住宿能报多少钱？"
     }'
```

**Python调用**
```python
import requests

response = requests.post(
    "http://localhost:8000/simple-rag/invoke",
    json={"input": "去上海出差住宿能报多少钱？"}
)

print(response.json()["output"])
```

**JavaScript调用**
```javascript
const response = await fetch('http://localhost:8000/simple-rag/invoke', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    input: '去上海出差住宿能报多少钱？' 
  })
});

const result = await response.json();
console.log(result.output);
```

### Module 2: Advanced RAG - 高级检索增强

混合检索 + 重排序优化。

```bash
curl -X POST "http://localhost:8000/advanced-rag/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "出差期间的餐饮补贴标准是什么？"
     }'
```

### Module 3: ReAct Agent - 工具调用智能体

自主推理和工具调用，支持天气查询、航班搜索、酒店预订。

```bash
curl -X POST "http://localhost:8000/react-agent/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "我要去深圳出差，帮我查天气和订酒店"
     }'
```

**可用工具**:
- `get_weather` - 查询城市天气
- `search_flights` - 搜索航班信息
- `search_hotels` - 搜索酒店信息

### Module 4: Multi-Agent - 多智能体协作

LangGraph状态图编排，实现复杂任务的多智能体协作。

```bash
curl -X POST "http://localhost:8000/multi-agent/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "下周去杭州出差3天，帮我规划行程"
     }'
```

**工作流程**:
1. Supervisor分析任务
2. 分配给Worker agents (Policy, Weather, Itinerary)
3. 汇总结果
4. 返回完整方案

### Module 5: Sequential Chain - 顺序链

多步骤顺序执行，适合有依赖关系的任务。

```bash
curl -X POST "http://localhost:8000/sequential-chain/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "destination": "上海",
         "days": 3
       }
     }'
```

### Module 5: Parallel Chain - 并行链

多任务并行执行，提升性能（3-5倍加速）。

```bash
curl -X POST "http://localhost:8000/parallel-chain/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "destination": "深圳",
         "days": 2
       }
     }'
```

### Module 6: Memory System - 记忆系统

三层记忆架构，支持上下文对话。

```bash
curl -X POST "http://localhost:8000/memory-chain/invoke" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "我叫张三，下周要去北京出差"
     }'
```

**记忆层次**:
1. BufferMemory - 短期对话缓冲
2. SummaryMemory - 中期摘要记忆
3. VectorMemory - 长期向量检索

## 🧪 API测试

运行完整的API测试套件：

```bash
# 确保API服务已启动
python -m api.main

# 在另一个终端运行测试
cd src/api
python test_api.py
```

测试覆盖：
- ✓ 健康检查
- ✓ 模块列表
- ✓ 所有模块的invoke端点
- ✓ 所有模块的stream端点（可选）

## 🎮 交互式Playground

每个模块都有一个交互式测试界面，可在浏览器中直接测试：

1. **Simple RAG**: http://localhost:8000/simple-rag/playground
2. **Advanced RAG**: http://localhost:8000/advanced-rag/playground
3. **ReAct Agent**: http://localhost:8000/react-agent/playground
4. **Multi-Agent**: http://localhost:8000/multi-agent/playground
5. **Sequential Chain**: http://localhost:8000/sequential-chain/playground
6. **Parallel Chain**: http://localhost:8000/parallel-chain/playground
7. **Memory System**: http://localhost:8000/memory-chain/playground

Playground功能：
- 📝 输入测试数据
- ▶️ 执行invoke/stream调用
- 📊 查看实时结果
- 🔄 测试不同参数

## 🐳 Docker部署

### 使用Docker Compose（推荐）

```bash
cd src/api

# 创建.env文件
cp .env.example .env
# 编辑.env，填写DASHSCOPE_API_KEY

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### 使用Dockerfile

```bash
cd src/api

# 构建镜像
docker build -t langchain-api .

# 运行容器
docker run -d \
  --name langchain-api \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY=your_key \
  langchain-api

# 查看日志
docker logs -f langchain-api
```

## 📊 LangSmith可观测性

启用LangSmith追踪，监控所有API调用：

```bash
# .env文件中配置
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=business-trip-management
```

**追踪内容**:
- 🔍 每个请求的完整执行链路
- ⏱️ 每个步骤的耗时
- 💰 Token使用量和成本
- ⚠️ 错误和异常信息

访问 https://smith.langchain.com 查看追踪数据。

## 🔒 安全配置

### CORS配置

生产环境应限制允许的来源：

```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 修改为实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 环境变量

敏感信息通过环境变量配置，不要硬编码：

```bash
# 必需
DASHSCOPE_API_KEY=your_key

# 可选
LANGCHAIN_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
```

### 速率限制

生产环境建议添加速率限制：

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/simple-rag/invoke")
@limiter.limit("10/minute")
async def simple_rag_invoke(request: Request):
    # ...
```

## 📈 性能优化

### 缓存策略

使用`@lru_cache`缓存chain实例：

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_simple_rag_chain():
    # 只创建一次，后续请求复用
    return create_chain()
```

### 异步支持

所有端点支持异步处理：

```python
# invoke端点自动支持同步和异步
# stream端点支持SSE流式响应
```

### 并发配置

使用Gunicorn提升并发能力：

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

## 🛠️ 故障排查

### 问题1: API无法启动

**症状**: `ModuleNotFoundError`

**解决**:
```bash
# 确保在正确的目录
cd src

# 以模块方式运行
python -m api.main
```

### 问题2: 健康检查失败

**症状**: `/health` 返回 `degraded`

**解决**:
```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY

# 设置环境变量
export DASHSCOPE_API_KEY=your_key
```

### 问题3: 模块导入错误

**症状**: `ImportError: cannot import name 'xxx'`

**解决**:
```bash
# 检查所有依赖
pip install -r requirements_api.txt

# 重新安装LangServe
pip install --upgrade langserve
```

### 问题4: Docker构建失败

**症状**: 构建超时或依赖安装失败

**解决**:
```bash
# 使用国内镜像
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t langchain-api .
```

## 📚 相关文档

- [LangChain文档](https://python.langchain.com/)
- [LangServe文档](https://python.langchain.com/docs/langserve)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [LangSmith文档](https://docs.smith.langchain.com/)

## 🤝 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

MIT License

## 🎯 下一步计划

- [ ] 添加认证中间件（API Key / OAuth2）
- [ ] 实现请求速率限制
- [ ] 添加Prometheus监控指标
- [ ] 集成Grafana可视化面板
- [ ] 支持批量请求处理
- [ ] 添加WebSocket支持
- [ ] 实现请求缓存
- [ ] 添加更多单元测试

## 📞 联系方式

- 项目主页: [GitHub仓库链接]
- 问题反馈: [Issues链接]
- 邮件: your-email@example.com
