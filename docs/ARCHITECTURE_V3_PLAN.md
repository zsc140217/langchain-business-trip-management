# 统一 RAG-Agent 架构规划文档 v3

文档版本: v3.0
创建日期: 2026-07-13
状态: 规划中
基于: v2 架构完成后的优化方向

---

## 一、v2 完成状态回顾

### 已完成的核心能力

**架构层**：
- ✅ 统一入口 OrchestratorAgent（规则匹配 + LLM 路由）
- ✅ Q&A 域四通道（simple/complex/planning/open）
- ✅ 审批域（自动/人工审批 + 飞书通知）
- ✅ MCP 工具架构（6个工具）

**记忆层**：
- ✅ 对话历史（ChatMemory）
- ✅ 用户画像（LongTermMemory）
- ✅ 工作记忆（WorkingMemory）
- ✅ 记忆增强 Prompt（build_enhanced_prompt）

**监控层**：
- ✅ Prometheus 基础指标
- ✅ AlertManager 告警规则
- ✅ LangSmith 链路追踪
- ✅ 飞书告警通道

**工具生态**：
- ✅ search_policy（政策检索）
- ✅ query_graph（图谱查询）
- ✅ search_weather/hotel/flight（差旅工具）
- ✅ submit_reimbursement（提交报销）
- ✅ check_approval_status（查询审批状态）

### v2 的遗留问题

**架构层**：
1. 模块间点对点 HTTP 调用，缺少统一通信层
2. 无全局 TraceID 传递，调用链路追踪不完整
3. OrchestratorAgent 单点调度，无负载均衡

**工具层**：
1. 工具硬编码接入，新增工具需修改代码
2. 无工具注册中心、无权限控制
3. 无工具熔断和健康检查机制

**业务层**：
1. 审批流程止于飞书通知，缺少 PDF 表单生成
2. 无多模态能力（发票识别、OCR）
3. 飞书只能单向推送，无法接收用户回调

**评估层**：
1. 静态测试集 Eval，无 Bad Case 回流
2. 无人工反馈闭环
3. 无 A/B 测试能力

---

## 二、v3 设计哲学

### 核心原则

1. **事件驱动优于点对点调用** — 模块间通过事件总线异步通信
2. **注册发现优于硬编码** — 工具通过 YAML 配置自动注册
3. **安全护栏优于事后补救** — 输入输出都要做护栏检查
4. **自动评估优于人工验证** — LLM-as-Judge + 反馈闭环
5. **多模态优于纯文本** — 支持图片、语音、文档输入
6. **双向交互优于单向推送** — 飞书 Webhook 接收用户操作

### 不做什么（避免过度设计）

1. ❌ **不引入微服务架构** — 保持单体应用，事件总线解耦即可
2. ❌ **不做分布式训练** — 使用云端 API，不自建模型训练
3. ❌ **不做 K8s 编排** — 先本地优化，生产部署另行规划
4. ❌ **不做语音输入** — 优先级低，放到 v4

---

## 三、v3 总体架构图

```text
用户/飞书消息（文本 + 图片 + 文档）
     │
     ▼
┌───────────────────────────────────────────────┐
│  飞书网关 (FeishuGateway)                       │
│  ├─ Webhook 接收（用户消息、卡片按钮回调）       │
│  ├─ 签名验证（HMAC-SHA256）                     │
│  ├─ 事件分发（消息 → 对话、按钮 → 审批）         │
│  └─ 卡片推送（审批、通知）                       │
└───────────────────────────────────────────────┘
     │
     ▼
┌───────────────────────────────────────────────┐
│  输入护栏 (InputGuardrail)                      │
│  ├─ Prompt Injection 检测                       │
│  ├─ 恶意指令过滤                                 │
│  ├─ 敏感信息检测                                 │
│  └─ 输入长度限制                                 │
└───────────────────────────────────────────────┘
     │
     ▼
┌───────────────────────────────────────────────┐
│  多模态处理 (MultimodalProcessor)               │
│  ├─ 文本 → 直接传递                             │
│  ├─ 图片 → OCR + Vision LLM                     │
│  ├─ 文档 → PDF 解析 + 信息抽取                   │
│  └─ 统一输出为文本 + 结构化数据                   │
└───────────────────────────────────────────────┘
     │
     ▼
┌───────────────────────────────────────────────┐
│  记忆层 (MemoryService) - v2已有               │
│  build_enhanced_prompt()                       │
│  ├─ 对话历史 (ChatMemory)                       │
│  ├─ 用户画像 (LongTermMemory)                   │
│  ├─ 工作记忆 (WorkingMemory)                    │
│  └─ 审批状态 (审批中的单据)                      │
└───────────────────────────────────────────────┘
     │
     ▼
┌───────────────────────────────────────────────┐
│  入口 Agent (OrchestratorAgent) - v2已有       │
│  ├─ 规则匹配 → 快路径                            │
│  ├─ LLM 路由 → Q&A 域 / 审批域                   │
│  └─ 全局 TraceID 管理 (v3新增)                   │
└───────────────────────────────────────────────┘
     |                 |
     ▼                 ▼
┌──────────┐    ┌─────────────────────┐
│ Q&A 域    │    │ 审批域（增强）       │
│ v2已有    │    │                     │
│           │    │ ├─ 表单生成 (v3新增) │
│ 四通道执行 │    │ │  → LLM 提取信息   │
│           │    │ │  → 自动校验        │
│           │    │ │                    │
│           │    │ ├─ PDF 渲染 (v3新增) │
│           │    │ │  → 报销表单模板    │
│           │    │ │  → 填充数据生成PDF │
│           │    │ │                    │
│           │    │ ├─ 审批推送 (v2已有) │
│           │    │ │  → 飞书交互式卡片  │
│           │    │ │  → 同意/拒绝按钮   │
│           │    │ │                    │
│           │    │ ├─ 审批回调 (v3新增) │
│           │    │ │  → Webhook 接收   │
│           │    │ │  → 状态更新        │
│           │    │ │  → 通知申请人      │
│           │    │ │                    │
│           │    │ └─ 审批流程引擎      │
│           │    │    → 金额阈值配置    │
│           │    │    → 超时自动升级    │
│           │    │    → 多级审批链      │
└───────────┘    └─────────────────────┘
     |                 |
     ▼                 ▼
┌───────────────────────────────────────────────┐
│  事件总线 (EventBus - Redis Stream) v3新增     │
│                                                 │
│  事件类型:                                      │
│  ├─ tool.called (工具调用事件)                  │
│  ├─ approval.created (审批创建事件)             │
│  ├─ approval.updated (审批状态变更事件)         │
│  ├─ memory.updated (记忆更新事件)               │
│  └─ error.occurred (错误事件)                   │
│                                                 │
│  消费者:                                        │
│  ├─ MonitoringConsumer → 监控指标收集           │
│  ├─ LoggingConsumer → 日志记录                  │
│  ├─ EvaluationConsumer → 自动评估               │
│  └─ NotificationConsumer → 飞书通知             │
└───────────────────────────────────────────────┘
     |
     ▼
┌───────────────────────────────────────────────┐
│  工具注册中心 (ToolRegistry) v3新增             │
│                                                 │
│  注册方式:                                      │
│  ├─ 编写 handler 函数                           │
│  ├─ 编写 YAML 配置                              │
│  ├─ 启动时自动扫描加载                           │
│  └─ LLM 自动发现可用工具                         │
│                                                 │
│  治理能力:                                      │
│  ├─ 权限控制 (RBAC)                             │
│  ├─ 熔断降级 (CircuitBreaker)                   │
│  ├─ 健康检查 (HealthCheck)                      │
│  ├─ 超时控制 (Timeout)                          │
│  └─ 调用监控 (Metrics)                          │
└───────────────────────────────────────────────┘
     |
     ▼
┌───────────────────────────────────────────────┐
│  输出护栏 (OutputGuardrail) v3新增              │
│  ├─ 敏感信息脱敏（电话/身份证）                   │
│  ├─ 违规内容过滤                                 │
│  ├─ 输出格式校验                                 │
│  └─ Token 长度限制                               │
└───────────────────────────────────────────────┘
     |
     ▼
┌───────────────────────────────────────────────┐
│  评估与反馈 (Evaluation) v3新增                 │
│                                                 │
│  自动评估:                                      │
│  ├─ LLM-as-Judge（GPT-4 评估回答质量）           │
│  ├─ 评估维度（准确性、完整性、有用性）            │
│  └─ 自动生成评分报告                             │
│                                                 │
│  人工反馈:                                      │
│  ├─ 用户点赞/点踩                                │
│  ├─ Bad Case 收集                               │
│  ├─ 定期分析优化                                 │
│  └─ 反馈闭环（优化 Prompt/工具）                 │
└───────────────────────────────────────────────┘
     |
     ▼
  最终回答 / 审批结果 / 监控告警
```

---

## 四、v3 核心模块详解

### 4.1 飞书网关（FeishuGateway）

**v2 问题**：只能单向推送消息，无法接收用户回调

**v3 解决方案**：
- Webhook 接收用户消息和卡片按钮回调
- 签名验证防止伪造请求
- 事件分发到不同处理器

**新增文件**：`src/harness/feishu/gateway.py`

```python
class FeishuGateway:
    """
    飞书网关 - 双向交互能力
    
    功能：
    1. Webhook 接收（用户消息、卡片按钮回调）
    2. 签名验证（HMAC-SHA256 + timestamp + nonce）
    3. 事件分发（消息 → 对话、按钮 → 审批）
    4. 交互式卡片推送（审批、通知）
    """
    
    def __init__(self, app_id: str, app_secret: str, 
                 verify_token: str, encrypt_key: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.verify_token = verify_token
        self.encrypt_key = encrypt_key
        self.event_handlers = {}
        self.redis_client = redis.Redis()  # nonce 去重
    
    def verify_signature(self, timestamp: str, nonce: str, 
                        body: str, signature: str) -> bool:
        """
        验证飞书签名
        
        防护措施：
        1. HMAC-SHA256 签名校验
        2. timestamp 防重放（5分钟内有效）
        3. nonce 去重（Redis 存储已处理的 nonce）
        """
        # 检查 timestamp（当前时间 ± 5分钟）
        current_time = int(time.time())
        request_time = int(timestamp)
        if abs(current_time - request_time) > 300:
            return False
        
        # 检查 nonce 是否已处理
        nonce_key = f"feishu:nonce:{nonce}"
        if self.redis_client.exists(nonce_key):
            return False
        
        # 验证签名
        sign_base = f"{timestamp}{nonce}{self.encrypt_key}{body}"
        expected_signature = hmac.new(
            self.encrypt_key.encode(),
            sign_base.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            return False
        
        # 存储 nonce（10分钟过期）
        self.redis_client.setex(nonce_key, 600, "1")
        return True
    
    def handle_webhook(self, request: dict) -> dict:
        """
        处理 Webhook 请求
        
        支持的事件类型：
        1. im.message.receive_v1 → 用户消息
        2. card.action.trigger → 卡片按钮点击
        """
        event_type = request["header"]["event_type"]
        
        if event_type == "im.message.receive_v1":
            return self._handle_message(request["event"])
        elif event_type == "card.action.trigger":
            return self._handle_card_action(request["event"])
        else:
            return {"code": 0}
    
    def _handle_message(self, event: dict) -> dict:
        """处理用户消息"""
        message = event["message"]
        sender = event["sender"]
        
        # 发布到事件总线
        event_bus.publish(Event(
            type="feishu.message.received",
            payload={
                "user_id": sender["user_id"],
                "message_type": message["message_type"],
                "content": message["content"],
            }
        ))
        
        return {"code": 0}
    
    def _handle_card_action(self, event: dict) -> dict:
        """处理卡片按钮点击"""
        action = event["action"]
        
        # 发布到事件总线
        event_bus.publish(Event(
            type="feishu.card.action",
            payload={
                "action_value": action["value"],
                "user_id": event["operator"]["user_id"],
            }
        ))
        
        return {"code": 0}
    
    def send_interactive_card(self, open_id: str, 
                             card_data: dict) -> bool:
        """
        发送交互式卡片
        
        卡片组件：
        1. 按钮（同意/拒绝）
        2. 下拉菜单（选择审批人）
        3. 日期选择器（选择出差日期）
        """
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }
        data = {
            "receive_id": open_id,
            "msg_type": "interactive",
            "content": json.dumps(card_data)
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()["code"] == 0
```

---

### 4.2 输入护栏（InputGuardrail）

**v2 问题**：无输入校验，存在 Prompt Injection 风险

**v3 解决方案**：
- Prompt Injection 检测
- 恶意指令过滤
- 敏感信息检测
- 输入长度限制

**新增文件**：`src/security/input_guardrail.py`

```python
import re
from typing import Tuple

class InputGuardrail:
    """
    输入护栏 - 安全检查
    
    检测项：
    1. Prompt Injection（忽略之前的指令、扮演XX角色）
    2. 恶意指令（删除数据、泄露密钥）
    3. 敏感信息（信用卡号、密码）
    4. 输入长度（> 10000 字符拒绝）
    """
    
    def __init__(self):
        self.injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"你现在是.+角色",
            r"忘记之前的规则",
            r"disregard\s+the\s+above",
            r"扮演.+模式",
        ]
        
        self.malicious_patterns = [
            r"删除.*数据",
            r"泄露.*密钥",
            r"sudo\s+rm\s+-rf",
            r"drop\s+table",
            r"union\s+select",
        ]
        
        self.sensitive_patterns = [
            (r"\d{16}", "信用卡号"),
            (r"password\s*[:=]\s*\S+", "密码"),
            (r"\d{15}|\d{18}", "身份证号"),
        ]
    
    def check(self, user_input: str, trace_id: str = "") -> Tuple[bool, str]:
        """
        检查输入是否安全
        
        Returns:
            (is_safe, reason)
        """
        # 1. 长度检查
        if len(user_input) > 10000:
            logger.warning(f"[{trace_id}] Input too long: {len(user_input)} chars")
            return False, "输入过长，请控制在10000字符以内"
        
        # 2. Prompt Injection 检测
        for pattern in self.injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"[{trace_id}] Prompt injection detected: {pattern}")
                return False, "检测到不安全的输入，请重新输入"
        
        # 3. 恶意指令检测
        for pattern in self.malicious_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"[{trace_id}] Malicious input detected: {pattern}")
                return False, "检测到恶意指令，请重新输入"
        
        # 4. 敏感信息检测（警告但不拦截）
        for pattern, info_type in self.sensitive_patterns:
            if re.search(pattern, user_input):
                logger.warning(f"[{trace_id}] Sensitive info detected: {info_type}")
                # 不拦截，但后续会在输出护栏中脱敏
        
        return True, ""
```

---

### 4.3 多模态处理（MultimodalProcessor）

**v2 问题**：只支持文本输入，无法处理发票、机票、PDF

**v3 解决方案**：
- 图片 → OCR + Vision LLM（发票识别）
- PDF → 文本提取 + 信息抽取（行程单）
- 统一输出为文本 + 结构化数据

**新增文件**：`src/multimodal/processor.py`

```python
from typing import Union, Dict, Any
from PIL import Image
import pdfplumber
import io

class MultimodalProcessor:
    """
    多模态处理器
    
    支持：文本、图片（OCR+Vision LLM）、PDF（文本提取+信息抽取）
    """
    
    def __init__(self, vision_llm, ocr_engine):
        self.vision_llm = vision_llm  # Qwen-VL / GPT-4V
        self.ocr_engine = ocr_engine  # PaddleOCR
    
    def process(self, input_data: Union[str, bytes], 
                input_type: str) -> Dict[str, Any]:
        """统一处理入口"""
        if input_type == 'text':
            return {'text': input_data, 'structured_data': None}
        elif input_type == 'image':
            return self._process_image(input_data)
        elif input_type == 'pdf':
            return self._process_pdf(input_data)
    
    def _process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """处理图片 - OCR + Vision LLM"""
        ocr_text = self.ocr_engine.extract(image_bytes)
        vision_result = self.vision_llm.analyze(
            image_bytes,
            prompt="识别文档类型。如果是发票，提取金额、日期、商家。"
        )
        
        structured_data = None
        if "发票" in vision_result:
            structured_data = self._extract_invoice_info(ocr_text)
        
        return {
            'text': f"[图片内容] {vision_result}\nOCR: {ocr_text}",
            'structured_data': structured_data,
            'metadata': {'type': 'image'}
        }
    
    def _extract_invoice_info(self, ocr_text: str) -> Dict:
        """提取发票信息"""
        # 使用 LLM Function Calling 提取结构化信息
        return {
            'type': 'invoice',
            'amount': 1234.56,  # 从 OCR 文本提取
            'date': '2026-07-13',
            'merchant': '北京XX酒店'
        }
    
    def _process_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """处理 PDF - 文本提取"""
        text_content = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text_content.append(page.extract_text())
        
        full_text = "\n".join(text_content)
        return {
            'text': f"[PDF内容]\n{full_text[:1000]}...",
            'structured_data': None,
            'metadata': {'type': 'pdf', 'pages': len(text_content)}
        }
```

---

### 4.4 事件总线（EventBus）

**v2 问题**：模块间点对点 HTTP 调用，缺少统一通信层

**v3 解决方案**：
- 引入 Redis Stream 作为事件总线
- 模块异步通信，解耦依赖
- 支持重试和死信队列

**新增文件**：`src/core/events/bus.py`

```python
import redis
from dataclasses import dataclass
import json
import time

@dataclass
class Event:
    """事件基类"""
    type: str           # 事件类型（tool.called / approval.created）
    trace_id: str       # 全局追踪ID
    payload: dict       # 事件数据
    timestamp: float = None
    event_id: str = None

class EventBus:
    """
    事件总线 - Redis Stream
    
    事件类型：
    - tool.called: 工具调用
    - approval.created: 审批创建
    - approval.updated: 审批更新
    - memory.updated: 记忆更新
    - error.occurred: 错误发生
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.stream_name = "agent:events"
        self.consumer_group = "agent-consumers"
        
        # 创建消费者组
        try:
            self.redis_client.xgroup_create(
                self.stream_name, self.consumer_group, 
                id='0', mkstream=True
            )
        except redis.exceptions.ResponseError:
            pass
    
    def publish(self, event: Event) -> str:
        """发布事件到 Stream"""
        if not event.timestamp:
            event.timestamp = time.time()
        
        event_data = {
            'type': event.type,
            'trace_id': event.trace_id,
            'timestamp': str(event.timestamp),
            'payload': json.dumps(event.payload)
        }
        
        message_id = self.redis_client.xadd(
            self.stream_name, event_data, maxlen=10000
        )
        return message_id
    
    def subscribe(self, event_type: str, handler):
        """订阅事件（支持通配符）"""
        pass  # 在消费者中实现
```

**新增消费者**：`src/core/events/consumers/monitoring_consumer.py`

```python
class MonitoringConsumer:
    """监控消费者 - 收集指标"""
    
    def __init__(self, event_bus):
        event_bus.subscribe('tool.called', self.on_tool_called)
        event_bus.subscribe('approval.*', self.on_approval_event)
    
    def on_tool_called(self, event):
        """工具调用事件 → Prometheus 指标"""
        payload = event.payload
        prometheus_client.increment(
            'tool_calls_total',
            labels={'tool': payload['tool_name'], 'success': payload['success']}
        )
    
    def on_approval_event(self, event):
        """审批事件 → Prometheus 指标"""
        prometheus_client.increment(
            'approval_events_total',
            labels={'type': event.type.split('.')[-1]}
        )
```

---

### 4.5 工具注册中心（ToolRegistry）

**v2 问题**：工具硬编码，新增需改代码

**v3 解决方案**：
- YAML 配置 + handler 函数自动注册
- 权限控制（RBAC）
- 熔断降级 + 健康检查

**新增文件**：`src/tools/registry/registry.py`

```python
import yaml
import glob
from typing import Dict, List, Callable
from dataclasses import dataclass

@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    parameters: dict
    required_roles: List[str]
    timeout: int
    handler: Callable

class ToolRegistry:
    """
    工具注册中心
    
    功能：
    1. 自动扫描加载工具
    2. 权限控制（RBAC）
    3. 熔断降级
    4. 健康检查
    """
    
    def __init__(self, config_dir: str = "src/tools/configs"):
        self.tools: Dict[str, ToolMetadata] = {}
        self._load_tools(config_dir)
    
    def _load_tools(self, config_dir: str):
        """扫描并加载所有工具"""
        for config_file in glob.glob(f"{config_dir}/*.yaml"):
            with open(config_file, encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 动态导入 handler
            handler = self._import_handler(config['handler'])
            
            metadata = ToolMetadata(
                name=config['name'],
                description=config['description'],
                parameters=config['parameters'],
                required_roles=config.get('required_roles', []),
                timeout=config.get('timeout', 30),
                handler=handler
            )
            
            self.tools[config['name']] = metadata
            print(f"✓ Tool registered: {config['name']}")
    
    def _import_handler(self, handler_path: str) -> Callable:
        """导入 handler 函数"""
        module_path, func_name = handler_path.split(':')
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    
    def get_available_tools(self, user_roles: List[str]) -> List[Dict]:
        """获取用户可用工具（OpenAI 格式）"""
        available = []
        for tool in self.tools.values():
            # 权限检查
            if tool.required_roles and not any(
                role in user_roles for role in tool.required_roles
            ):
                continue
            
            available.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return available
    
    def call_tool(self, tool_name: str, params: dict, 
                  user_roles: List[str], trace_id: str) -> dict:
        """调用工具（权限检查 + 超时控制）"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # 权限检查
        if tool.required_roles and not any(
            role in user_roles for role in tool.required_roles
        ):
            raise PermissionError(f"No permission: {tool_name}")
        
        # 调用 handler
        try:
            result = tool.handler(**params)
            success = True
        except Exception as e:
            result = {'error': str(e)}
            success = False
        
        # 发布事件
        event_bus.publish(Event(
            type='tool.called',
            trace_id=trace_id,
            payload={'tool_name': tool_name, 'success': success}
        ))
        
        return result
```

**工具配置示例**：`src/tools/configs/weather.yaml`

```yaml
name: "search_weather"
description: "查询指定城市的天气信息"
handler: "src.tools.handlers.weather:handle"

parameters:
  type: "object"
  properties:
    city:
      type: "string"
      description: "城市名称，如'北京'"
  required: ["city"]

required_roles: []  # 所有用户可用
timeout: 10
```

**Handler 示例**：`src/tools/handlers/weather.py`

```python
def handle(city: str, date: str = None) -> dict:
    """天气查询 handler"""
    # 调用 MCP 天气工具
    result = mcp_client.call_tool('weather', {'city': city, 'date': date})
    return {'weather': result['description'], 'temperature': result['temp']}

def health_check() -> bool:
    """健康检查"""
    try:
        import requests
        response = requests.get("https://api.weather.com/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

---

## 五、v3 任务清单

### P0 任务（核心必做，4-6周）

| 任务ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|--------|----------|--------|----------|------|
| **T1** | **飞书网关双向交互** | P0 | 5天 | 无 |
| T1.1 | Webhook 接收 + 签名验证 | P0 | 2天 | 无 |
| T1.2 | 交互式卡片构建器 | P0 | 2天 | T1.1 |
| T1.3 | 事件分发器 | P0 | 1天 | T1.1 |
| **T2** | **输入输出护栏** | P0 | 3天 | 无 |
| T2.1 | 输入护栏（Prompt Injection 检测） | P0 | 1.5天 | 无 |
| T2.2 | 输出护栏（敏感信息脱敏） | P0 | 1.5天 | 无 |
| **T3** | **多模态能力** | P0 | 7天 | 无 |
| T3.1 | OCR 引擎集成（PaddleOCR） | P0 | 2天 | 无 |
| T3.2 | Vision LLM 集成（Qwen-VL） | P0 | 2天 | 无 |
| T3.3 | 发票识别 + 结构化输出 | P0 | 2天 | T3.1, T3.2 |
| T3.4 | PDF 解析 + 信息抽取 | P0 | 1天 | 无 |
| **T4** | **事件总线** | P0 | 4天 | 无 |
| T4.1 | Redis Stream 事件总线 | P0 | 2天 | 无 |
| T4.2 | 监控消费者（指标收集） | P0 | 1天 | T4.1 |
| T4.3 | 日志消费者 | P0 | 1天 | T4.1 |
| **T5** | **工具注册中心** | P0 | 5天 | 无 |
| T5.1 | YAML 配置加载 + 动态注册 | P0 | 2天 | 无 |
| T5.2 | 权限控制（RBAC） | P0 | 1天 | T5.1 |
| T5.3 | 熔断器 + 健康检查 | P0 | 2天 | T5.1 |
| **T6** | **报销表单自动生成** | P0 | 6天 | 无 |
| T6.1 | LLM 表单信息提取 | P0 | 2天 | 无 |
| T6.2 | PDF 渲染（ReportLab） | P0 | 2天 | T6.1 |
| T6.3 | 审批流程引擎增强（阈值配置） | P0 | 1天 | 无 |
| T6.4 | 审批回调处理（飞书按钮） | P0 | 1天 | T1.2 |

**P0 总计**：30天（6周），按2人并行可在3周内完成核心功能。

---

### P1 任务（应该完成，2-3周）

| 任务ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|--------|----------|--------|----------|------|
| **T7** | **评估体系升级** | P1 | 5天 | T4 |
| T7.1 | LLM-as-Judge 自动评估 | P1 | 2天 | 无 |
| T7.2 | 用户反馈收集（点赞/点踩） | P1 | 1天 | 无 |
| T7.3 | Bad Case 分析工具 | P1 | 2天 | T7.2 |
| **T8** | **全局 TraceID 传递** | P1 | 2天 | 无 |
| T8.1 | TraceID 上下文管理 | P1 | 1天 | 无 |
| T8.2 | 日志/监控打标签 | P1 | 1天 | T8.1 |
| **T9** | **Token 消耗统计** | P1 | 3天 | T4 |
| T9.1 | LLM 调用拦截器（计算 Token） | P1 | 1.5天 | 无 |
| T9.2 | 按用户/模型/时间维度统计 | P1 | 1.5天 | T9.1 |

**P1 总计**：10天（2周）

---

### P2 任务（可延后，1-2周）

| 任务ID | 任务名称 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| T10 | 审计日志系统 | P2 | 3天 |
| T11 | Grafana 看板完善 | P2 | 2天 |
| T12 | 配置热更新 | P2 | 2天 |

---

## 六、实施计划

### Phase 1: 基础设施层（Week 1-2）

**目标**：建立 v3 核心基础设施

**任务**：
- Week 1: 事件总线 + 输入输出护栏 + 全局 TraceID
  - T4.1-T4.3: Redis Stream 事件总线（2天）
  - T2.1-T2.2: 输入输出护栏（3天）
  - T8.1-T8.2: 全局 TraceID（2天，并行）

- Week 2: 工具注册中心
  - T5.1-T5.3: 工具注册中心完整实现（5天）

**里程碑**：
- ✅ 事件总线可用，至少2个消费者运行
- ✅ 输入护栏拦截率 > 95%（测试集）
- ✅ 所有请求有 TraceID
- ✅ 至少3个工具迁移到新注册中心

---

### Phase 2: 业务能力层（Week 3-4）

**目标**：完成核心业务功能增强

**任务**：
- Week 3: 多模态能力
  - T3.1-T3.4: OCR + Vision LLM + 发票识别（7天）

- Week 4: 报销表单 + 飞书双向交互
  - T6.1-T6.4: 报销表单自动生成（6天，3天并行）
  - T1.1-T1.3: 飞书网关双向交互（5天，2天并行）

**里程碑**：
- ✅ 发票识别准确率 > 90%
- ✅ 报销表单 PDF 生成成功率 > 95%
- ✅ 飞书审批卡片点击回调成功率 100%

---

### Phase 3: 评估与优化（Week 5-6）

**目标**：提升质量和可观测性

**任务**：
- Week 5: 评估体系
  - T7.1-T7.3: LLM-as-Judge + 反馈收集（5天）

- Week 6: Token 统计 + 审计日志
  - T9.1-T9.2: Token 消耗统计（3天）
  - T10: 审计日志系统（3天）

**里程碑**：
- ✅ LLM-as-Judge 评估覆盖率 100%
- ✅ Token 消耗统计按用户维度可查询
- ✅ 审计日志保留 >= 1年

---

## 七、文件变更清单

### 新建文件

| 文件路径 | 说明 | Phase |
|----------|------|-------|
| `src/harness/feishu/gateway.py` | 飞书网关（Webhook + 签名） | Phase 2 |
| `src/harness/feishu/card_builder.py` | 交互式卡片构建器 | Phase 2 |
| `src/security/input_guardrail.py` | 输入护栏 | Phase 1 |
| `src/security/output_guardrail.py` | 输出护栏 | Phase 1 |
| `src/multimodal/processor.py` | 多模态处理器 | Phase 2 |
| `src/multimodal/ocr_engine.py` | OCR 引擎封装 | Phase 2 |
| `src/multimodal/vision_llm.py` | Vision LLM 封装 | Phase 2 |
| `src/core/events/bus.py` | 事件总线 | Phase 1 |
| `src/core/events/event.py` | 事件基类 | Phase 1 |
| `src/core/events/consumers/monitoring_consumer.py` | 监控消费者 | Phase 1 |
| `src/core/events/consumers/logging_consumer.py` | 日志消费者 | Phase 1 |
| `src/core/tracing/context.py` | TraceID 上下文 | Phase 1 |
| `src/tools/registry/registry.py` | 工具注册中心 | Phase 1 |
| `src/tools/registry/circuit_breaker.py` | 熔断器 | Phase 1 |
| `src/tools/configs/weather.yaml` | 天气工具配置 | Phase 1 |
| `src/tools/configs/hotel.yaml` | 酒店工具配置 | Phase 1 |
| `src/tools/handlers/weather.py` | 天气 handler | Phase 1 |
| `src/modules/reimbursement/form_generator.py` | 表单生成器 | Phase 2 |
| `src/modules/reimbursement/pdf_renderer.py` | PDF 渲染器 | Phase 2 |
| `src/modules/reimbursement/templates/reimbursement.html` | 报销表单模板 | Phase 2 |
| `src/evaluation/llm_judge.py` | LLM 评估器 | Phase 3 |
| `src/evaluation/feedback_collector.py` | 反馈收集器 | Phase 3 |
| `src/evaluation/badcase_analyzer.py` | Bad Case 分析 | Phase 3 |
| `src/monitoring/token_tracker.py` | Token 统计 | Phase 3 |
| `src/monitoring/audit_logger.py` | 审计日志 | Phase 3 |

### 修改文件

| 文件路径 | 改动说明 | Phase |
|----------|----------|-------|
| `src/agents/orchestrator_agent.py` | 集成 TraceID、事件总线、输入护栏 | Phase 1 |
| `src/agents/approval_engine.py` | 集成表单生成、PDF 渲染、回调处理 | Phase 2 |
| `src/api/unified_api.py` | 集成多模态处理、飞书 Webhook 端点 | Phase 2 |
| `src/memory/memory_service.py` | 发布记忆更新事件 | Phase 1 |
| `src/monitoring/prometheus_exporter.py` | 新增 Token 消耗指标 | Phase 3 |

---

## 八、风险评估与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **OCR 准确率不足** | 中 | 高 | 使用多模型融合（PaddleOCR + Tesseract），Vision LLM 二次校验 |
| **Vision LLM 成本过高** | 高 | 中 | 先 OCR 后 LLM，只在必要时调用；使用开源模型（Qwen-VL） |
| **事件总线消息堆积** | 低 | 中 | Redis Stream maxlen 限制 + 死信队列 + 监控告警 |
| **工具注册中心循环依赖** | 低 | 高 | 延迟初始化 + 依赖检测 |
| **飞书签名验证失败** | 中 | 高 | 详细错误日志 + timestamp 容差5分钟 + nonce 去重 |
| **PDF 渲染中文乱码** | 中 | 中 | 使用支持中文的字体（Noto Sans CJK）+ WeasyPrint |
| **多模态处理延迟高** | 高 | 中 | 异步处理 + 进度通知 + 超时提示 |

---

## 九、成功指标

| 指标 | v2 基线 | v3 目标 | 测量方式 |
|------|---------|---------|----------|
| **发票识别准确率** | 0% | 90%+ | 测试集100张发票 |
| **报销表单生成成功率** | 0% | 95%+ | 审批域 E2E 测试 |
| **飞书卡片回调成功率** | 0% | 100% | Webhook 接收日志 |
| **输入护栏拦截率** | 0% | 95%+ | 安全测试集 |
| **工具调用成功率** | 95% | 98%+ | Prometheus 指标 |
| **LLM-as-Judge 评估覆盖率** | 0% | 100% | 所有对话自动评估 |
| **Token 消耗可观测性** | 部分 | 100% | 按用户/模型维度统计 |
| **全链路 TraceID 覆盖率** | 0% | 100% | 所有请求有 trace_id |

---

## 十、关键决策记录

### 决策1: 为什么选择 Redis Stream 而非 RabbitMQ？

**背景**：需要引入事件总线解耦模块

**选项**：
- RabbitMQ（重量级消息队列）
- Redis Stream（轻量级）
- Kafka（过度设计）

**决策**：Redis Stream

**理由**：
1. 项目已使用 Redis（记忆、缓存），无需额外部署
2. 消息量不大（<1000 msg/s），Redis Stream 足够
3. 简单易用，学习成本低
4. 支持消费者组、ACK、重试

---

### 决策2: 为什么选择 Qwen-VL 而非 GPT-4V？

**背景**：需要 Vision LLM 做发票识别

**选项**：
- GPT-4V（闭源，API 调用）
- Qwen-VL（开源，可本地部署）
- InternVL（开源）

**决策**：Qwen-VL

**理由**：
1. 中文能力强，适合国内发票
2. 可本地部署，降低成本
3. 性能接近 GPT-4V（发票识别场景）
4. 社区活跃，文档完善

---

### 决策3: 为什么不引入微服务架构？

**背景**：大厂建议服务治理、分布式链路

**选项**：
- 拆分为微服务（Q&A 服务、审批服务、工具服务）
- 保持单体应用 + 事件总线解耦

**决策**：保持单体 + 事件总线

**理由**：
1. 当前规模不大（< 100 QPS），单体足够
2. 微服务增加运维复杂度（网络、部署、监控）
3. 事件总线已解耦模块，满足扩展需求
4. 未来流量增长可拆分（先优化后拆分）

---

## 十一、下一步（v4 展望）

v3 完成后，以下方向可在 v4 考虑：

1. **语音交互**：ASR + TTS，支持语音问答
2. **Agent 协作**：多 Agent 并行处理复杂任务
3. **知识库自动更新**：爬取最新政策文档
4. **A/B 测试平台**：自动化对比不同策略
5. **多租户支持**：支持多个企业独立使用
6. **移动端 App**：React Native / Flutter

---

## 十二、参考资料

**技术文档**：
- [飞书开放平台文档](https://open.feishu.cn/document/)
- [Redis Stream 官方文档](https://redis.io/docs/data-types/streams/)
- [PaddleOCR 文档](https://github.com/PaddlePaddle/PaddleOCR)
- [Qwen-VL 文档](https://github.com/QwenLM/Qwen-VL)

**最佳实践**：
- [LangChain Agent 最佳实践](https://python.langchain.com/docs/modules/agents/)
- [Prompt Injection 防护指南](https://learnprompting.org/docs/prompt_hacking/defensive_measures)

---

文档版本: v3.0
最后更新: 2026-07-13
作者: Claude (基于项目答疑文档整理)

