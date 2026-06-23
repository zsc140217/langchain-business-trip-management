# 模块2今日实施计划（2026-06-23）

## ✅ Phase 1 完成总结（Dify + 飞书集成成功）

### 实际完成方案

**架构**：
```
Dify Chatflow → Workflow API → 审批引擎 → lark_notify 插件 → 飞书群 Webhook
```

**核心配置**：
- 飞书 App ID: `cli_aa8759bff078dcbd`
- 飞书 Webhook Key: `557e5b9b-e431-486f-a26c-2b0509b73437`
- Dify 公网地址: `https://kvxv3x7b-80.inc1.devtunnels.ms/`（VS Code 端口转发）
- 插件: lark_notify v0.0.1（Dify Marketplace）

**测试结果**：
- ✅ Chatflow 意图识别成功
- ✅ Workflow 审批引擎执行成功（并行 LLM）
- ✅ lark_notify 推送消息到飞书群成功
- ✅ 飞书群收到格式化卡片消息

**方案特点**：
- ✅ 单向推送（Dify → 飞书）
- ✅ 无需额外服务部署
- ❌ 不支持双向对话（用户不能在飞书中发起聊天）

---

## 📚 技术讲解

### 1. Webhook 原理

**定义**: Webhook 是"反向 API"，服务器在事件发生时主动推送数据到指定 URL。

| 特性 | 传统 API（轮询） | Webhook（推送） |
|------|----------------|----------------|
| 通信方向 | 客户端主动请求 | 服务器主动通知 |
| 实时性 | 需要轮询，有延迟 | 事件触发，实时 |
| 资源消耗 | 高（频繁请求） | 低（按需推送） |

**飞书群机器人 Webhook**：
- URL 格式: `https://open.feishu.cn/open-apis/bot/v2/hook/{key}`
- 使用方式: 在飞书群添加自定义机器人 → 获取 Webhook → POST 消息

### 2. 端口转发（Port Forwarding）

**问题**: Dify 运行在本地 `localhost:80`，飞书服务器无法访问。

**解决**: VS Code Dev Tunnels 端口转发

**原理**:
```
外部请求 → 微软云端服务器 → 本地 VS Code 代理 → localhost:80
```

**操作步骤**:
1. VS Code 打开项目
2. 按 `Ctrl+\`` 打开终端 → 切换到 "端口" 标签
3. 点击 "转发端口" → 输入 `80`
4. 右键端口 → "端口可见性" → "Public"
5. 复制生成的公网 URL

**其他工具对比**:
- VS Code Dev Tunnels: ✅ 无需安装，稳定
- ngrok: 功能强大，需注册
- localtunnel: 快速但不稳定
- Cloudflare Tunnel: 安全，配置复杂

### 3. Dify 变量引用

**语法**: `{{#节点名.变量名#}}`

**示例**: `{{#解析审批结果.message#}}` 引用 "解析审批结果" 节点的 `message` 输出。

---

## Phase 1：Dify快速验证（2小时）- 原计划

### Step 1.1：飞书开放平台准备（10分钟）

1. 访问：https://open.feishu.cn/
2. 注册并登录（手机号验证）
3. 创建企业自建应用：
   - 应用名称：差旅审批助手
   - 描述：基于LLM的智能差旅审批系统

### Step 1.2：配置飞书应用权限（10分钟）

进入应用管理页面，开通以下权限：
- ✅ 接收消息 v2.0（`im:message`）
- ✅ 获取用户信息（`contact:user.base:readonly`）
- ✅ 发送消息（`im:message:send_as_bot`）

### Step 1.3：Dify配置飞书渠道（10分钟）

回到Dify项目：
1. 进入「差旅审批助手」应用
2. 点击右上角「发布」按钮
3. 选择「飞书机器人」
4. 填入飞书应用凭证：
   - App ID：从飞书开放平台复制
   - App Secret：从飞书开放平台复制
5. 配置事件订阅URL（Dify会自动生成）
6. 验证连接

### Step 1.4：测试多轮对话（30分钟）

**测试用例1：信息补全（多轮）**
```
你：我要出差
Bot：请问您要去哪个城市？
你：上海
Bot：请问出差时间是？
你：下周一到周三
Bot：请问出差目的是？
你：拜访客户
Bot：[返回审批结果]
```

**观察要点**：
- [ ] Dify如何存储会话上下文？
- [ ] 会话ID在哪里？（飞书的conversation_id）
- [ ] 上下文保持了多久？
- [ ] 如何清除会话？

**测试用例2：中断恢复**
```
你：我要去北京出差
Bot：请问出差时间是？
[等待5分钟不回复]
你：下周一到周五
Bot：是否能记住"北京"？
```

**观察要点**：
- [ ] 会话超时时间是多少？
- [ ] 超时后是否保留状态？

### Step 1.5：理解Dify的会话管理（30分钟）

在Dify控制台观察：
1. 打开「日志与标注」
2. 查看每条消息的详细信息
3. 重点关注：
   - `conversation_id`：会话标识
   - `inputs`：用户输入
   - `outputs`：Bot输出
   - `message_files`：附件处理

**记录学习要点**：
```markdown
### Dify会话管理机制
- 会话ID生成规则：[填写]
- 上下文存储方式：[填写]
- 会话过期时间：[填写]
- 消息去重机制：[填写]
```

### Step 1.6：测试异步处理（20分钟）

在飞书发送一个复杂查询：
```
对比北京、上海、深圳三个城市的差旅标准
```

**观察要点**：
- [ ] Bot是否立即回复"处理中"？
- [ ] 实际处理时间多久？
- [ ] Dify的`response_mode`是什么？（blocking / streaming）

### Step 1.7：总结Dify经验（20分钟）

创建学习笔记：`learning/dify_feishu_integration_notes.md`

**总结内容**：
1. 飞书事件订阅机制
2. Dify的会话管理设计
3. 消息去重和幂等性
4. 超时处理策略
5. 迁移到LangChain的关键点

---

## Phase 2：LangChain 实现（基于 Dify 成功经验优化）

### 方案对比：从 Dify 学到的教训

| 功能 | Dify 方案（已完成） | LangChain 优化方案 |
|------|-------------------|-------------------|
| 消息推送 | lark_notify 插件 → 群 Webhook | 同样使用群 Webhook（简单） |
| 双向对话 | ❌ 不支持 | ✅ FastAPI + 事件订阅 |
| 会话管理 | 内置（Chatflow 自动） | PostgreSQL Checkpointing |
| 队列 | 不需要（单向推送） | 可选（异步优化） |

### 架构设计 V2（简化版，基于实际需求）

#### 方案 A：单向推送（最快，推荐先实现）

```
用户触发（Web/API）
  ↓
FastAPI 接口
  ↓
LangGraph ReAct Agent
  ↓
飞书群 Webhook（直接 POST）
  ↓
飞书群消息
```

**优点**：
- ✅ 无需 Redis 队列
- ✅ 无需飞书事件订阅
- ✅ 1-2 小时完成
- ✅ 复用现有 LangGraph

**缺点**：
- ❌ 用户不能在飞书发起对话

#### 方案 B：双向对话（完整版）

```
飞书用户发消息
  ↓
飞书事件订阅 → FastAPI Webhook
  ↓
LangGraph ReAct Agent（thread_id = conversation_id）
  ↓
飞书 Send Message API
  ↓
用户收到回复
```

**优点**：
- ✅ 完整双向对话
- ✅ 多轮会话管理

**缺点**：
- ⏱️ 需要配置飞书事件订阅（复杂）
- ⏱️ 需要实现签名验证
- ⏱️ 3-4 小时完成

### Step 2.1：技术选型（基于 Dify 经验修正）

**决策1：先实现哪个方案？**
- 建议：**方案 A（单向推送）**
- 理由：Dify 验证了这个模式可行，快速上线
- 后续：有需求再升级到方案 B

**决策2：还需要 Redis 队列吗？**
- 方案 A：❌ **不需要**（同步处理即可）
- 方案 B：⚠️ **可选**（如果 LangGraph 执行 >5秒，建议异步）
- 建议：**先不用**，性能瓶颈再加

**决策3：会话存储？**
- 方案 A：不需要（单次请求）
- 方案 B：复用 LangGraph PostgreSQL Checkpointing
- `thread_id` = 飞书的 `conversation_id`（从事件中提取）

### Step 2.2：方案 A 实现（单向推送，1-2小时）

#### 2.2.1 创建飞书客户端（30分钟）

创建文件：`src/harness/feishu_client.py`

**核心功能**：
```python
import httpx
import json

class FeishuClient:
    """飞书 API 客户端（群机器人 Webhook）"""
    
    def __init__(self, webhook_key: str):
        self.webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{webhook_key}"
    
    def send_card_message(
        self, 
        title: str, 
        content: str, 
        card_type: str = "info"
    ) -> dict:
        """发送卡片消息到飞书群
        
        Args:
            title: 卡片标题
            content: Markdown 格式内容
            card_type: info/success/warning/error
        """
        # 构造飞书卡片 JSON
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": self._get_template_color(card_type)
                },
                "elements": [
                    {"tag": "markdown", "content": content}
                ]
            }
        }
        
        response = httpx.post(self.webhook_url, json=card)
        return response.json()
    
    def _get_template_color(self, card_type: str) -> str:
        """卡片颜色映射"""
        colors = {
            "info": "blue",
            "success": "green", 
            "warning": "orange",
            "error": "red"
        }
        return colors.get(card_type, "blue")
```

**配置文件**：`.env`
```bash
FEISHU_WEBHOOK_KEY=557e5b9b-e431-486f-a26c-2b0509b73437
```

#### 2.2.2 创建 FastAPI 接口（30分钟）

创建文件：`src/harness/travel_approval_api.py`

**核心功能**：
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.modules.module_5_langgraph.graphs.react_graph import create_react_graph
from src.harness.feishu_client import FeishuClient
import os

app = FastAPI()

# 初始化
graph = create_react_graph()
feishu_client = FeishuClient(os.getenv("FEISHU_WEBHOOK_KEY"))

class TravelRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    purpose: str
    user_name: str = "员工"

@app.post("/api/travel/submit")
async def submit_travel_application(request: TravelRequest):
    """提交差旅申请并推送结果到飞书"""
    
    # 1. 构造查询
    query = f"我要去{request.destination}出差，时间{request.start_date}到{request.end_date}，目的是{request.purpose}"
    
    # 2. 调用 LangGraph
    result = graph.invoke({"query": query})
    
    # 3. 提取审批结果
    approval_message = result.get("response", "审批失败")
    
    # 4. 判断审批类型（决定卡片颜色）
    if "通过" in approval_message or "✅" in approval_message:
        card_type = "success"
    elif "拒绝" in approval_message or "❌" in approval_message:
        card_type = "error"
    elif "人工审批" in approval_message or "📋" in approval_message:
        card_type = "warning"
    else:
        card_type = "info"
    
    # 5. 推送到飞书群
    feishu_result = feishu_client.send_card_message(
        title=f"{request.user_name}的差旅申请",
        content=approval_message,
        card_type=card_type
    )
    
    return {
        "status": "success",
        "approval_result": approval_message,
        "feishu_sent": feishu_result.get("StatusCode") == 0
    }
```

#### 2.2.3 测试（30分钟）

**启动服务**：
```bash
# 终端 1：启动 FastAPI
uvicorn src.harness.travel_approval_api:app --reload --port 8000
```

**测试 API**：
```bash
curl -X POST 'http://localhost:8000/api/travel/submit' \
  -H 'Content-Type: application/json' \
  -d '{
    "destination": "上海",
    "start_date": "2026-06-20",
    "end_date": "2026-06-22",
    "purpose": "客户拜访",
    "user_name": "张三"
  }'
```

**验证**：
1. ✅ API 返回成功
2. ✅ 飞书群收到卡片消息
3. ✅ 卡片颜色正确（通过=绿色）

---

### Step 2.3：方案 B 实现（双向对话，3-4小时）- 可选

⚠️ **建议**：先完成方案 A 并上线，有需求再实现方案 B

#### 2.3.1 配置飞书事件订阅（30分钟）

**飞书开放平台配置**：
1. 进入应用 → 事件订阅
2. 请求地址 URL：
   ```
   https://你的公网地址/webhook/feishu/event
   ```
3. 获取 Verification Token 和 Encrypt Key
4. 订阅事件：
   - `im.message.receive_v1`（接收消息）

#### 2.3.2 实现 Webhook 接收（1小时）

创建文件：`src/harness/feishu_webhook.py`

**核心功能**：
```python
from fastapi import FastAPI, Request
import hashlib
import time

app = FastAPI()

@app.post("/webhook/feishu/event")
async def feishu_event_handler(request: Request):
    """接收飞书事件"""
    
    # 1. 验证签名（安全性）
    timestamp = request.headers.get("X-Lark-Request-Timestamp")
    nonce = request.headers.get("X-Lark-Request-Nonce")
    signature = request.headers.get("X-Lark-Signature")
    
    body = await request.body()
    if not verify_signature(timestamp, nonce, body, signature):
        return {"error": "Invalid signature"}
    
    # 2. 解析事件
    data = await request.json()
    
    # 3. URL 验证（首次配置）
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}
    
    # 4. 处理消息事件
    event = data.get("event", {})
    if event.get("type") == "im.message.receive_v1":
        return await handle_message(event)
    
    return {"code": 0}

async def handle_message(event: dict):
    """处理用户消息"""
    
    # 提取消息内容
    message = event.get("message", {})
    content = json.loads(message.get("content", "{}"))
    user_query = content.get("text", "").strip()
    
    # 提取会话 ID
    conversation_id = message.get("chat_id")
    
    # 调用 LangGraph（带会话管理）
    config = {"configurable": {"thread_id": conversation_id}}
    result = graph.invoke({"query": user_query}, config)
    
    # 回复用户（调用飞书 Send Message API）
    await send_feishu_reply(
        open_id=event["sender"]["sender_id"]["open_id"],
        message=result["response"]
    )
    
    return {"code": 0}
```

#### 2.3.3 实现消息发送（30分钟）

```python
async def send_feishu_reply(open_id: str, message: str):
    """调用飞书 Send Message API"""
    
    # 1. 获取 access_token
    token = await get_app_access_token()
    
    # 2. 发送消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"receive_id_type": "open_id"}
    payload = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": message})
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, params=params, json=payload)
        return response.json()
```

---

---

## 今日产出（更新）

### Phase 1 已完成 ✅

**配置文件**：
- 飞书应用配置：App ID, App Secret, Webhook Key
- VS Code 端口转发：公网 URL 已获取
- Dify lark_notify 插件配置

**测试验证**：
- ✅ Dify Chatflow → Workflow 端到端流程
- ✅ lark_notify 推送到飞书群成功
- ✅ 飞书群收到格式化卡片消息

**学习笔记**：
- 技术讲解已记录在本文档
- Webhook 原理和使用
- 端口转发工具对比
- Dify 插件系统理解

### Phase 2 ✅ 已完成（2026-06-23 21:50）

**代码文件（方案 A）**：
- ✅ `src/harness/feishu_client.py` - 飞书 Webhook 客户端（131行，100%覆盖率）
- ✅ `src/harness/travel_approval_api.py` - FastAPI 接口（158行，91%覆盖率）
- ✅ `.env` 配置文件更新 - 添加 FEISHU_WEBHOOK_KEY

**测试代码**：
- ✅ `tests/test_feishu_client.py` - 客户端单元测试（9个测试，100%通过）
- ✅ `tests/test_travel_api.py` - API 集成测试（9个测试，100%通过）
- ✅ **整体测试覆盖率：94%**（目标80%，超过14%）

**辅助工具**：
- ✅ `test_travel_e2e.py` - 端到端测试脚本
- ✅ `start_api.py` - 快速启动脚本
- ✅ `test_result.json` - 真实测试结果记录

**端到端验证**：
- ✅ API 服务启动成功
- ✅ LangGraph 调用成功（1次迭代）
- ✅ 飞书消息推送成功（HTTP 200, feishu_sent: true）
- ✅ 飞书群收到卡片消息

**Bug 修复记录**：
- 问题：`graph.invoke()` 缺少初始状态导致 `'iteration'` KeyError
- 解决：使用 `create_initial_state()` 创建完整初始状态
- 修改文件：`src/harness/travel_approval_api.py` 第103-105行

---

## 时间节点检查（最终）

- [x] ~~11:00~~ **已完成** - Phase 1完成，Dify + 飞书跑通
- [x] **21:50** - 方案 A 代码完成（FastAPI + LangGraph + Webhook）✅
- [x] **21:50** - 方案 A 测试通过（94%覆盖率）✅
- [x] **21:50** - 端到端验证通过（飞书消息发送成功）✅
- [x] **21:50** - 文档和总结完成 ✅
- [ ] 17:00+（可选）- 方案 B 实现（双向对话）- 未实现（按需）

---

## 实施建议

### 立即开始：方案 A（单向推送）

**优先级：高**
- ✅ 经过 Dify 验证可行
- ✅ 实现简单（1-2小时）
- ✅ 无需复杂配置
- ✅ 快速上线

**实施步骤**：
1. 创建 `feishu_client.py`（30分钟）
2. 创建 `travel_approval_api.py`（30分钟）
3. 测试端到端（30分钟）

### 后续扩展：方案 B（双向对话）

**优先级：中（按需）**
- ⚠️ 配置复杂（飞书事件订阅）
- ⚠️ 需要签名验证
- ⏱️ 3-4小时实现

**何时实现**：
- 用户明确需要在飞书中发起对话
- 需要多轮会话上下文
- 有充足时间测试

---

## 降级方案

如果某个环节卡住：

**卡点1：Redis安装失败**
- 降级：用Python的`queue.Queue`（内存队列，重启丢失）

**卡点2：飞书配置复杂**
- 降级：先用本地POST测试Webhook

**卡点3：多轮对话复杂**
- 降级：先实现单轮，多轮留到明天

---

## 下一步（明天）

- [ ] 添加图片处理（多模态）
- [ ] 添加监控指标
- [ ] 扩展到微信（复用架构）
- [ ] 压力测试

---

# 📚 面试复习专区

## 一、Dify vs LangChain 对比总结

### 核心区别

| 维度 | Dify | LangChain |
|------|------|-----------|
| **定位** | 低代码 AI 应用平台 | Python AI 开发框架 |
| **集成方式** | 插件市场（lark_notify） | 自定义代码实现 |
| **开发难度** | ⭐ 配置即用 | ⭐⭐⭐ 需要编码 |
| **灵活性** | ⚠️ 受限于插件功能 | ✅ 完全自主控制 |
| **部署方式** | 需要 Dify 服务 | 独立部署 FastAPI |
| **双向对话** | ❌ 不支持（飞书 Webhook） | ✅ 支持（事件订阅） |
| **适用场景** | 快速验证、MVP | 生产级、定制化需求 |

### 技术架构对比

**Dify 方案**：
```
Dify Chatflow → Workflow API → lark_notify 插件 → 飞书 Webhook
```

**LangChain 方案**：
```
FastAPI 接口 → LangGraph Agent → FeishuClient → 飞书 Webhook
```

---

## 二、LangChain 接入微信实现（类比飞书）

### 微信公众号 vs 飞书 Webhook 对比

| 特性 | 飞书 Webhook | 微信公众号 |
|------|-------------|-----------|
| **通信方向** | 单向推送 | 双向通信 |
| **认证方式** | Webhook Key | Token + SHA1 签名 |
| **消息格式** | JSON | XML |
| **会话管理** | 不需要 | 需要（OpenID） |
| **超时限制** | 10秒 | 5秒 |
| **使用场景** | 通知推送 | 对话交互 |

### 微信公众号接入完整流程

#### 架构设计
```
微信用户发消息
    ↓
微信服务器 → FastAPI Webhook (/wechat/callback)
    ↓
验证签名（SHA1(token + timestamp + nonce)）
    ↓
解析 XML 消息（from_user, content）
    ↓
LangGraph 处理（thread_id = from_user）
    ↓
构造回复 XML
    ↓
返回给微信服务器（5秒内）
    ↓
用户收到消息
```

#### 核心代码结构

**1. 微信客户端**
```python
class WeChatClient:
    def verify_signature(self, signature, timestamp, nonce) -> bool:
        """验证微信签名"""
        tmp_list = sorted([self.token, timestamp, nonce])
        tmp_str = ''.join(tmp_list)
        hash_str = hashlib.sha1(tmp_str.encode()).hexdigest()
        return hash_str == signature
    
    def parse_xml_message(self, xml_data: str) -> dict:
        """解析微信 XML 消息 → {from_user, content, msg_type}"""
    
    def build_text_response(self, to_user, from_user, content) -> str:
        """构造 XML 格式回复"""
```

**2. FastAPI Webhook 端点**
```python
@app.get("/wechat/callback")  # 微信服务器验证
async def wechat_verify(signature, timestamp, nonce, echostr):
    if wechat_client.verify_signature(signature, timestamp, nonce):
        return echostr
    raise HTTPException(400)

@app.post("/wechat/callback")  # 接收消息
async def wechat_message(request: Request):
    xml_data = await request.body()
    msg = wechat_client.parse_xml_message(xml_data)
    
    # 调用 LangGraph（带会话管理）
    config = {"configurable": {"thread_id": msg["from_user"]}}
    result = graph.invoke({"query": msg["content"]}, config)
    
    # 5秒内返回 XML 回复
    return Response(
        content=wechat_client.build_text_response(...),
        media_type="application/xml"
    )
```

**3. LangGraph 会话管理**
```python
from langgraph.checkpoint.postgres import PostgresSaver

# 配置 Checkpointing（持久化会话）
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
graph = create_react_graph().compile(checkpointer=checkpointer)

# 调用时传入 thread_id
config = {"configurable": {"thread_id": user_openid}}
result = graph.invoke(state, config)
```

### 关键技术点

**1. 签名验证**
- 目的：防止伪造请求
- 算法：SHA1([token, timestamp, nonce].sorted())
- 时机：每次接收消息前

**2. 会话管理**
- thread_id：使用微信用户 OpenID
- 存储：PostgreSQL Checkpointing
- 过期：设置 TTL（如 24 小时）

**3. 超时处理**
- 微信要求：5 秒内响应
- 方案 1：同步处理（简单场景）
- 方案 2：异步处理 + "处理中"回复（复杂场景）

**4. 消息格式**
- 接收：XML（`<ToUserName>`, `<Content>`）
- 回复：XML（`<ToUserName>`, `<Content>`, `<CreateTime>`）

---

## 三、关键技术面试问题

### Q1: Dify 和 LangChain 接入第三方平台的主要区别是什么？

**答案要点**：
- **开发方式**：Dify 是配置式（插件），LangChain 是编码式（自定义）
- **灵活性**：Dify 受限于插件功能，LangChain 完全自主控制
- **部署**：Dify 需要平台服务，LangChain 独立部署
- **适用场景**：Dify 适合快速验证，LangChain 适合生产级应用

### Q2: 如何用 LangChain 实现微信公众号对话？

**答案要点**：
1. **配置微信后台**：服务器 URL、Token
2. **实现签名验证**：SHA1(token + timestamp + nonce)
3. **解析 XML 消息**：提取用户 ID 和消息内容
4. **LangGraph 处理**：使用 Checkpointing 管理会话（thread_id = OpenID）
5. **构造 XML 回复**：5 秒内返回
6. **关键点**：会话持久化、超时处理、消息去重

### Q3: Webhook 单向推送和双向对话有什么区别？

**答案要点**：

**单向推送**（飞书 Webhook）：
- 服务器主动推送消息到飞书群
- 不接收用户回复
- 无需会话管理
- 简单快速

**双向对话**（微信公众号）：
- 接收用户消息 + 回复消息
- 需要会话管理（多轮对话）
- 需要签名验证
- 需要处理超时

### Q4: LangGraph 的会话管理如何实现？

**答案要点**：

**方法 1：Checkpointing（推荐）**
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
graph = workflow.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": user_id}}
result = graph.invoke(state, config)
```

**方法 2：手动 Memory**
```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory()
```

**对比**：
- Checkpointing：自动持久化、支持中断恢复、生产推荐
- Memory：简单灵活、不持久化、适合原型

### Q5: 你们这次实现遇到了什么问题？如何解决的？

**真实案例**：

**问题**：FastAPI 调用 LangGraph 报错 `KeyError: 'iteration'`

**原因**：
```python
# ❌ 错误（只传了 query）
result = graph.invoke({"query": query})
```

**解决**：
```python
# ✅ 正确（使用完整初始状态）
from src.modules.module_5_langgraph.state import create_initial_state
initial_state = create_initial_state(query, max_iterations=3)
result = graph.invoke(initial_state)
```

**经验**：
- LangGraph 状态必须完整初始化
- 使用 `create_initial_state()` 而非手动构造
- 先跑 mock 测试，再跑真实集成

### Q6: 如何设计生产级的 LangChain 应用？

**答案要点**：

**架构分层**：
```
接入层：FastAPI / Webhook
    ↓
业务层：LangGraph Agent
    ↓
基础层：LLM / RAG / Tools
    ↓
存储层：PostgreSQL / Redis / VectorDB
```

**关键组件**：
1. **API Gateway**：限流、认证
2. **消息队列**：异步处理（超过 5 秒）
3. **会话存储**：Checkpointing
4. **向量数据库**：RAG 检索
5. **监控告警**：LangSmith / Prometheus

**性能优化**：
- LLM 并发控制
- 向量检索缓存
- 结果缓存（Redis）

**安全考虑**：
- 签名验证
- 敏感信息脱敏
- 频率限制

### Q7: 你们的测试覆盖率是多少？如何保证代码质量？

**答案要点**：

**测试策略**：
- **单元测试**：独立函数/类，Mock 外部依赖
- **集成测试**：模块间交互，Mock LLM
- **端到端测试**：真实环境，实际 LLM 调用

**我们的实践**：
- 测试覆盖率：94%（目标 80%）
- 测试框架：pytest
- Mock 工具：unittest.mock
- 测试模式：AAA（Arrange-Act-Assert）

**质量保证**：
- 所有 PR 必须通过测试
- 代码审查（code review）
- 类型检查（Pydantic）

### Q8: 本次实现的技术栈和成果？

**技术栈**：
- FastAPI：Web 框架
- LangGraph：Agent 编排
- httpx：HTTP 客户端
- Pydantic：数据验证
- pytest：测试框架

**完成内容**：
1. ✅ 飞书客户端（131行，100%覆盖）
2. ✅ FastAPI 接口（158行，91%覆盖）
3. ✅ 完整测试（18个测试，94%覆盖）
4. ✅ 端到端验证（真实飞书消息发送成功）

**架构特点**：
- 单向推送（无会话管理）
- 独立部署（不依赖 Dify）
- 完全自主控制
- 高测试覆盖率

---

## 四、快速复习清单

### 核心概念
- [ ] Webhook 原理（推送 vs 轮询）
- [ ] 单向推送 vs 双向对话
- [ ] LangGraph Checkpointing
- [ ] thread_id 设计

### 技术实现
- [ ] 飞书 Webhook（JSON, POST）
- [ ] 微信签名验证（SHA1）
- [ ] XML 消息解析和构造
- [ ] FastAPI Webhook 端点

### 对比分析
- [ ] Dify vs LangChain
- [ ] 飞书 vs 微信
- [ ] Checkpointing vs Memory

### 架构设计
- [ ] 生产级架构分层
- [ ] 异常处理和降级
- [ ] 测试策略（94%覆盖率）
- [ ] 性能优化

---

## 五、快速启动命令

### 启动 API
```bash
python start_api.py
```

### 运行测试
```bash
# 单元测试 + 覆盖率
pytest tests/test_feishu_client.py tests/test_travel_api.py --cov=src.harness -v

# 端到端测试
python test_travel_e2e.py
```

### 发送测试请求
```bash
curl -X POST 'http://localhost:8000/api/travel/submit' \
  -H 'Content-Type: application/json' \
  -d '{
    "destination": "上海",
    "start_date": "2026-06-25",
    "end_date": "2026-06-27",
    "purpose": "客户拜访",
    "user_name": "张三"
  }'
```

---

**面试准备建议**：重点掌握 Q1-Q8，结合代码理解技术细节，能够清晰描述实现流程和解决问题的思路。

**文档更新时间**：2026-06-23 21:50  
**会话成本记录**：$81.34
