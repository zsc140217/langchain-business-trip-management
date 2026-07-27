# 统一通信层集成计划 - 渐进式改造方案

## 一、现状分析

### 1.1 前后端已联调的接口

**后端 API** (`src/api/unified_api.py`):
```python
@app.post("/api/unified/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest):
    # 调用 orchestrator.route() 返回 (answer, route)
    answer, route = orchestrator.route(query, user_id, conversation_id)
    
    return ChatResponse(
        answer=answer,
        route=route,
        user_id=request.user_id,
        conversation_id=request.conversation_id
    )
```

**前端调用** (`frontend/src/App.tsx`):
```typescript
const response = await fetch(`${API_BASE}/api/unified/chat`, {
    method: 'POST',
    body: JSON.stringify({
        query: input,
        user_id: userInfo?.user_id || 'employee',
        conversation_id: conversationId,
    })
})

const data = await response.json()
// 前端期望: data.answer, data.conversation_id
```

**关键观察**:
- ✅ 前端依赖 `data.answer` 字段
- ✅ 前端依赖 `data.conversation_id` 字段
- ✅ 响应格式已稳定
- ❌ **不能直接替换为 StandardResponse，会破坏前端**

### 1.2 其他端点

- `/health` - 健康检查（监控系统可能依赖）
- `/api/auth/login` - 认证（前端依赖）
- `/api/unified/stats` - 统计信息
- `/api/test/feishu` - 飞书测试

---

## 二、核心问题

### 问题1: 响应格式不兼容

**通信层 StandardResponse**:
```json
{
    "success": true,
    "code": "OK",
    "message": "Success",
    "data": {"answer": "...", "route": "..."},
    "trace_id": "trace_abc123",
    "duration_ms": 234.56
}
```

**前端期望的格式**:
```json
{
    "answer": "北京市一类地区住宿标准为500元/天",
    "route": "qa_domain",
    "user_id": "employee",
    "conversation_id": "conv_123"
}
```

**不兼容点**:
- 前端直接访问 `data.answer`，而不是 `data.data.answer`
- 前端不关心 `success`、`code`、`trace_id` 等字段
- 前端期望扁平结构，通信层是嵌套结构

### 问题2: OrchestratorAgent 返回值

**当前实现**:
```python
def route(self, query, user_id, conversation_id) -> Tuple[str, str]:
    # 返回 (answer, route)
    return answer, route
```

**通信层期望**:
```python
async def route(self, query, user_id, conversation_id) -> StandardResponse:
    # 返回 StandardResponse
    return StandardResponse.success_response(...)
```

**冲突**: 修改 OrchestratorAgent 的返回值会破坏所有调用点

---

## 三、改造策略对比

### 策略A: 激进改造（❌ 不推荐）

**方案**: 全面替换为 StandardResponse，前端同步修改

**优势**:
- 一次性完成，架构彻底统一

**劣势**:
- ❌ 破坏前后端联调成果
- ❌ 前端需要大量修改（所有 API 调用点）
- ❌ 回滚困难
- ❌ 风险极高

### 策略B: 适配器模式（✅ 推荐）

**方案**: 在 API 层添加适配器，内部使用通信层，外部保持原格式

**优势**:
- ✅ 前端零改动
- ✅ 向后兼容
- ✅ 渐进式迁移
- ✅ 可以随时回滚

**劣势**:
- 需要维护适配器代码（但很轻量）

### 策略C: 新旧并存（✅ 可选）

**方案**: 
- 保留 `/api/unified/chat` 旧格式
- 新增 `/api/v2/unified/chat` 使用 StandardResponse

**优势**:
- ✅ 完全无风险
- ✅ 新老系统可以共存
- ✅ 可以逐步迁移前端

**劣势**:
- 需要维护两套接口

---

## 四、最终方案（策略B + 策略C混合）

### 4.1 总体架构

```
前端请求 → FastAPI端点（保持旧格式）
              ↓
          适配器层（格式转换）
              ↓
          通信层（StandardRequest/Response）
              ↓
          域处理器（OrchestratorAgent等）
```

### 4.2 实施步骤

#### Phase 1: 内部集成（对外零影响）

**目标**: 在不改变 API 响应格式的前提下，内部使用通信层

**实施内容**:

1. **创建适配器模块** (`src/communication/adapters.py`):
```python
class LegacyAPIAdapter:
    """将通信层的StandardResponse转换为旧的API格式"""
    
    @staticmethod
    def to_chat_response(std_response: StandardResponse, conversation_id: str) -> dict:
        """转换为旧的ChatResponse格式"""
        if std_response.success:
            return {
                "answer": std_response.data.get("answer"),
                "route": std_response.data.get("route", ""),
                "user_id": std_response.data.get("user_id"),
                "conversation_id": conversation_id
            }
        else:
            # 错误情况：保持旧的异常抛出方式
            raise HTTPException(
                status_code=500,
                detail=std_response.message
            )
```

2. **改造 unified_api.py**（最小改动）:
```python
from src.communication import CommunicationLayer, event_bus
from src.communication.adapters import LegacyAPIAdapter

# 初始化通信层
comm_layer = CommunicationLayer(event_bus)

@app.post("/api/unified/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest):
    """保持旧格式，内部使用通信层"""
    
    # 通过通信层处理请求
    std_response = await comm_layer.handle_request(
        action="chat.query",
        payload={
            "query": request.query,
            "conversation_id": request.conversation_id
        },
        user_id=request.user_id,
        source="http"
    )
    
    # 适配器转换为旧格式（前端无感知）
    legacy_response = LegacyAPIAdapter.to_chat_response(
        std_response, 
        request.conversation_id
    )
    
    return ChatResponse(**legacy_response)
```

**效果**:
- ✅ 前端完全无感知
- ✅ 内部已使用通信层（TraceID、中间件、事件总线）
- ✅ 日志自动包含 TraceID
- ✅ 审批引擎可以发布事件

3. **注册域处理器**:
```python
async def chat_domain_handler(request: StandardRequest) -> StandardResponse:
    """聊天域处理器"""
    query = request.payload["query"]
    conversation_id = request.payload.get("conversation_id")
    
    # 调用原有的 orchestrator（不修改返回值）
    answer, route = orchestrator.route(
        query=query,
        user_id=request.context.user_id,
        conversation_id=conversation_id
    )
    
    return StandardResponse.success_response(
        data={
            "answer": answer,
            "route": route,
            "user_id": request.context.user_id
        },
        trace_id=request.context.trace_id
    )

# 启动时注册
comm_layer.register_domain_handler("chat", chat_domain_handler)
```

#### Phase 2: 事件驱动改造（飞书通知解耦）

**目标**: 审批引擎使用事件总线，解耦飞书客户端

**实施内容**:

1. **创建飞书事件处理器** (`src/harness/feishu_event_handlers.py`):
```python
from src.communication import event_bus, Event, EventType

async def handle_approval_approved(event: Event):
    """处理审批通过事件"""
    trace_id = event.trace_id
    payload = event.payload
    
    logger.info(f"[{trace_id}] Sending Feishu notification")
    
    if feishu_client:
        await feishu_client.send_approval_card(
            approval_id=payload["approval_id"],
            status="approved",
            amount=payload["amount"]
        )

# 注册订阅
event_bus.subscribe(EventType.APPROVAL_APPROVED, handle_approval_approved)
```

2. **修改 ApprovalEngine**（最小改动）:
```python
# 在审批完成后发布事件（不删除原有的飞书调用，先并行）
await event_bus.publish(Event(
    event_type=EventType.APPROVAL_APPROVED,
    payload={"approval_id": approval_id, "amount": amount},
    trace_id=TraceManager.get_trace_id(),
    timestamp=datetime.now(),
    source="approval_engine"
))

# 保留原有的飞书调用（双写，确保不丢消息）
# 待验证稳定后再删除
```

#### Phase 3: 新版本 API（可选）

**目标**: 提供新版本 API 供前端逐步迁移

**实施内容**:

1. **新增 v2 端点**:
```python
@app.post("/api/v2/unified/chat")
async def unified_chat_v2(request: ChatRequest):
    """v2版本，返回StandardResponse格式"""
    
    std_response = await comm_layer.handle_request(
        action="chat.query",
        payload={"query": request.query, "conversation_id": request.conversation_id},
        user_id=request.user_id,
        source="http"
    )
    
    # 直接返回StandardResponse格式
    return std_response.to_dict()
```

2. **前端可以选择性迁移**:
```typescript
// 旧版本（不变）
const data = await response.json()
const answer = data.answer

// 新版本（可选）
const data = await response.json()
if (data.success) {
    const answer = data.data.answer
    const traceId = data.trace_id  // 可用于问题追踪
}
```

---

## 五、改造优先级

### P0（必须，立即实施）

1. ✅ 创建适配器模块（1小时）
2. ✅ 改造 `/api/unified/chat` 端点使用通信层（2小时）
3. ✅ 注册域处理器（1小时）
4. ✅ 测试前端功能完全正常（1小时）

**验收标准**:
- 前端功能完全正常，无任何改动
- 后端日志包含 TraceID
- 响应格式与之前完全一致

### P1（重要，近期实施）

1. ⏳ 飞书事件处理器创建（2小时）
2. ⏳ ApprovalEngine 发布事件（双写模式）（2小时）
3. ⏳ 验证飞书通知正常（1小时）

**验收标准**:
- 审批通过后同时触发事件和原有调用
- 飞书通知正常发送
- 可以逐步移除原有的直接调用

### P2（可选，长期规划）

1. ⏳ 新增 `/api/v2/*` 端点（3小时）
2. ⏳ 前端逐步迁移到 v2（前端团队）
3. ⏳ 完全移除旧格式（待所有客户端迁移完成）

---

## 六、风险控制

### 6.1 回滚方案

**如果出现问题，可以立即回滚**:

```python
# unified_api.py - 回滚开关
USE_COMMUNICATION_LAYER = os.getenv("USE_COMMUNICATION_LAYER", "false") == "true"

@app.post("/api/unified/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest):
    if USE_COMMUNICATION_LAYER:
        # 新实现：使用通信层
        std_response = await comm_layer.handle_request(...)
        return LegacyAPIAdapter.to_chat_response(std_response, ...)
    else:
        # 旧实现：直接调用
        answer, route = orchestrator.route(...)
        return ChatResponse(answer=answer, route=route, ...)
```

**回滚步骤**:
1. 设置环境变量 `USE_COMMUNICATION_LAYER=false`
2. 重启服务
3. 验证功能正常

### 6.2 灰度发布

**建议采用灰度策略**:
- 10% 流量使用通信层（设置随机概率）
- 监控错误率和响应时间
- 逐步提升到 50% → 100%

### 6.3 监控指标

**需要监控的关键指标**:
- 响应时间变化（预期 <10ms 增加）
- 错误率（应保持不变）
- TraceID 覆盖率（应达到 100%）
- 事件发布成功率（应达到 100%）

---

## 七、时间估算

| 阶段 | 工作内容 | 工作量 | 风险 |
|-----|---------|-------|------|
| P0 | 适配器 + 端点改造 + 测试 | 5小时 | 低 |
| P1 | 事件驱动改造 | 5小时 | 低 |
| P2 | v2 API（可选） | 3小时 | 无 |
| **总计** | **P0+P1** | **10小时（约1.5天）** | **低** |

---

## 八、与文档的对应关系

本计划是 `docs/COMMUNICATION_LAYER_IMPLEMENTATION_REPORT.md` 的实施细化：

- **Phase 1（已完成）**: 通信层核心模块实现 ✅
- **Phase 2（本计划）**: 现有 API 改造 ⏳
  - 采用适配器模式（与文档 8.2-8.5 对应）
  - 但保持向后兼容（文档未强调，本计划补充）
- **Phase 3（未来）**: 生产环境准备（文档 11.2）

**关键区别**:
- 文档建议直接替换为 StandardResponse
- 本计划采用适配器模式，保持前端零改动
- 更安全、更渐进、更符合生产实践

---

## 九、决策点

### 需要用户确认的问题

1. **是否接受适配器模式？**
   - 优势: 前端零改动，风险极低
   - 劣势: 需要维护适配器代码（约50行）

2. **是否需要 v2 API？**
   - 如果前端短期内不计划改造，可以暂时不做
   - 如果未来有新客户端，建议提供

3. **灰度发布比例？**
   - 建议: 10% → 50% → 100%
   - 还是直接 100%（如果对测试有信心）

4. **飞书通知改造时机？**
   - 立即改造（P1）
   - 还是先验证 P0 稳定后再改

---

## 十、推荐方案

**我的建议**:

1. **立即实施 P0**（5小时）
   - 创建适配器
   - 改造 `/api/unified/chat`
   - 前端零改动
   - 充分测试

2. **验证稳定后实施 P1**（5小时）
   - 飞书事件驱动改造
   - 双写模式（事件 + 原有调用）
   - 验证1周后移除原有调用

3. **暂不实施 P2**
   - 等前端有需求时再考虑
   - 或者有新客户端时再提供

**理由**:
- ✅ 风险最低（前端无感知）
- ✅ 收益最大（TraceID、中间件、事件总线）
- ✅ 可以随时回滚
- ✅ 符合渐进式重构最佳实践

---

**计划完成时间**: 2026-07-21  
**计划作者**: Claude (Opus 4.8)  
**状态**: 待用户确认
