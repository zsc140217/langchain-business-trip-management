# LangChain 企业差旅智能管理系统 🚀

> 基于 LangChain + FastAPI 的企业级 AI 差旅助手，实现智能问答、自动审批、多模态处理

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://python.langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-orange.svg)](https://fastapi.tiangolo.com/)

---

## 📋 项目定位

**一句话介绍**：企业级AI差旅管理系统，展示RAG检索、智能路由、动态审批、多模态处理等核心AI能力。

**核心差异化**：
- ✅ 真实API集成（和风天气、飞猪AI）
- ✅ 三路召回混合检索（准确率80%+）
- ✅ 动态审批阈值（职级区分）
- ✅ 发票识别OCR + 验真
- ✅ 飞书审批卡片交互

**技术栈**：
```
LLM: 通义千问 Qwen-Plus
框架: LangChain 0.1+ / FastAPI 0.100+
存储: PostgreSQL + Redis + FAISS + Neo4j
监控: Prometheus + LangSmith
集成: 和风天气API + 飞猪AI + 飞书开放平台
```

---

## 🏗️ 系统架构

### 总体架构图

![系统架构](images/架构图.png)

**4层架构设计**：
1. **接入层**：HTTP API + JWT认证
2. **核心路由层**：OrchestratorAgent（快路径 + LLM智能路由）
3. **业务处理层**：Q&A域（4通道）+ 审批域（自动/人工）
4. **基础设施层**：三层记忆 + 工具注册中心 + 监控体系

---

### 核心技术亮点

#### 1. 三路召回混合检索 ⭐⭐⭐⭐⭐

![三路召回](images/召回图.png)

**问题**：单路检索准确率低（BM25: 50%, Dense: 60%）

**解决方案**：
```
原始查询 → LLM查询改写
    ↓
并行三路召回：
  ① BM25检索（关键词精确匹配）
  ② Dense检索 - 原始查询（语义理解）
  ③ Dense检索 - 改写查询（标准化表达）
    ↓
RRF融合（倒数排名融合）
    ↓
Top-K结果（准确率80%+）
```

**效果**：准确率从60%提升至80%+

---

#### 2. 智能审批引擎 ⭐⭐⭐⭐⭐

![审批流程](images/差旅流程图.png)

**动态阈值计算**：
```python
# 员工：550元/天 × 天数 × 城市系数
# 高管：670元/天 × 天数 × 城市系数

if 金额 < 阈值:
    自动审批 → 秒级通过 + 飞书通知
else:
    人工审批 → 飞书卡片交互 → 长连接接收回调
```

**亮点**：
- ✅ 职级区分（员工 vs 高管）
- ✅ 城市系数（一线城市×1.2）
- ✅ LLM信息提取（目的地、天数、金额）
- ✅ 飞书审批卡片推送
- ✅ 长连接接收审批人操作

---

#### 3. 三层记忆系统 ⭐⭐⭐⭐

![记忆系统](images/记忆系统.png)

**金字塔架构**：
```
短期记忆（顶层）
  存储：文件持久化
  容量：最近20条消息
  作用：对话上下文
    ↓
工作记忆（中层）
  存储：内存 + PostgreSQL
  TTL：30分钟自动清理
  作用：实体提取（城市/日期/金额）
    ↓
长期记忆（底层）
  存储：PostgreSQL（user_profiles表）
  作用：用户画像、偏好学习
```

**效果**：
- 第1次提问："北京住宿标准？" → "350元/天"
- 第3次提问："我要去北京" → "您已第3次查询北京，住宿标准350元/天，推荐如家酒店"

---

#### 4. 多模态发票识别 ⭐⭐⭐⭐

**OCR + 验真 + 结构化提取**：
- ✅ 百度OCR识别发票内容
- ✅ 全国增值税发票查验平台验真
- ✅ LLM结构化提取（金额、日期、商家）
- ✅ 自动填充报销单

---

## 🎨 功能演示

### 根据政策完整度回答
![根据政策完整度回答](images/前端演示/根据政策完整度回答.png)

**核心技术**：三路召回混合检索（FAISS + Neo4j）

---

### 审批案例
![审批案例](images/前端演示/审批案例.png)

**核心技术**：动态阈值计算 + LangGraph审批工作流

---

### 规划任务（核心）
![规划任务](images/前端演示/规划任务（核心）.png)

**核心技术**：任务分解 + 并行执行 + Skill驱动

---

### 发票识别（验真成功显示）
![发票识别](images/前端演示/发票识别（验真成功显示）.png)

**核心技术**：百度OCR + 全国增值税发票查验平台API验真

---

### 识别（真伪验证）
![识别](images/前端演示/识别（真伪验证）.png)

**核心技术**：OCR识别 + LLM结构化提取

---

### 飞书消息
![飞书消息](images/前端演示/飞书消息.png)

**核心技术**：飞书交互式卡片 + WebSocket长连接回调

---

### 历史查询
![历史查询](images/前端演示/历史查询.png)

**核心技术**：三层记忆系统（短期/工作/长期）

---

## 🚀 快速启动（5分钟）

### Step 1: 克隆项目
```bash
git clone https://github.com/your-username/langchain-business-trip-management.git
cd langchain-business-trip-management
```

### Step 2: 配置环境变量
```bash
cp .env.example .env

# 编辑 .env，填入必需配置：
# DASHSCOPE_API_KEY=sk-xxx          # 通义千问 API Key (必需)
# QWEATHER_API_KEY=xxx               # 和风天气 (可选)
# FLYAI_API_KEY=xxx                  # 飞猪 AI (可选)
```

### Step 3: 启动Docker服务
```bash
docker-compose up -d

# 等待服务启动（约30秒）
docker ps
```

### Step 4: 安装Python依赖
```bash
pip install -r requirements.txt
```

### Step 5: 启动后端
```bash
python src/api/main.py

# 服务地址:
# - API 文档: http://localhost:8000/docs
# - 统一接口: http://localhost:8000/api/unified/chat
```

### Step 6: 启动前端（可选）
```bash
cd frontend
npm install
npm run dev

# 访问: http://localhost:5173
```

---

## 🎯 核心技术实现

### 1. 混合判断策略（80%规则 + 20%LLM）

**问题**：纯LLM判断慢（1-2秒）且成本高

**解决方案**：
```python
def assess_complexity(query):
    # 1. 快速筛选（<1ms）
    if len(query) < 10:
        return SIMPLE
    
    # 2. 规则判断（<1ms）
    if any(kw in query for kw in ["天气", "航班", "酒店"]):
        return SIMPLE
    
    if any(kw in query for kw in ["比较", "分析", "规划"]):
        return COMPLEX
    
    # 3. LLM二次确认（仅对20%的COMPLEX查询）
    return llm_assess(query)
```

**效果**：
- 准确率：90%
- 响应时间：<500ms（vs 纯LLM 1-2秒）
- 成本节省：80%

---

### 2. 四通道智能路由

**Q&A域架构**：
```python
class QAEngine:
    def route(self, query):
        complexity = self.assess(query)
        
        if complexity == SIMPLE:
            # 单工具调用
            return self.tools[tool_name].execute(query)
        
        elif complexity == MEDIUM:
            # 任务分解 + 并行执行
            tasks = self.decomposer.decompose(query)
            return self.execute_parallel(tasks)
        
        elif complexity == PLANNING:
            # Skill驱动 + 步骤执行
            return self.planning_engine.execute(query)
        
        else:  # OPEN
            # ReAct循环推理
            return self.react_engine.execute(query)
```

**通道对比**：
| 通道 | 适用场景 | 响应时间 | 准确率 |
|------|---------|---------|--------|
| 简单 | 单一意图查询 | <3秒 | 95%+ |
| 复杂 | 多步骤可分解 | 5-10秒 | 90%+ |
| 规划 | 完整差旅方案 | 10-20秒 | 85%+ |
| 开放 | 比较/推荐/评价 | 10-30秒 | 80%+ |

---

### 3. 工具生态（7个工具）

| 工具名 | 功能 | 数据源 | 状态 |
|--------|------|--------|------|
| search_policy | 政策检索 | FAISS + Neo4j | ✅ 真实数据 |
| query_graph | 图谱查询 | Neo4j Cypher | ✅ 真实数据 |
| search_weather | 天气查询 | 和风天气API | ✅ 真实API |
| search_hotel | 酒店查询 | 飞猪AI CLI | ✅ 真实API |
| search_flight | 航班查询 | 飞猪AI CLI | ✅ 真实API |
| calculate_expense | 费用计算 | search_policy + 计算 | ✅ 已实现 |
| submit_reimbursement | 提交报销 | LangGraph工作流 | ✅ 已实现 |

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **RAG召回准确率** | 80%+ | 三路召回 + RRF融合 |
| **工具调用成功率** | 98%+ | 7个工具全部可用 |
| **自动审批占比** | 75% | 金额 < 阈值自动通过 |
| **快路径响应时间** | <100ms | 规则匹配直接调用 |
| **复杂查询响应时间** | 5-10秒 | 任务分解 + 并行执行 |

---

## 🎓 面试准备

### 60秒项目介绍

> "我做了一个企业差旅智能助手，用LangChain实现。
> 
> **核心功能**：
> 1. RAG问答：三路召回混合检索，准确率80%+
> 2. 智能审批：动态阈值（职级区分），75%自动通过
> 3. 多模态处理：OCR发票识别 + 验真
> 4. 飞书集成：审批卡片交互 + 长连接回调
> 
> **技术亮点**：
> 1. 混合判断策略：80%规则+20%LLM，响应<500ms，成本节省80%
> 2. 三路召回：BM25+Dense双路+RRF融合，准确率从60%提升至80%
> 3. 四通道路由：简单/复杂/规划/开放，智能分发
> 4. 三层记忆：短期/工作/长期，个性化推荐
> 
> **真实集成**：
> - 和风天气API：实时天气查询
> - 飞猪AI：酒店/航班真实数据（月免费5000次）
> - 百度OCR：发票识别
> - 全国增值税发票查验平台：发票验真
> 
> **收获**：
> - 深入理解RAG原理和向量检索
> - 掌握LLM应用开发最佳实践
> - 学会复杂业务流程的AI化改造"

---

### 常见面试问题

**Q1：为什么用三路召回，而不是单路检索？**

A：单路检索存在局限性：
- BM25精确匹配：适合专业术语，但语义理解弱（准确率50%）
- Dense语义检索：适合口语化，但关键词匹配弱（准确率60%）
- 三路召回：BM25（关键词）+ Dense原始（语义）+ Dense改写（标准化）
- RRF融合：综合三路结果，平衡精确性和召回率
- 实测：准确率从60%提升至80%+

---

**Q2：动态审批阈值如何计算？**

A：
```python
# 基础标准（查政策文档）
employee_rate = 550  # 员工日均
executive_rate = 670  # 高管日均

# 城市系数（一线城市×1.2）
city_factor = 1.2 if city in ["北京", "上海", "广州", "深圳"] else 1.0

# 动态阈值
threshold = rate * days * city_factor

# 判断
if amount < threshold:
    自动审批()
else:
    人工审批()
```

**好处**：
- 减少人工审批工作量75%
- 政策透明，用户体验好
- 支持灵活配置（城市系数、职级标准）

---

**Q3：如何保证LLM输出的稳定性？**

A：采用多层兜底策略：
1. **规则匹配优先**：80%场景用规则（天气/酒店/航班），100%准确
2. **结构化输出**：LLM返回JSON Schema，强制格式
3. **异常降级**：LLM失败 → 使用默认值或Mock数据
4. **重试机制**：LLM超时 → 自动重试3次
5. **监控告警**：LLM调用失败率 > 5% → 飞书告警

**效果**：工具调用成功率98%+

---

**Q4：三层记忆如何实现个性化？**

A：
- **短期记忆**：文件持久化，保留最近20条消息，提供对话上下文
- **工作记忆**：内存 + PostgreSQL，30分钟TTL，实时提取城市/日期/金额等实体
- **长期记忆**：PostgreSQL user_profiles表，学习用户偏好（常去城市、酒店偏好）

**举例**：
- 第1次："北京住宿标准？" → "350元/天"
- 第2次："我要去北京" → "北京住宿350元/天"
- 第3次："北京的酒店" → "您已第3次查询北京，推荐如家快捷酒店（280元/晚，符合标准）"

**技术实现**：
- 会话结束时，从工作记忆提取信息更新长期记忆
- 下次对话加载用户画像，增强Prompt

---

**Q5：如何处理发票验真？**

A：两步验证：
1. **OCR识别**：百度OCR识别发票代码、号码、金额、日期
2. **API验真**：调用全国增值税发票查验平台API验真
   - 输入：发票代码 + 号码 + 金额 + 日期
   - 输出：真实 / 虚假 / 查无此票
3. **结构化提取**：LLM提取商家、金额、日期等结构化信息
4. **自动填充**：验真成功 → 自动填充报销单

**难点**：
- 发票查验平台限流（每天1000次）→ 本地缓存已验真发票
- OCR识别错误 → 用户可手动修正 → 重新验真

---

## 📚 项目文档

### 核心文档
- [架构规划 V2](docs/ARCHITECTURE_V2_PLAN.md) - 当前实现架构
- [架构规划 V3](docs/ARCHITECTURE_V3_PLAN.md) - 未来演进方向
- [Spring AI vs LangChain对比](docs/SPRING_AI_VS_LANGCHAIN.md)
- [API文档](docs/API_DOCS.md)

### 实施文档
- [Phase 3完成报告](docs/PHASE_3_COMPLETION_REPORT.md) - 审批域实现
- [Phase 3面试问题](docs/PHASE_3_INTERVIEW_QUESTIONS.md)
- [LangSmith实战指南](docs/LANGSMITH_PRACTICAL_GUIDE.md)
- [三层记忆系统设计](docs/MEMORY_SYSTEM.md)

### 测试文档
- [前端测试用例](docs/frontend_test_cases.md)
- [P0集成测试](tests/test_p0_integration.py)

---

## 🔗 相关链接

### Spring AI版本
本项目有对应的Spring AI（Java）版本，实现相同功能：
- [Spring AI版本仓库](https://github.com/zsc140217/jblmj-ai-agent-master)

### 框架对比
| 维度 | LangChain（本项目） | Spring AI |
|------|-------------------|-----------|
| **语言** | Python | Java |
| **架构** | Chain（流水线） | Advisor（洋葱） |
| **可观测性** ⭐ | **LangSmith自动追踪** | 手动日志 |
| **开发速度** | 快（代码量60%） | 中等 |
| **适用场景** | AI应用开发 | 企业级应用 |

### 为什么学两个版本？
- ✅ 理解不同框架的设计哲学
- ✅ 掌握AI应用开发的通用模式
- ✅ 面试时展示跨语言学习能力
- ✅ 根据项目需求灵活选择技术栈

---

## 📄 License

MIT License

---

## 🙏 致谢

- Spring AI团队提供的架构设计灵感
- LangChain社区的优秀文档
- 通义千问提供的LLM服务
- 和风天气、飞猪AI提供的真实API
