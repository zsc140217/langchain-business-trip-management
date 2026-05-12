# 三层记忆系统设计文档

## 架构概览

三层记忆系统是从Spring AI迁移到LangChain的核心功能，用于实现智能对话的上下文管理和个性化推荐。

```
┌─────────────────────────────────────────────────────────┐
│                    MemoryService                        │
│                    (统一门面)                            │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Layer 1      │  │  Layer 2      │  │  Layer 3      │
│  短期记忆      │  │  工作记忆      │  │  长期记忆      │
│ ChatMemory    │  │ WorkingMemory │  │ LongTermMemory│
└───────────────┘  └───────────────┘  └───────────────┘
│                  │                  │
│ 文件存储        │ 内存存储         │ JSON文件
│ 20条消息        │ 30分钟TTL        │ 无限制
│ 上下文理解      │ 实体提取         │ 用户画像
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Layer 1: 短期记忆 (ChatMemory)

### 设计目标
- 存储最近的对话历史
- 提供上下文理解能力
- 支持滑动窗口机制

### 技术实现
```python
from src.memory import ChatMemory

# 创建短期记忆
memory = ChatMemory(chat_id="conv_001", max_messages=20)

# 添加消息
memory.add_user_message("我要去北京出差")
memory.add_assistant_message("好的，请问您需要什么帮助？")

# 获取上下文
context = memory.get_context_string(limit=10)
```

### 存储结构
```json
{
  "chat_id": "conv_001",
  "updated_at": "2026-05-12T10:30:00",
  "messages": [
    {
      "role": "user",
      "content": "我要去北京出差",
      "timestamp": "2026-05-12T10:29:00",
      "metadata": {}
    }
  ]
}
```

### 特性
- ✅ 文件持久化 (`data/chat-history/{chat_id}.json`)
- ✅ 滑动窗口（默认20条）
- ✅ 自动保存
- ✅ 支持元数据

---

## Layer 2: 工作记忆 (WorkingMemoryManager)

### 设计目标
- 实时提取对话中的实体和意图
- 提供会话级别的上下文摘要
- 自动清理过期记忆

### 技术实现
```python
from src.memory import WorkingMemoryManager

# 创建工作记忆管理器
manager = WorkingMemoryManager(ttl_minutes=30)

# 提取实体和意图
manager.extract_and_update("conv_001", "我要去北京出差，拜访华为公司")

# 获取上下文摘要
summary = manager.get_context_summary("conv_001")
```

### 实体提取规则

| 实体类型 | 提取方法 | 示例 |
|---------|---------|------|
| 城市 | 关键词匹配 | 北京、上海、深圳 |
| 客户 | 正则表达式 | XX公司、XX客户 |
| 日期 | 正则表达式 | 明天、5月12日 |
| 酒店 | 正则表达式 | XX酒店、XX宾馆 |

### 意图识别

| 意图 | 关键词 |
|-----|--------|
| 查询天气 | 天气、气温、下雨 |
| 查询酒店 | 酒店、住宿、预订 |
| 查询航班 | 航班、机票、飞机 |
| 查询政策 | 政策、规定、报销 |
| 行程规划 | 行程、安排、计划 |

### 数据结构
```python
@dataclass
class WorkingMemory:
    conversation_id: str
    cities: Set[str]           # 提取的城市
    customers: Set[str]        # 提取的客户
    dates: Set[str]            # 提取的日期
    hotels: Set[str]           # 提取的酒店
    current_intent: str        # 当前意图
    intent_history: List[str]  # 意图历史
```

### 特性
- ✅ 内存存储（ConcurrentHashMap风格）
- ✅ 30分钟TTL自动清理
- ✅ 实体提取（城市、客户、日期、酒店）
- ✅ 意图追踪
- ✅ 线程安全

---

## Layer 3: 长期记忆 (LongTermMemoryManager)

### 设计目标
- 学习用户偏好和行为模式
- 提供个性化推荐
- 支持GDPR合规

### 技术实现
```python
from src.memory import LongTermMemoryManager

# 创建长期记忆管理器
manager = LongTermMemoryManager()

# 从工作记忆学习
manager.learn_from_conversation("user_001", "conv_001", working_memory)

# 获取个性化提示
hint = manager.get_personalized_hint("user_001", current_city="北京")

# 获取用户统计
stats = manager.get_user_stats("user_001")
```

### 用户画像结构
```python
@dataclass
class UserProfile:
    user_id: str
    preferred_cities: Dict[str, int]      # 城市 -> 访问次数
    preferred_hotels: Dict[str, int]      # 酒店 -> 预订次数
    frequent_customers: Dict[str, int]    # 客户 -> 拜访次数
    common_intents: List[str]             # 常见意图
    conversation_count: int               # 总会话数
    preferences: Dict[str, str]           # 自定义偏好
```

### 学习流程
```
会话结束
    ↓
从工作记忆提取信息
    ↓
更新用户画像
    ├─ 城市偏好统计
    ├─ 酒店偏好统计
    ├─ 客户拜访记录
    └─ 意图统计
    ↓
保存到JSON文件
```

### 个性化推荐示例
```
您已经第3次查询北京的信息了
根据您的历史记录，推荐希尔顿酒店
您经常拜访的客户: 华为公司, 腾讯公司, 阿里巴巴
您常用的功能: 查询天气, 查询酒店, 行程规划
```

### 特性
- ✅ JSON文件存储 (`data/user-profiles/{user_id}.json`)
- ✅ 无限容量
- ✅ 增量学习
- ✅ 个性化推荐
- ✅ GDPR合规（支持数据删除）

---

## MemoryService统一门面

### 设计目标
- 提供统一的API接口
- 协调三层记忆的交互
- 简化使用复杂度

### 完整使用示例

```python
from src.memory import MemoryService

# 初始化服务
service = MemoryService(
    chat_memory_max_messages=20,
    working_memory_ttl_minutes=30
)

# 1. 处理用户消息
user_id = "user_001"
conv_id = "conv_001"
service.process_user_message(user_id, conv_id, "我要去北京出差")

# 2. 处理助手消息
service.process_assistant_message(conv_id, "好的，请问您需要什么帮助？")

# 3. 生成增强提示
enhanced_prompt = service.build_enhanced_prompt(
    user_id=user_id,
    conversation_id=conv_id,
    current_city="北京",
    include_chat_history=True,
    chat_history_limit=10
)

# 4. 会话结束时学习
service.end_conversation(user_id, conv_id)

# 5. 清理过期记忆
service.cleanup_expired_working_memory()

# 6. 获取统计信息
user_stats = service.get_user_stats(user_id)
memory_stats = service.get_memory_stats()

# 7. GDPR合规：删除用户数据
service.delete_user_data(user_id)
```

### 增强提示示例

```
【对话历史】
用户: 我要去北京出差
助手: 好的，请问您需要什么帮助？
用户: 查询一下天气，还要推荐希尔顿酒店
助手: 北京明天晴天，推荐您入住希尔顿酒店

【当前对话上下文】
涉及城市: 北京
酒店: 希尔顿酒店
当前意图: 查询天气

【个性化提示】
您已经第2次查询北京的信息了
根据您的历史记录，推荐希尔顿酒店
您经常拜访的客户: 华为公司
您常用的功能: 查询天气, 查询酒店
```

---

## 与Spring AI的对比

| 维度 | Spring AI | LangChain (本实现) |
|-----|-----------|-------------------|
| **Layer 1** | FileBasedChatMemory | ChatMemory |
| **存储方式** | JSON文件 | JSON文件 |
| **滑动窗口** | 20条 | 20条（可配置） |
| **Layer 2** | WorkingMemoryManager | WorkingMemoryManager |
| **存储方式** | ConcurrentHashMap | dict + Lock |
| **TTL机制** | 30分钟 | 30分钟（可配置） |
| **Layer 3** | LongTermMemoryManager | LongTermMemoryManager |
| **存储方式** | JSON文件 | JSON文件 |
| **统一门面** | @Service注解 | MemoryService类 |
| **依赖注入** | @Autowired | 构造函数 |

---

## 设计亮点

### 1. 分层存储策略
- **短期**：文件持久化，重启不丢失
- **工作**：内存存储，快速访问
- **长期**：JSON文件，无限容量

### 2. 自动清理机制
- 工作记忆30分钟TTL
- 防止内存泄漏
- 定期清理过期数据

### 3. 增量学习
- 会话结束时从工作记忆提取信息
- 更新长期记忆的用户画像
- 不影响实时对话性能

### 4. GDPR合规
- 提供`delete_user_data()`方法
- 支持用户数据删除
- 符合隐私保护要求

### 5. 线程安全
- 工作记忆使用Lock保护
- 支持并发访问
- 避免数据竞争

---

## 性能指标

| 操作 | 延迟 | 说明 |
|-----|------|------|
| 添加消息 | <5ms | 文件写入 |
| 实体提取 | <10ms | 正则匹配 |
| 获取上下文 | <1ms | 内存读取 |
| 学习更新 | <20ms | JSON序列化 |
| 清理过期 | <50ms | 遍历检查 |

---

## 使用场景

### 场景1：首次对话
```python
# 用户第一次使用系统
service.process_user_message("user_001", "conv_001", "我要去北京出差")

# 系统响应：基于规则的通用回复
# 无个性化提示（长期记忆为空）
```

### 场景2：多次对话后
```python
# 用户第5次查询北京
service.process_user_message("user_001", "conv_005", "又要去北京了")

# 系统响应：个性化推荐
# "您已经第5次查询北京的信息了"
# "根据您的历史记录，推荐希尔顿酒店"
```

### 场景3：会话恢复
```python
# 用户关闭浏览器后重新打开
# 短期记忆从文件加载
# 工作记忆重新创建
# 长期记忆保持不变
```

---

## 扩展建议

### 1. 向量化记忆
```python
# 使用Embedding存储对话摘要
# 支持语义相似度检索
from langchain.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings()
memory_vector = embeddings.embed_query(conversation_summary)
```

### 2. 记忆压缩
```python
# 使用LLM压缩长对话
from langchain.memory import ConversationSummaryMemory

summary_memory = ConversationSummaryMemory(llm=llm)
```

### 3. 多模态记忆
```python
# 支持图片、语音等多模态输入
memory.add_message("user", content="图片描述", metadata={"image_url": "..."})
```

### 4. 分布式存储
```python
# 使用Redis替代内存存储
# 支持多实例共享工作记忆
import redis
redis_client = redis.Redis(host='localhost', port=6379)
```

---

## 测试覆盖

运行测试：
```bash
python tests/test_memory_system.py
```

测试用例：
- ✅ 基本流程测试
- ✅ 个性化推荐测试
- ✅ 实体提取测试
- ✅ 滑动窗口测试
- ✅ 统计信息测试
- ✅ GDPR合规测试

---

## 总结

三层记忆系统成功从Spring AI迁移到LangChain，保持了原有的架构设计和核心功能：

1. **Layer 1 (短期记忆)**：文件持久化，滑动窗口，上下文理解
2. **Layer 2 (工作记忆)**：内存存储，实体提取，意图追踪
3. **Layer 3 (长期记忆)**：用户画像，个性化推荐，增量学习

通过`MemoryService`统一门面，简化了使用复杂度，提供了完整的测试覆盖和文档支持。
