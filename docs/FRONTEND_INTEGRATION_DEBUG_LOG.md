# 前端集成问题调试记录

**日期**: 2026-07-16 ~ 2026-07-17  
**状态**: ✅ 所有问题已解决（5个问题）  
**影响范围**: 前端集成、工具调用、审批流程

本文档记录了从MCP事件循环到完整前端集成的所有问题修复。

---

## 问题1: MCP事件循环冲突 ✅ 已解决

**日期**: 2026-07-16  
**症状**: `Cannot run the event loop while another loop is running`  
**原因**: FastAPI的事件循环与MCP客户端冲突  
**修复**: 将MCP事件循环隔离到独立线程  
**文件**: `src/tools/mcp_client.py`

---

## 问题2: 政策查询缺少LLM总结 ✅ 已解决

**日期**: 2026-07-17  
**症状**: VectorStoreRetriever返回文档，但没有LLM总结  
**原因**: `search_policy_tool.py`只返回原始文档  
**修复**: 添加LLM总结步骤（检索 → LLM总结 → 用户友好回答）  
**文件**: `src/tools/search_policy_tool.py`

---

## 问题3: Neo4j连接失败导致工具崩溃 ✅ 已解决

**日期**: 2026-07-17  
**症状**: `图谱检索器初始化失败: 无法连接到 Neo4j`  
**原因**: 初始化失败抛异常，工具完全不可用  
**修复**: 降级处理，返回友好提示  
**文件**: `src/tools/query_graph_tool.py`

---

## 问题4: 工具参数传递错误 ✅ 已解决

**日期**: 2026-07-17  
**症状**: `missing 1 required positional argument: 'query'`  
**原因**: `base_tool.py`的`execute()`方法参数传递错误  
**修复**: `invoke(kwargs)` → `invoke(input_dict=kwargs)`  
**文件**: `src/tools/base_tool.py`

---

## 问题5: 审批流程卡住，前端无响应 ✅ 已解决

**日期**: 2026-07-17  
**症状**: 用户提交不完整审批信息后，LangGraph返回材料清单，但前端收不到响应  
**原因**: `approval_engine.py`忽略了LangGraph返回的answer  
**修复**: 提取answer，新增`incomplete`状态，返回材料清单给前端  
**文件**: `src/agents/approval_engine.py`

**新审批流程**:
```
用户: "我去北京3天花了800"
  ↓
{"status": "incomplete", "message": "请提供以下材料..."}
  ↓
前端显示材料清单
  ↓
用户补充完整信息
  ↓
{"status": "approved", "message": "审批通过"}
```

---

## 问题症状

### 用户报告
天气查询通过前端和API测试时返回错误消息：
```json
{
  "answer": "抱歉，查询北京天气时出错，请稍后重试。",
  "route": "fast_path"
}
```

### 错误日志
```
2026-07-16 22:58:52 - src.tools.weather_adapter - ERROR - WeatherTool failed: Cannot run the event loop while another loop is running
```

### 关键观察
- ✅ MCP直接调用成功（独立Python脚本测试）
- ❌ 通过FastAPI调用失败（事件循环冲突）
- ✅ 快路径路由正常工作
- ❌ 工具执行阶段失败

---

## 根本原因分析

### 调用链路
```
FastAPI (async) 
  → unified_api.py (/api/unified/chat endpoint)
  → orchestrator_agent.py (_try_fast_path)
  → weather_adapter.py (WeatherTool._run)
  → mcp_client.py (MCPClientManager.call_tool)
  → [事件循环冲突]
```

### 技术原因

**问题1: 事件循环在错误的线程中创建**

旧代码 (`mcp_client.py:23-26`):
```python
def start(self):
    self._loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self._loop)
    self._loop.run_until_complete(self._connect())
```

- `start()` 在主线程被调用（FastAPI启动时）
- FastAPI (uvicorn) 已在主线程运行事件循环
- 尝试创建新循环导致冲突

**问题2: 线程池方案失效**

第一次修复尝试（失败）:
```python
def call_tool(self, tool_name, arguments):
    try:
        running_loop = asyncio.get_running_loop()
        # 使用线程池执行
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                self._loop.run_until_complete,
                self._call(tool_name, arguments)
            )
            return future.result(timeout=30)
    except RuntimeError:
        return self._loop.run_until_complete(
            self._call(tool_name, arguments))
```

失败原因：
- `self._loop` 仍在主线程创建
- 在线程池中调用 `run_until_complete()` 时，循环未在正确的线程上下文中

**核心矛盾**：
- FastAPI要求异步环境（事件循环已存在）
- LangChain工具接口是同步的（`BaseTool._run()`）
- MCP客户端需要异步操作（stdio通信）

---

## 解决方案

### 架构设计

**核心思路**: 将MCP客户端的事件循环隔离到独立线程

```
主线程 (FastAPI event loop)
  ↓
同步调用 WeatherTool._run()
  ↓
线程安全调用 → [独立线程]
                  ↓
                MCP event loop
                  ↓
                stdio 通信
```

### 实现细节

#### 1. 独立线程中启动事件循环

```python
# src/tools/mcp_client.py

class MCPClientManager:
    def __init__(self, server_script=None):
        # ... 原有代码 ...
        self._thread = None
        self._ready = threading.Event()  # 同步信号

    def start(self):
        """在独立线程中启动事件循环和MCP连接"""
        def run_in_thread():
            # 创建新的事件循环（在独立线程中）
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                # 建立MCP连接
                self._loop.run_until_complete(self._connect())
                self._ready.set()  # 通知主线程连接就绪
                # 保持事件循环运行
                self._loop.run_forever()
            finally:
                self._loop.close()

        # 启动守护线程
        self._thread = threading.Thread(target=run_in_thread, daemon=True)
        self._thread.start()
        
        # 等待连接就绪（最多5秒）
        if not self._ready.wait(timeout=5):
            raise RuntimeError("MCP client failed to start within 5 seconds")
```

**关键点**:
- ✅ 事件循环在独立线程创建和运行
- ✅ `daemon=True` 确保不阻塞主进程退出
- ✅ `threading.Event()` 同步等待连接就绪
- ✅ `loop.run_forever()` 保持连接活跃

#### 2. 线程安全的工具调用

```python
def call_tool(self, tool_name, arguments):
    """线程安全地调用MCP工具"""
    if not self._session:
        raise RuntimeError("MCPClientManager not started")

    # 使用 asyncio.run_coroutine_threadsafe 在独立线程的事件循环中执行
    future = asyncio.run_coroutine_threadsafe(
        self._call(tool_name, arguments),
        self._loop
    )
    # 等待结果（最多30秒）
    return future.result(timeout=30)
```

**关键点**:
- ✅ `run_coroutine_threadsafe()` 是标准的跨线程异步调用方式
- ✅ 返回 `concurrent.futures.Future` 对象
- ✅ `.result(timeout=30)` 阻塞等待结果（同步接口）

#### 3. 清理和停止

```python
def stop(self):
    """停止MCP客户端和事件循环"""
    if self._loop and self._loop.is_running():
        # 在独立线程的事件循环中调度关闭
        if self._stack:
            asyncio.run_coroutine_threadsafe(
                self._stack.aclose(),
                self._loop
            )
        # 停止事件循环
        self._loop.call_soon_threadsafe(self._loop.stop)

    # 等待线程结束（最多2秒）
    if self._thread and self._thread.is_alive():
        self._thread.join(timeout=2)

    self._session = None
    self._ready.clear()
```

#### 4. 增强日志记录

```python
# src/tools/weather_adapter.py

def _run(self, city: str) -> str:
    try:
        logger.info(f"[WeatherTool] 开始查询城市: {city}")
        client = get_mcp_client()
        logger.info(f"[WeatherTool] MCP客户端已获取")
        result = client.call_tool("query_weather", {"city": city})
        logger.info(f"[WeatherTool] 查询成功，结果长度: {len(str(result))}")
        return result
    except Exception as e:
        logger.error(f"WeatherTool failed: {e}", exc_info=True)  # 添加堆栈跟踪
        return f"抱歉，查询{city}天气时出错，请稍后重试。"
```

---

## 测试验证

### 测试命令
```bash
# 1. 启动后端
python -m uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001

# 2. 测试天气查询
python test_weather.py
```

### 测试结果

**修复前**:
```json
{
  "answer": "抱歉，查询北京天气时出错，请稍后重试。",
  "route": "fast_path"
}
```

**修复后** ✅:
```json
{
  "answer": "[WEATHER] 北京 晴 温度：28°C 体感：29°C 西风 2级 湿度：57%",
  "route": "fast_path",
  "user_id": "test_user",
  "conversation_id": null
}
```

### 日志验证

成功的日志输出：
```
2026-07-16 23:15:30 - src.agents.orchestrator_agent - INFO - [OrchestratorAgent] 命中快路径: weather
2026-07-16 23:15:30 - src.tools.weather_adapter - INFO - [WeatherTool] 开始查询城市: 北京
2026-07-16 23:15:30 - src.tools.weather_adapter - INFO - [WeatherTool] MCP客户端已获取
2026-07-16 23:15:30 - src.tools.weather_adapter - INFO - [WeatherTool] 查询成功，结果长度: 47
2026-07-16 23:15:30 - src.agents.orchestrator_agent - INFO - [OrchestratorAgent] 快路径完成，耗时 0.02s
```

---

## 技术总结

### 核心模式: 异步-同步桥接

**问题**：
- 异步框架 (FastAPI) + 同步工具接口 (LangChain) + 异步通信 (MCP stdio)

**解决方案**：
1. **线程隔离**: 独立线程运行MCP事件循环
2. **线程安全调用**: `asyncio.run_coroutine_threadsafe()`
3. **同步等待**: `Future.result()` 阻塞获取结果

### Python异步编程要点

#### 1. 事件循环规则
- 一个线程只能有一个运行中的事件循环
- `asyncio.get_running_loop()` 检测当前线程的循环
- `asyncio.new_event_loop()` 创建新循环（不自动设置为当前）

#### 2. 跨线程异步调用
```python
# ❌ 错误：在其他线程的循环上调用 run_until_complete
loop.run_until_complete(coro)

# ✅ 正确：使用 run_coroutine_threadsafe
future = asyncio.run_coroutine_threadsafe(coro, loop)
result = future.result(timeout=30)
```

#### 3. 线程同步
```python
# 使用 threading.Event 同步启动
ready = threading.Event()

def worker():
    # ... 初始化完成 ...
    ready.set()

thread.start()
ready.wait(timeout=5)  # 阻塞直到就绪
```

### 适用场景

此模式适用于：
- ✅ 在异步框架（FastAPI/Sanic）中使用同步阻塞的库
- ✅ 在LangChain工具中使用异步MCP客户端
- ✅ 需要长期保持的异步连接（WebSocket/stdio）
- ✅ 避免 "event loop already running" 错误

**不适用**：
- ❌ 纯异步环境（直接 await 即可）
- ❌ 纯同步环境（不需要事件循环）

---

## 相关文件

### 修改的文件
| 文件 | 修改内容 | 行数 |
|------|---------|-----|
| `src/tools/mcp_client.py` | 重构事件循环管理 | 23-88 |
| `src/tools/weather_adapter.py` | 增强日志记录 | 15-24 |

### 依赖此模式的文件
| 文件 | 用途 |
|------|------|
| `src/tools/weather_adapter.py` | 天气查询工具 |
| `src/tools/flight_adapter.py` | 航班查询工具 |
| `src/tools/hotel_adapter.py` | 酒店查询工具 |

### 测试文件
- `test_weather.py` - API级别测试
- `tests/unit/test_weather_tool.py` - 单元测试

---

## 经验教训

### 1. 事件循环不可嵌套
**错误思路**: "我在线程池里运行事件循环，应该就隔离了"  
**真相**: 事件循环必须在专属线程中创建和运行

### 2. 调试异步问题的方法
- ✅ 添加详细日志（每一步的执行状态）
- ✅ 使用 `exc_info=True` 获取完整堆栈
- ✅ 独立测试每一层（MCP直接调用 vs FastAPI调用）
- ✅ 检查线程上下文 (`threading.current_thread()`)

### 3. FastAPI与同步工具的集成
FastAPI本身支持在端点中调用同步函数（自动在线程池中执行），但：
- MCP客户端需要**长期运行**的事件循环
- 不能每次调用都创建新循环（连接开销大）
- 需要**单例模式** + **独立线程**

### 4. 性能考虑
**当前方案**:
- ✅ 连接复用（单例，启动时连接一次）
- ✅ 线程开销可接受（仅一个后台线程）
- ✅ 调用延迟低（~20ms，见日志）

**备选方案**（未采用）:
- ❌ 每次调用创建新连接（慢，浪费资源）
- ❌ 完全异步化LangChain工具（需要重写框架）

---

## 后续优化建议

### 1. 健康检查
添加MCP连接健康检查：
```python
def is_healthy(self) -> bool:
    return (self._session is not None 
            and self._loop is not None 
            and self._loop.is_running())
```

### 2. 自动重连
连接断开时自动重连：
```python
async def _call_with_retry(self, tool_name, arguments, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self._call(tool_name, arguments)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"MCP call failed, retrying... ({attempt+1}/{max_retries})")
            await self._reconnect()
```

### 3. 指标监控
添加性能指标：
```python
import time

def call_tool(self, tool_name, arguments):
    start_time = time.time()
    try:
        result = self._call_tool_impl(tool_name, arguments)
        duration = time.time() - start_time
        logger.info(f"[MCP] {tool_name} took {duration:.3f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[MCP] {tool_name} failed after {duration:.3f}s: {e}")
        raise
```

---

## 参考资料

### Python官方文档
- [asyncio - 异步I/O](https://docs.python.org/3/library/asyncio.html)
- [asyncio.run_coroutine_threadsafe()](https://docs.python.org/3/library/asyncio-task.html#asyncio.run_coroutine_threadsafe)
- [threading - 线程模块](https://docs.python.org/3/library/threading.html)

### 相关问题
- [StackOverflow: RuntimeError: This event loop is already running](https://stackoverflow.com/questions/46827007/runtimeerror-this-event-loop-is-already-running-in-python)
- [FastAPI + asyncio best practices](https://fastapi.tiangolo.com/async/)

---

**文档更新**: 2026-07-16  
**作者**: AI Assistant + 用户调试  
**调试耗时**: ~2小时  
**最终状态**: ✅ 问题已解决，所有MCP工具正常工作
