# Module 6: Memory System - 记忆系统

三层记忆架构，用于智能对话上下文管理和历史记忆检索。

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│              CompositeMemory                        │
│           (组合记忆 - 统一接口)                       │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│BufferMemory  │  │SummaryMemory │  │VectorMemory  │
│(短期缓冲)     │  │(中期摘要)     │  │(长期检索)     │
└──────────────┘  └──────────────┘  └──────────────┘
  最近5轮对话      历史对话摘要      语义向量检索
```

## 核心组件

### 1. BufferMemory - 对话缓冲记忆
- 保留最近N轮对话的完整内容
- ConversationBufferMemory (LangChain)
- 固定窗口滑动策略

### 2. SummaryMemory - 摘要记忆
- 自动生成和维护对话历史摘要
- ConversationSummaryMemory + ChatTongyi
- Token限制管理

### 3. VectorMemory - 向量记忆
- 基于语义相似度的长期记忆检索
- FAISS + DashScopeEmbeddings
- 持久化存储和加载

### 4. CompositeMemory - 组合记忆
- 统一管理三层记忆
- 智能上下文组合
- 灵活启用/禁用各层

## 快速开始

```python
from src.modules.module_6_memory import CompositeMemory
import os

os.environ['DASHSCOPE_API_KEY'] = 'your-api-key'

# 初始化
memory = CompositeMemory(
    buffer_max_turns=5,
    summary_max_tokens=2000,
    vector_k=3
)

# 添加对话
memory.add_exchange(
    "I want to book a flight",
    "Sure! When would you like to travel?",
    metadata={'intent': 'booking'}
)

# 获取上下文
context = memory.get_context(query="travel plans")
print(context)
```

## 测试

```bash
pytest tests/unit/module_6_memory/ -v
```

## 依赖项

- langchain>=0.1.0
- langchain-community>=0.0.20
- faiss-cpu>=1.7.4
- dashscope>=1.14.0
