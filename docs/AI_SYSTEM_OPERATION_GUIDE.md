# AI系统操作指南 (For AI Agents)

> 本文档专为AI助手设计，提供系统架构、启动流程、故障排查和维护指南

## 📋 目录

1. [系统架构概览](#系统架构概览)
2. [快速启动流程](#快速启动流程)
3. [核心组件说明](#核心组件说明)
4. [常见问题排查](#常见问题排查)
5. [开发与调试](#开发与调试)
6. [API使用指南](#api使用指南)

---

## 系统架构概览

### 技术栈
- **后端框架**: FastAPI (Python 3.12)
- **LLM**: 通义千问 (qwen3.7-plus)
- **向量数据库**: FAISS + DashScope Embeddings
- **MCP服务器**: 独立线程运行的工具服务器
- **前端**: React + Vite + TypeScript
- **监控**: LangSmith + Prometheus

### 核心架构层次
```
用户请求
    ↓
FastAPI (unified_api.py)
    ↓
OrchestratorAgent (路由层)
    ↓
┌─────────────┬─────────────┐
│  QA Domain  │  Approval   │
│             │   Domain    │
└─────────────┴─────────────┘
        ↓              ↓
    MCP Tools    Approval Engine
```

### 关键路径
1. **请求入口**: `src/api/unified_api.py:unified_chat()`
2. **路由决策**: `src/agents/orchestrator_agent.py:route()`
3. **工具调用**: `src/tools/mcp_client.py` → MCP Server
4. **响应合成**: `src/agents/qa_engine.py` 或 `src/agents/approval_engine.py`

---

## 快速启动流程

### 前置条件检查
```bash
# 1. 验证Python环境
python --version  # 应为 3.12+

# 2. 检查依赖
pip list | grep -E "fastapi|langchain|dashscope"

# 3. 验证环境变量
echo $DASHSCOPE_API_KEY
echo $FEISHU_WEBHOOK_KEY
echo $LANGCHAIN_API_KEY
```

### 启动后端服务

**方法1: 直接启动 (推荐用于开发)**
```bash
cd E:/Desktop/langchain-business-trip-management
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload
```

**方法2: 后台启动**
```bash
cd E:/Desktop/langchain-business-trip-management
nohup uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
```

### 验证服务状态
```bash
# 健康检查
curl http://localhost:8001/health

# 预期响应
{
  "status": "healthy",
  "components": {
    "orchestrator": true,
    "memory_service": true,
    "feishu_client": true
  }
}
```

---

## 核心组件说明

### 1. MCP客户端 (`src/tools/mcp_client.py`)

**设计原理**: 
- 在**独立线程**中运行专属事件循环
- 通过 `asyncio.run_coroutine_threadsafe()` 实现线程安全调用
- 避免与FastAPI主事件循环冲突

**关键类**: `MCPClientManager`
```python
# 启动流程
def start(self):
    # 创建后台线程
    self._thread = threading.Thread(target=self._run_loop, daemon=True)
    self._thread.start()

# 调用工具
def call_tool(self, tool_name, arguments):
    future = asyncio.run_coroutine_threadsafe(
        self._call(tool_name, arguments),
        self._loop
    )
    return future.result(timeout=10)
```

**支持的工具**:
- `search_hotels` - 酒店查询
- `query_weather` - 天气查询
- `search_flights` - 航班查询

**调试MCP连接**:
```python
from src.tools.mcp_client import get_mcp_client

client = get_mcp_client()
# 等待初始化完成 (最多5秒)
import time
time.sleep(5)

# 测试调用
result = client.call_tool("query_weather", {"city": "北京"})
print(result)
```

### 2. 路由层 (`src/agents/orchestrator_agent.py`)

**路由决策流程**:
```
1. 加载用户记忆上下文
2. 检查是否为审批域查询 (关键词匹配)
   - 关键词: "报销", "申请", "审批", "提交"
3. 尝试快路径匹配 (规则引擎)
   - 天气: "天气", "温度"
   - 酒店: "酒店", "住宿"
   - 航班: "航班", "机票"
4. 默认路由到Q&A域
```

### 3. 工具定义规范

**关键点**: 所有工具必须定义 `args_schema`

```python
from pydantic import BaseModel, Field
from src.tools.base_tool import BaseTool

class MyToolInput(BaseModel):
    """输入参数定义"""
    param: str = Field(description="参数说明")

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "工具描述"
    args_schema: type[BaseModel] = MyToolInput  # 必须！
    
    def _run(self, param: str) -> str:
        # 实现逻辑
        return "result"
```

---

## 常见问题排查

### 问题1: MCP工具调用失败

**症状**:
```
RuntimeError: Cannot run the event loop while another loop is running
```

**原因**: 事件循环冲突

**解决方案**:
1. 确认使用的是修复后的 `mcp_client.py` (线程模式)
2. 检查是否有其他代码直接调用 `asyncio.run()`
3. 重启后端服务清除旧进程

**验证**:
```bash
# 检查MCP客户端版本
grep -A 5 "class MCPClientManager" src/tools/mcp_client.py
# 应包含 "threading.Thread" 字样
```

### 问题2: 工具参数错误

**症状**:
```
HotelTool._run() got an unexpected keyword argument 'query'
```

**原因**: 缺少 `args_schema` 定义

**解决方案**:
```python
# 确保所有工具都有 args_schema
class HotelTool(BaseTool):
    args_schema: type[BaseModel] = HotelSearchInput  # 必须！
```

### 问题3: 服务启动缓慢

**症状**: 启动超过30秒

**可能原因**: 
1. FAISS向量库加载慢
2. MCP客户端初始化超时
3. 飞书WebSocket连接失败

**解决方案**:
```bash
# 禁用飞书WebSocket (如不需要)
# 在 .env 中设置
ENABLE_FEISHU_WS=false
```

### 问题4: API响应超时

**症状**: 请求超过60秒无响应

**排查步骤**:
```bash
# 1. 查看实时日志
tail -f backend.log | grep -E "ERROR|timeout"

# 2. 测试单个工具
python -c "
from src.tools.hotel_adapter import HotelTool
tool = HotelTool()
result = tool._run(city='北京')
print(result)
"
```

---

## API使用指南

### 核心接口

#### 1. 统一对话接口
```http
POST /api/unified/chat
Content-Type: application/json

{
  "query": "帮我查北京的酒店",
  "user_id": "user123",
  "conversation_id": "conv456"
}
```

**响应**:
```json
{
  "answer": "为您查询到北京的酒店...",
  "route": "qa_domain",
  "user_id": "user123",
  "conversation_id": "conv456"
}
```

#### 2. 健康检查
```http
GET /health
```

#### 3. 接口文档
```http
GET /docs  # Swagger UI
GET /redoc  # ReDoc
```

### 测试脚本示例

**Python测试**:
```python
import requests

def test_hotel_query():
    url = "http://localhost:8001/api/unified/chat"
    payload = {
        "query": "北京有什么五星级酒店",
        "user_id": "test_user"
    }
    
    response = requests.post(url, json=payload, timeout=60)
    result = response.json()
    
    assert response.status_code == 200
    assert "酒店" in result["answer"]
    
    return result

if __name__ == "__main__":
    result = test_hotel_query()
    print(f"Route: {result['route']}")
    print(f"Answer: {result['answer'][:200]}...")
```

**Shell测试**:
```bash
#!/bin/bash
# test_api.sh

BASE_URL="http://localhost:8001"

# 测试健康检查
curl -s ${BASE_URL}/health | jq .

# 测试酒店查询
curl -s -X POST ${BASE_URL}/api/unified/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"北京酒店推荐","user_id":"test"}' | jq .
```

---

## 快速参考

### 环境变量清单

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | ✓ | 通义千问API密钥 |
| `LANGCHAIN_API_KEY` | ✓ | LangSmith追踪密钥 |
| `LANGCHAIN_TRACING_V2` | ✓ | 启用LangSmith追踪 |
| `FEISHU_WEBHOOK_KEY` | - | 飞书通知密钥 |

### 关键目录

```
langchain-business-trip-management/
├── src/
│   ├── api/
│   │   └── unified_api.py          # FastAPI入口
│   ├── agents/
│   │   ├── orchestrator_agent.py   # 路由层
│   │   ├── qa_engine.py            # Q&A引擎
│   │   └── approval_engine.py      # 审批引擎
│   ├── tools/
│   │   ├── mcp_client.py           # MCP客户端 (关键)
│   │   ├── hotel_adapter.py        # 酒店工具
│   │   ├── weather_adapter.py      # 天气工具
│   │   └── flight_adapter.py       # 航班工具
│   ├── memory/
│   │   └── memory_service.py       # 记忆服务
│   └── mcp/
│       └── trip_tools_server.py    # MCP服务器
└── frontend/
    └── src/
        └── components/
            └── ChatInterface.tsx   # 聊天界面
```

### 常用命令

```bash
# 启动后端
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload

# 启动前端
cd frontend && npm run dev

# 健康检查
curl http://localhost:8001/health

# 停止所有服务
tasklist | findstr python | awk '{print $2}' | xargs -I {} taskkill //F //PID {}
```

---

**文档版本**: v1.0  
**最后更新**: 2026-07-17  
**状态**: ✅ MCP功能已修复并验证通过
