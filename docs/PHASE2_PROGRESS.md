# Phase 2 进度文档 - Q&A 域实施

**文档版本**: v1.0  
**创建时间**: 2026-07-11  
**当前状态**: 🔵 进行中  
**预计完成**: 3-4天  

---

## 📊 总体进度

```
Phase 2: Q&A 域实施
├─ 核心基础设施        ⏳ 20% (1/5)
├─ 执行引擎            ⬜ 0% (0/3)
└─ 集成与测试          ⬜ 0% (0/3)
```

**完成度**: 9% (1/11 任务)

---

## ✅ 已完成任务

### 1. 城市名翻译工具 ✅ (2026-07-11)

**文件**: `src/utils/city_translator.py` (344 行)

**功能**:
- 覆盖 200+ 中国城市（直辖市、省会、地级市）
- 支持中英文双向查询
- 字典映射（O(1) 查找速度）
- 失败时返回 None（由调用方决定是否用 LLM 翻译）

**核心 API**:
```python
from src.utils.city_translator import normalize_city_name, is_supported_city

# 标准化城市名（英文 → 中文）
city_zh = normalize_city_name("Beijing", "zh")  # "北京"

# 检查是否支持
if is_supported_city("Hangzhou"):  # True
    ...
```

**统计数据**:
- 支持城市数: 200+
- 查找时间: O(1)
- 覆盖范围: 4个直辖市 + 31个省会 + 100+地级市

**测试**:
```bash
python src/utils/city_translator.py
# 输出: 支持的城市数量: 200+
# Beijing -> 北京
# beijing -> 北京
# UnknownCity -> None
```

**集成位置**:
- `src/tools/hotel_adapter.py` - invoke 方法开始处
- `src/tools/flight_adapter.py` - invoke 方法开始处
- `src/agents/orchestrator_agent.py` - 工具调用前
- `src/agents/qa_engine.py` - 简单通道调用前

---

## 🔵 进行中任务

### 2. OrchestratorAgent - 统一入口 ⏳ (预计今天完成)

**文件**: `src/agents/orchestrator_agent.py`

**职责**:
1. 加载记忆上下文
2. 规则匹配（快路径）
3. LLM 路由决策（Q&A 域 vs 审批域）
4. Q&A 域内再分四个通道
5. 记忆更新
6. 监控埋点

**设计要点**:
- **规则匹配优先**: 天气/航班/酒店/政策标准 → 直接调工具
- **城市名翻译**: 调用酒店/航班工具前，先用 `city_translator` 转中文
- **LLM 路由兜底**: 规则未匹配时，用 LLM 分析意图
- **审批域拦截**: 检测"报销/申请/审批"关键词 → 路由到 ApprovalEngine

**快路径规则**:
```python
fast_rules = {
    "weather": ["天气", "温度", "下雨", "气温"],
    "flight": ["航班", "机票", "飞机"],
    "hotel": ["酒店", "宾馆", "住宿"],
    "policy_search": ["标准", "报销", "补贴", "规定", "政策"],
}
```

**LLM 路由 Prompt**:
```
分析用户查询，返回 JSON 格式路由决策。

域分类:
- qa_domain: 政策查询、关系查询、比较推荐
- approval_domain: 提交报销、查审批状态

只返回 JSON: {"domain": "qa_domain/approval_domain", "reason": "原因"}
```

**类结构**:
```python
class OrchestratorAgent:
    def __init__(self, llm, memory_service, tools, approval_engine, monitor):
        self.llm = llm
        self.memory = memory_service
        self.tools = tools
        self.approval_engine = approval_engine
        self.monitor = monitor
        self.qa_engine = QAEngine(llm, memory_service, tools)
        self.fast_rules = {...}
    
    def route(self, query, user_id, conversation_id) -> dict:
        """统一路由入口"""
        # 1. 加载记忆
        context = self.memory.build_enhanced_prompt(user_id, conversation_id)
        
        # 2. 规则匹配
        matched = self._match_fast_rules(query)
        if matched:
            return self._execute_fast(matched, query, context)
        
        # 3. 审批域路由
        if self._is_approval_query(query):
            return self.approval_engine.execute(query, user_id, conversation_id)
        
        # 4. Q&A 域路由
        return self.qa_engine.execute(query, context)
    
    def _match_fast_rules(self, query: str) -> Optional[str]:
        """规则匹配（快路径）"""
        for rule_name, keywords in self.fast_rules.items():
            if any(kw in query for kw in keywords):
                return rule_name
        return None
    
    def _execute_fast(self, rule_name: str, query: str, context: str) -> dict:
        """执行快路径"""
        if rule_name == "weather":
            return self.tools["query_weather"].invoke({"city": extract_city(query)})
        elif rule_name == "hotel":
            city = extract_city(query)
            city_zh = normalize_city_name(city, "zh")
            return self.tools["search_hotels"].invoke({"city": city_zh})
        elif rule_name == "flight":
            cities = extract_cities(query)
            cities_zh = [normalize_city_name(c, "zh") for c in cities]
            return self.tools["search_flights"].invoke({"departure_city": cities_zh[0], "arrival_city": cities_zh[1]})
        elif rule_name == "policy_search":
            return self.tools["search_policy"].invoke({"query": query})
    
    def _is_approval_query(self, query: str) -> bool:
        """检测是否为审批域查询"""
        approval_keywords = ["报销", "申请", "审批", "提交出差", "我的申请", "审批进度"]
        return any(kw in query for kw in approval_keywords)
```

**状态**: 设计完成，待实现

---

### 3. QAEngine - Q&A 域执行器 ⏳ (预计今天完成)

**文件**: `src/agents/qa_engine.py`

**职责**:
- 接收 OrchestratorAgent 的 Q&A 域请求
- LLM 分析查询类型（simple/complex/planning/open）
- 调度四个通道执行

**四通道分类**:
| 通道 | 适用场景 | 执行引擎 | 示例 |
|------|---------|---------|------|
| simple | 单工具能回答 | 直接调工具 | "北京住宿标准" |
| complex | 多步骤可分解 | TaskDecomposer + Multi-Agent | "去杭州出差3天要多少钱" |
| planning | 完整差旅方案 | Planning Skill | "帮我安排下周去深圳出差" |
| open | 比较/推荐 | ReAct 循环 | "飞机和高铁哪个划算" |

**LLM 路由 Prompt**:
```
分析用户查询，返回 JSON 格式路由决策。

分类标准:
- simple: 单一意图，一个工具能回答
  示例: "北京住宿标准"、"今天天气怎么样"
- complex: 多步骤，可分解为明确子任务
  示例: "去杭州出差3天，查天气查酒店算费用"
- planning: 需要完整差旅方案
  示例: "帮我安排下周去深圳出差"
- open: 比较/推荐/评价
  示例: "飞机和高铁哪个划算"、"夏天适合去哪里出差"

只返回 JSON: 
{"type": "simple/complex/planning/open", "tool": "工具名(仅 simple 需要)", "reason": "原因"}
```

**类结构**:
```python
class QAEngine:
    def __init__(self, llm, memory_service, tools):
        self.llm = llm
        self.memory = memory_service
        self.tools = tools
        
        # 四个通道执行器
        self.complex_engine = ComplexTaskEngine(llm, tools)
        self.planning_engine = PlanningEngine(llm, tools)
        self.react_engine = ReactEngine(llm, tools)
    
    def execute(self, query: str, context: str) -> dict:
        """Q&A 域执行入口"""
        # LLM 路由决策
        decision = self._llm_route(query, context)
        
        if decision["type"] == "simple":
            return self._execute_simple(query, decision.get("tool"))
        elif decision["type"] == "complex":
            return self.complex_engine.execute(query)
        elif decision["type"] == "planning":
            return self.planning_engine.execute(query)
        elif decision["type"] == "open":
            return self.react_engine.execute(query)
        else:
            # 默认走复杂通道（最保险）
            return self.complex_engine.execute(query)
    
    def _llm_route(self, query: str, context: str) -> dict:
        """LLM 路由决策"""
        prompt = self._build_route_prompt(query, context)
        response = self.llm.invoke(prompt)
        return json.loads(response)
    
    def _execute_simple(self, query: str, tool_name: Optional[str]) -> dict:
        """简单通道：直接调工具"""
        if tool_name and tool_name in self.tools:
            return self.tools[tool_name].invoke({"query": query})
        else:
            # 默认调用政策检索
            return self.tools["search_policy"].invoke({"query": query})
```

**状态**: 设计完成，待实现

---

## ⬜ 待开始任务

### 4. ComplexTaskEngine - 复杂通道执行器

**文件**: `src/agents/executors/complex_task_engine.py`

**职责**:
- 复用现有 `TaskDecomposer` 分解查询
- 并行执行子任务（Multi-Agent）
- 合并结果

**依赖**:
- `src/agents/task_decomposer.py` ✅ 已有
- `src/agents/workflow_orchestrator.py` ✅ 已有

**实现思路**:
```python
class ComplexTaskEngine:
    def __init__(self, llm, tools):
        self.decomposer = TaskDecomposer(llm)
        self.orchestrator = WorkflowOrchestrator(llm, tools)
    
    def execute(self, query: str) -> dict:
        # 1. 分解任务
        tasks = self.decomposer.decompose(query)
        
        # 2. 并行执行
        results = self.orchestrator.execute_parallel(tasks)
        
        # 3. 合并结果
        return self._merge_results(results, query)
```

**状态**: 待开始
**预计时间**: 4小时

---

### 5. PlanningEngine - 规划通道执行器

**文件**: `src/agents/executors/planning_engine.py`

**职责**:
- 加载 Planning Skill（`skills/trip_planning_skill.md`）
- 按 Skill 步骤执行（Step 1-7）
- 并行查询政策、天气、酒店
- 生成差旅方案

**Skill 文件**: `skills/trip_planning_skill.md`

**Skill 内容**:
```markdown
# 差旅规划 Skill

当用户要求"安排出差"、"规划行程"、"出差方案"时，按以下步骤执行。

## Step 1: 提取信息
从查询和记忆中获取：
- 目的地: {city}
- 日期: {start_date} - {end_date}
- 天数: {days}
- 职级: {position}（用户画像）
- 预算: {budget}（可选）

## Step 2: 查差旅标准（并行）
1. search_policy(query="{city} 住宿标准")
2. search_policy(query="伙食补助标准")
3. search_policy(query="{city} 交通标准")

## Step 3: 查天气
search_weather(city="{city}", date="{date}")

## Step 4: 推荐酒店
search_hotel(city="{city}")

## Step 5: 查历史偏好
query_memory(query="差旅偏好", user_id="{user_id}")

## Step 6: 算费用
calculate_expense(city="{city}", days="{days}", position="{position}")

## Step 7: 生成方案
【差旅方案】
目的地：{city} | 时间：{date}（{days}天）
住宿：{result} → {cost}元
伙食：{result} → {cost}元
交通：{result} → {cost}元
总计：{total}元
天气提醒：{tips} | 推荐酒店：{hotel}
```

**实现思路**:
```python
class PlanningEngine:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.skill = self._load_skill("skills/trip_planning_skill.md")
    
    def execute(self, query: str) -> dict:
        # 1. 提取信息（Step 1）
        info = self._extract_info(query)
        
        # 2-4. 并行查询（Step 2-4）
        results = self._parallel_query(info)
        
        # 5-6. 查历史和算费用（Step 5-6）
        history = self.tools["query_memory"].invoke({...})
        expense = self._calculate_expense(info, results)
        
        # 7. 生成方案（Step 7）
        return self._generate_plan(info, results, history, expense)
```

**状态**: 待开始
**预计时间**: 6小时

---

### 6. ReactEngine - 开放通道执行器

**文件**: `src/agents/executors/react_engine.py`

**职责**:
- 复用现有 ReAct Agent
- 支持比较/推荐/评价类查询
- 循环推理，最多 5 轮

**依赖**:
- `src/modules/module_3_react_agent/agent.py` ✅ 已有

**实现思路**:
```python
class ReactEngine:
    def __init__(self, llm, tools):
        self.agent = create_react_agent(llm, tools)
    
    def execute(self, query: str) -> dict:
        # 使用现有 ReAct Agent
        result = self.agent.invoke({"input": query})
        return {"answer": result["output"]}
```

**状态**: 待开始
**预计时间**: 2小时

---

### 7. 记忆层接入

**文件**: 
- `src/memory/memory_service.py` (修改)
- `src/memory/working_memory.py` (修改)

**新增 API**:
```python
# MemoryService 新增方法
def build_enhanced_prompt(self, user_id: str, conversation_id: str) -> str:
    """构建增强 Prompt（对话历史 + 用户画像 + 工作记忆）"""
    chat_history = self.chat_memory.get_messages(conversation_id)
    user_profile = self.long_term_memory.get_user_profile(user_id)
    working_ctx = self.working_memory.get_context(user_id)
    return f"用户画像: {user_profile}\n工作记忆: {working_ctx}\n对话历史: {chat_history}"

def query_memory(self, user_id: str, query: str) -> str:
    """查询记忆（用于 query_memory 工具）"""
    return self.long_term_memory.search(user_id, query)

# WorkingMemory 新增方法
def update_approval_status(self, user_id: str, approval_id: str, status: str):
    """更新审批状态（Phase 3 审批域需要）"""
    key = f"approval:{user_id}:{approval_id}"
    self.set(key, {"status": status}, ttl=86400)
```

**状态**: 待开始  
**预计时间**: 4小时

---

### 8. 监控埋点

**文件**: `src/monitoring/prometheus_exporter.py` (修改)

**新增指标**:
```python
unified_requests_total = Counter("unified_requests_total", "Total requests", ["domain", "channel", "status"])
request_duration_seconds = Histogram("request_duration_seconds", "Duration", ["domain", "channel"])
tool_calls_total = Counter("tool_calls_total", "Tool calls", ["tool_name", "success"])
```

**状态**: 待开始 (Phase 4 优先)  
**预计时间**: 3小时

---

### 9-11. 测试与文档

**端到端测试**: `tests/test_phase2_e2e.py` - 5个场景  
**单元测试**: 80%+ 覆盖率  
**文档**: 架构设计、API 使用示例

**状态**: 待开始  
**预计时间**: 9小时

---

## 🎯 Phase 3 预览 - 审批域

**已有基础**: ✅ FeishuClient, ApprovalGraph  
**待实现**: ApprovalEngine, 3个审批工具, 工作记忆集成  
**预计时间**: 2-3天

---

## 🔮 后续优化方案

### 优化 1: 表格数据集成 (Phase 4)

**场景**: 差旅标准表、历史出差表、审批历史表

**推荐方案**: PostgreSQL + Text-to-SQL 混合
```sql
CREATE TABLE travel_standards (
    city VARCHAR(50),
    position_level VARCHAR(20),
    accommodation_limit DECIMAL(10,2)
);
```

**实施时机**: Phase 4

---

### 优化 2: LLM 路由准确率提升

**推荐**: Few-shot 示例  
**实施时机**: Phase 2 测试期间

---

### 优化 3: 城市名 LLM 翻译兜底

**推荐**: 模糊匹配 + LLM 兜底  
**成本**: < ¥0.02/天  
**实施时机**: Phase 2 测试期间

---

### 优化 4: 工具调用失败降级

**推荐**: 多级降级（中文查询 → LLM翻译 → 政策查询）  
**实施时机**: Phase 2 集成测试期间

---

### 优化 5: 审批域表格集成

**Phase 3**: PostgreSQL 表 + 基础查询  
**Phase 4**: Text-to-SQL + 飞书表格集成

---

## 📝 每日进度记录

### 2026-07-11 (Day 1)

**完成**: ✅ 城市翻译工具, ✅ 进度文档  
**进行中**: ⏳ OrchestratorAgent, ⏳ QAEngine  
**明天**: 实现两个 Agent + ComplexTaskEngine

---

## 🎯 里程碑

| 里程碑 | 目标日期 | 状态 |
|--------|---------|------|
| Phase 1: 工具系统 | 2026-07-10 | ✅ |
| Phase 2: Q&A 域 | 2026-07-14 | ⏳ 9% |
| Phase 3: 审批域 | 2026-07-17 | ⬜ |
| Phase 4: 监控完善 | 2026-07-20 | ⬜ |

---

## 📞 决策记录

### ✅ 决策 1: 城市名翻译 (2026-07-11)
- 字典映射 200+ 城市
- 失败时 LLM 翻译

### ✅ 决策 2: 审批域时机 (2026-07-11)
- Phase 3 单独实施

### ⏳ 待决策 1: LLM 路由优化
- Few-shot / 置信度 / 微调模型
- 决策时机: Phase 2 测试期间

### ⏳ 待决策 2: 表格集成方案
- PostgreSQL / Text-to-SQL / Table QA / 飞书表格
- 决策时机: Phase 3 实施前

---

## 📚 参考文档

- [架构规划 v2](./ARCHITECTURE_V2_PLAN.md)
- [Phase 1 交接文档](../交接文档_v2.0.txt)
- [生产任务清单](./PRODUCTION_TASK_LIST.md)

---

**最后更新**: 2026-07-11 by Claude  
**下次更新**: 2026-07-12
