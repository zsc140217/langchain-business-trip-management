# 架构图 AI 绘图提示词

## 图1: 系统总体架构图（推荐）

### 提示词（中文）
```
绘制一个企业差旅管理系统的技术架构图，现代简洁风格，使用蓝色和灰色配色方案。

架构分为5层，从上到下：

【用户层】
- 飞书用户（图标：人物头像）
- 发送消息：文本查询、图片（发票）

【网关层】
- 飞书网关（图标：云朵）
  - Webhook接收
  - 签名验证
  - 双向交互

【核心层】- 最重要
- OrchestratorAgent（统一入口，图标：路由器）
  - 左侧：快路径匹配（天气/酒店/航班）→ 直接调用工具
  - 右侧：LLM智能路由 → 分发到两个业务域

【业务层】- 并排显示
- 左侧：Q&A域（图标：问答气泡）
  - 简单通道：单工具调用
  - 复杂通道：任务分解+并行
  - 规划通道：Skill驱动
  - 开放通道：ReAct循环

- 右侧：审批域（图标：文档+印章）
  - 自动审批：<阈值 → 秒级通过
  - 人工审批：≥阈值 → 飞书卡片
  - 状态查询：工作记忆

【基础设施层】- 底部横跨
- 三层记忆系统（图标：数据库）
  - 短期记忆：对话历史
  - 工作记忆：实体提取
  - 长期记忆：用户画像
  
- 工具注册中心（图标：工具箱）
  - 政策检索、天气查询、酒店/航班（飞猪API）
  
- 监控体系（图标：仪表盘）
  - Prometheus指标
  - LangSmith追踪
  - 飞书告警

数据流动：用实线箭头表示请求流，虚线箭头表示异步通知。
整体采用分层架构风格，每层用不同色块区分，关键路径用加粗箭头标注。
```

### 提示词（English - 备用）
```
Create a technical architecture diagram for an enterprise business travel management system. Modern minimalist style with blue and gray color scheme.

Architecture in 5 layers from top to bottom:

【User Layer】
- Feishu users (icon: user avatar)
- Send messages: text queries, images (invoices)

【Gateway Layer】
- Feishu Gateway (icon: cloud)
  - Webhook receiver
  - Signature verification
  - Bidirectional interaction

【Core Layer】- Most Important
- OrchestratorAgent (unified entry, icon: router)
  - Left: Fast-path matching (weather/hotel/flight) → direct tool call
  - Right: LLM intelligent routing → dispatch to two business domains

【Business Layer】- Side by side
- Left: Q&A Domain (icon: chat bubble)
  - Simple channel: single tool call
  - Complex channel: task decomposition + parallel
  - Planning channel: Skill-driven
  - Open channel: ReAct loop

- Right: Approval Domain (icon: document + seal)
  - Auto approval: < threshold → instant pass
  - Manual approval: ≥ threshold → Feishu card
  - Status query: working memory

【Infrastructure Layer】- Bottom spanning
- Three-tier Memory System (icon: database)
  - Short-term: conversation history
  - Working: entity extraction
  - Long-term: user profile
  
- Tool Registry (icon: toolbox)
  - Policy search, weather, hotel/flight (Fliggy API)
  
- Monitoring (icon: dashboard)
  - Prometheus metrics
  - LangSmith tracing
  - Feishu alerts

Data flow: solid arrows for requests, dashed arrows for async notifications.
Use layered architecture style, each layer with different color blocks, key paths with bold arrows.
```

---

## 图2: 审批流程图（可选）

### 提示词
```
绘制一个差旅报销审批流程图，流程图风格。

流程从上到下：

【起点】用户提交报销申请："我要报销去北京的费用800元"

↓

【决策节点1】LLM信息提取
- 提取：目的地、金额、天数
- 调用政策检索：查询审批阈值

↓

【决策节点2】金额判断
- 条件：金额 < 阈值？
  
  【是】→ 自动审批路径（左侧绿色）
    1. 审批通过
    2. 更新工作记忆
    3. 飞书通知申请人："✅ 已自动通过"
    4. 结束
  
  【否】→ 人工审批路径（右侧橙色）
    1. 生成审批单
    2. 飞书卡片推送审批人
    3. 等待审批人点击【同意】/【拒绝】
    4. 长连接接收回调
    5. 更新审批状态
    6. 通知申请人
    7. 结束

使用绿色表示自动化流程，橙色表示人工介入，灰色表示等待状态。
```

---

## 图3: 三路召回检索流程（技术亮点）

### 提示词
```
绘制一个RAG检索优化流程图，展示三路召回混合检索策略。

从左到右分为3个阶段：

【输入】用户查询："北京的住宿标准"

↓

【阶段1：查询改写】
- LLM改写查询 → "北京市差旅住宿补贴标准"

↓

【阶段2：三路并行召回】（3个并行分支）

分支1（上）：BM25检索
  - 方法：关键词精确匹配
  - 数据源：FAISS向量库
  - 返回：Top-5文档（侧重精确匹配）

分支2（中）：Dense检索 - 原始查询
  - 方法：语义向量检索
  - 数据源：FAISS向量库
  - 返回：Top-5文档（侧重语义理解）

分支3（下）：Dense检索 - 改写查询
  - 方法：语义向量检索
  - 数据源：FAISS向量库
  - 返回：Top-5文档（侧重标准化表达）

↓

【阶段3：RRF融合】
- 算法：倒数排名融合（Reciprocal Rank Fusion）
- 公式：RRF_score = Σ 1/(k + rank_i)
- 输出：融合后的Top-3文档

↓

【输出】返回最相关文档 → LLM生成答案

每个分支用不同颜色标识：
- BM25（蓝色）：精确匹配
- Dense原始（绿色）：语义理解
- Dense改写（紫色）：标准化

在右侧标注性能指标：
- 单路BM25：准确率50%
- 单路Dense：准确率60%
- 三路召回+RRF：准确率80%+
```

---

## 图4: 记忆系统架构（可选）

### 提示词
```
绘制三层记忆系统架构图，金字塔结构。

从上到下3层：

【第1层：短期记忆】（顶部，最小）
- 存储：文件（data/chat-history/）
- 容量：最近20条消息
- TTL：会话结束后持久化
- 作用：提供对话上下文
- 图标：聊天气泡

【第2层：工作记忆】（中间，中等）
- 存储：内存 + PostgreSQL (extracted_entities表)
- 容量：30分钟内提取的实体
- TTL：30分钟自动清理
- 作用：实时提取城市、日期、金额等关键信息
- 图标：脑图

【第3层：长期记忆】（底部，最大）
- 存储：PostgreSQL (user_profiles表)
- 容量：无限制
- TTL：永久保存
- 作用：学习用户偏好、行为模式
- 图标：档案柜

在右侧标注数据流：
- 上：用户消息 → 3层同时更新
- 下：会话结束时，工作记忆提取信息 → 更新长期记忆

用渐变色表示记忆的时间跨度：
- 短期：亮蓝色（当前会话）
- 工作：蓝绿色（30分钟）
- 长期：深蓝色（永久）
```

---

## 使用建议

### 推荐AI工具
1. **Midjourney**（最推荐）
   - 命令：`/imagine prompt: [上述提示词]`
   - 参数：`--ar 16:9 --style raw --v 6`
   - 适合：需要高质量渲染

2. **DALL-E 3**（ChatGPT内置）
   - 直接粘贴提示词
   - 优点：理解中文好，修改方便

3. **Stable Diffusion**（免费）
   - 需要添加技术关键词：`technical diagram, architecture, flowchart`
   - 可能需要多次迭代

4. **通义万相 / 文心一格**（国产）
   - 中文理解好
   - 免费额度充足

### 生成后优化
- 如果文字不清晰：用Figma/PPT添加文字标注
- 如果布局不理想：提供反馈重新生成
- 建议生成2-3个版本，选最满意的
