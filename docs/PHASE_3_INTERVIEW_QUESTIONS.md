# Phase 3 审批域 - 面试复习问题

本文档采用**口头问答**的方式帮助你理解 Phase 3 审批域的设计和实现。

## 目录

- [🟢 基础级别](#基础级别)
- [🟡 中级级别](#中级级别)
- [🔴 高级级别](#高级级别)
- [🎯 复习方法](#复习方法)

---

## 🟢 基础级别（理解核心概念）

### Q1: 什么是审批域？它和 Q&A 域有什么区别？

**审批域**是一个独立的业务域，专门处理报销申请、审批查询等有状态的工作流。

**关键区别**：
- **Q&A 域**：无状态查询，问完就结束（查天气、查政策）
- **审批域**：有状态流程，需要等待（提交申请 → 等待审批 → 查询结果）

**类比**：
- Q&A 域像"查字典"：问一次，答一次
- 审批域像"寄快递"：寄出去 → 追踪状态 → 收到货

**技术差异**：
- Q&A 域：工具调用 → 返回结果
- 审批域：状态机 + 工作记忆 + 外部回调

---

### Q2: 为什么审批要分自动审批和人工审批？

**原因**：平衡效率和风险控制

**自动审批**（金额 < 1000 元）：
- ✅ 优点：秒级响应，用户体验好
- ✅ 优点：减少审批人工作量
- ❌ 缺点：有风险（需要设定合理阈值）

**人工审批**（金额 ≥ 1000 元）：
- ✅ 优点：高金额需要人工把关
- ✅ 优点：可以审查合理性
- ❌ 缺点：响应慢（需要等待审批人）

**设计思路**：
```
小额高频 → 自动化（规则决策）
大额低频 → 人工审核（LLM + 人类智能）
```

---

### Q3: 工作记忆为什么要存储审批状态？

**核心原因**：审批是长时间流程，需要持久化状态

**场景举例**：
1. 上午 10 点：用户提交报销（金额 3000 元）
2. 下午 2 点：用户查询"我的审批进度怎么样了？"
3. 下午 4 点：审批人批准
4. 下午 4:05：用户再次查询 → 看到"已通过"

**存储内容**：
```python
{
    "approvals": {
        "APV20260712001": {
            "approval_id": "APV20260712001",
            "user_id": "user_001",
            "destination": "北京",
            "amount": 3000,
            "status": "pending",
            "submit_time": "2026-07-12 10:00:00"
        }
    }
}
```

---

## 🟡 中级级别（理解技术实现）

### Q4: ApprovalEngine 的核心职责是什么？

**ApprovalEngine 的 5 大职责**：

1. **接收申请** - `execute()`
2. **决策路由** - 根据金额阈值选择路径
3. **状态管理** - 更新工作记忆
4. **发送通知** - 调用 FeishuClient
5. **处理回调** - 处理审批结果（Phase 4）

**决策流程**：
```python
def execute(self, query, user_id, conversation_id):
    # 1. 提取信息
    info = self._extract_application_info(query, user_id)
    
    # 2. 路由决策
    if info["estimated_amount"] < self.auto_approval_threshold:
        return self._auto_approve(info)
    else:
        return self._manual_approval(info)
```

---

### Q5: LangGraph 的 interrupt() 机制是如何工作的？

**interrupt() 的作用**：暂停图的执行，等待外部输入

**执行流程**：
```
第一次调用 graph.invoke(state)
    ↓
执行到 approval_node
    ↓
遇到 interrupt() → 图暂停
    ↓
外部审批人做决策
    ↓
第二次调用 graph.invoke(state, input=decision)
    ↓
继续执行并返回结果
```

**必要条件**：
- 必须有 **checkpointer**（MemorySaver）
- 必须有 **thread_id**（隔离不同会话）

---

### Q6: 飞书通知为什么要异步发送？

**为什么异步？**

1. **不阻塞主流程**：审批不应该因为通知失败而失败
2. **提升响应速度**：立即返回，不等待网络请求
3. **容错能力**：飞书 API 可能超时、限流

**失败处理**：
```python
try:
    self.feishu_client.send_card_message(...)
    logger.info("飞书通知已发送")
except Exception as e:
    logger.error(f"飞书通知失败: {e}")
    # 继续执行，不抛异常
```

**优先级**：审批流程正确性 > 飞书通知成功率

---

## 🔴 高级级别（理解架构设计）

### Q7: 为什么要三层架构？

**三层架构**：

- **Layer 1: OrchestratorAgent** - 统一入口，路由到不同业务域
- **Layer 2: ApprovalEngine** - 业务逻辑封装
- **Layer 3: LangGraph** - 工作流引擎

**优势**：
- ✅ 单一职责：每层只做一件事
- ✅ 可测试性：每层可以独立 Mock 测试
- ✅ 可扩展性：新增审批类型只需修改 ApprovalEngine
- ✅ 可维护性：业务逻辑不散落在工作流节点中

---

### Q8: 审批域的状态机设计

**状态转换**：
```
提交申请 → pending → approved/rejected（终态）
自动审批 → 直接 approved
```

**防止状态混乱**：
- 使用不可变更新模式
- 并发控制（加锁）
- 不允许从终态再转换

---

### Q9: 如何保证并发安全？

**并发场景**：

1. **审批单号冲突** - 线程安全计数器 + 锁
2. **工作记忆并发写入** - WorkingMemoryManager 内置锁
3. **LangGraph 并发** - thread_id 隔离

---

### Q10: Phase 3 和 Phase 4 的边界

**Phase 3**：
- ✅ 核心流程验证
- ✅ 工作记忆存储（内存）
- ✅ 基础飞书通知

**Phase 4 增强**：
- 数据库持久化
- 真实 Webhook 回调
- 监控告警
- 审批历史查询

**为什么分阶段**：降低风险、快速迭代、增量交付

---

## 🎯 复习方法

### 方法 1：逐个问题口头回答
1. 只看问题，不看答案
2. 口头回答或写在纸上
3. 对比答案，找差距
4. 重复直到流畅

### 方法 2：模拟技术面试
找同学当面试官，随机提问

### 方法 3：画图理解
画出架构图、状态机、数据流图

### 方法 4：代码实战
实现简化版的 ApprovalEngine

---

## 📚 扩展阅读

- [LangGraph interrupt() 机制](https://python.langchain.com/docs/langgraph/how-tos/human_in_the_loop/)
- [飞书群机器人 Webhook](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN)
- [状态机设计模式](https://refactoring.guru/design-patterns/state)

---

**创建时间**: 2026-07-12  
**Phase 3 完成状态**: 33/33 测试通过 ✅
