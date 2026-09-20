# LlamaIndex 集成设计方案 📐

> 详细的技术方案设计，涵盖 7 大高级 RAG 特性

---

## 目录

1. [项目背景](#1-项目背景)
2. [技术方案](#2-技术方案)
3. [架构设计](#3-架构设计)
4. [实施计划](#4-实施计划)
5. [对比测试方案](#5-对比测试方案)
6. [风险评估](#6-风险评估)
7. [面试准备](#7-面试准备)

---

## 1. 项目背景

### 1.1 当前架构回顾

**现有系统**（基于 LangChain）：

```
用户查询
    ↓
OrchestratorAgent（三层路由）
    ├─ Layer 1: 规则快路径（80%）
    ├─ Layer 2: LLM 意图识别（15%）
    └─ Layer 3: QAEngine 四通道（5%）
         ├─ SimpleChannel（单一查询）
         ├─ ComplexChannel（多步推理）
         ├─ PlanningChannel（任务规划）
         └─ OpenChannel（开放问题）
              ↓
         FusionRetriever（三路召回）
              ├─ BM25（稀疏检索）
              ├─ Dense 原始查询（稠密检索）
              └─ Dense 改写查询（改写后检索）
                   ↓
              RRF 融合 + Rerank
                   ↓
         LLM 生成答案
```

**现有优势**：
1. ✅ 功能完整，架构清晰
2. ✅ 三路召回准确率达 80%+
3. ✅ 智能路由降低成本 80%

**可优化点**：
1. 检索模块代码量大（150 行手写逻辑）
2. 缺少父子切片（检索粒度固定）
3. 否定词处理依赖 Prompt 工程
4. Step-Back 后退提示未实现

---

### 1.2 为什么引入 LlamaIndex？

**核心原因**：LlamaIndex 是 **RAG 专用框架**，内置了很多我们手写的功能

| 功能 | LangChain（手写） | LlamaIndex（内置） | 优势 |
|------|------------------|-------------------|------|
| 三路召回 + RRF | 150 行代码 | `QueryFusionRetriever` 10 行 | 代码简洁 |
| 查询改写 | 手动调用 LLM | `num_queries=2` 自动 | 开箱即用 |
| 父子切片 | 未实现 | `AutoMergingRetriever` | 新增能力 |
| 智能路由 | 手写 150 行 | `RouterQueryEngine` 30 行 | 声明式配置 |
| Step-Back | 未实现 | 自定义 `TransformQueryEngine` | 新增能力 |

**学习价值**：
- ✅ 对比两个框架的设计哲学
- ✅ 理解专用框架 vs 通用框架的权衡
- ✅ 掌握渐进式技术迁移方法
- ✅ 面试时展示跨框架学习能力

---

### 1.3 集成目标

**不是完全重写，而是渐进式集成**：

```
Phase 1: 独立实验（当前）
  - 在 llamaindex_lab/ 下验证功能
  - 不影响主系统
  - 对比性能差异

Phase 2: 混合架构（未来可选）
  - LangChain：路由、记忆、工具调用、审批流程
  - LlamaIndex：检索、索引、查询优化
  - 适配器模式封装接口

Phase 3: 性能优化（按需）
  - 根据对比结果决定是否迁移
  - 保留 LangChain 的优势部分
```

---

## 2. 技术方案

### 2.1 父子切片（Parent-Child Chunking）

#### 2.1.1 原理

**核心思想**：解决检索粒度 vs 生成上下文的矛盾

```
原始文档（5000 tokens）
    ↓
【分层切片】
  爷切片（2048 tokens）- 最大上下文
     ↓
  父切片（1024 tokens）- 平衡粒度
     ↓
  子切片（512 tokens）- 精确检索
    ↓
【检索策略】
  ① 用子切片检索（精确匹配）
  ② 如果多个子切片属于同一父切片
  ③ 自动返回父切片内容（上下文完整）
```

**优势**：
- ✅ 检索粒度小（子切片 512）→ 召回精准
- ✅ 生成上下文大（父切片 1024）→ LLM 理解完整

#### 2.1.2 LlamaIndex 实现方案

```python
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.retrievers import AutoMergingRetriever

# 1. 定义层级切片策略
node_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 1024, 512],  # 爷→父→子
    chunk_overlap=50                 # 重叠 50 tokens
)

# 2. 解析文档生成层级节点
nodes = node_parser.get_nodes_from_documents(documents)

# 3. 构建存储上下文
storage_context = StorageContext.from_defaults()
storage_context.docstore.add_documents(nodes)

# 4. 构建索引
index = VectorStoreIndex(
    nodes,
    storage_context=storage_context
)

# 5. 创建自动合并检索器
base_retriever = index.as_retriever(similarity_top_k=10)
retriever = AutoMergingRetriever(
    base_retriever,
    storage_context.docstore,
    simple_ratio_thresh=0.5  # 子切片命中率 > 50% 返回父切片
)

# 6. 使用示例
nodes = retriever.retrieve("北京住宿标准？")
# 内部逻辑：
#   - 检索 10 个子切片（512 tokens）
#   - 发现其中 6 个属于同一父切片
#   - 命中率 60% > 50%，自动返回父切片（1024 tokens）
```

#### 2.1.3 适用场景分析

| 场景类型 | 是否适用父子切片 | 原因 |
|---------|----------------|------|
| 政策文档（长篇） | ✅ **强烈推荐** | 条款间有关联，需完整上下文 |
| 法律合同 | ✅ **推荐** | 语境依赖强 |
| FAQ（短问答） | ❌ 不推荐 | 本身就很短，无需切片 |
| 知识图谱 | ❌ 不推荐 | 用 Cypher 查询更高效 |

**我们项目的适用性**：✅ **非常适合**（差旅政策文档平均 2000+ tokens）

---

### 2.2 根据不同通道不同改写

#### 2.2.1 改写策略矩阵

| 通道 | 改写策略 | 目的 | 示例转换 |
|------|---------|------|---------|
| **Simple** | 不改写 | 速度优先 | "北京住宿标准" → 不变 |
| **Complex** | HyDE 改写 | 生成假设答案提升召回 | "北京住宿标准" → "北京市作为一线城市，差旅住宿标准为每天350元..." |
| **Planning** | 子问题分解 | 拆分为多个独立查询 | "北京3天行程" → ["北京景点推荐", "北京酒店查询", "北京交通方式"] |
| **Open** | 扩展改写 | 增加同义词和关键词 | "如何提升体验" → "差旅体验优化 最佳实践 用户满意度提升方案" |

#### 2.2.2 LlamaIndex 实现方案

**方案概览**：为每个通道创建不同的 `QueryEngine`

```python
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import (
    TransformQueryEngine,
    SubQuestionQueryEngine
)

# === 通道 1: Simple（无改写）===
simple_engine = index.as_query_engine(
    similarity_top_k=5
)

# === 通道 2: Complex（HyDE 改写）===
hyde_transform = HyDEQueryTransform(
    llm=llm,
    include_original=True  # 同时保留原始查询
)
complex_engine = TransformQueryEngine(
    base_query_engine=index.as_query_engine(),
    query_transform=hyde_transform
)

# === 通道 3: Planning（子问题分解）===
planning_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[
        QueryEngineTool(
            query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name="policy_search",
                description="查询差旅政策和标准"
            )
        )
    ],
    llm=llm,
    verbose=True
)

# === 通道 4: Open（自定义扩展改写）===
class ExpandQueryTransform(BaseQueryTransform):
    """扩展查询关键词"""
    def _run(self, query_bundle: QueryBundle) -> QueryBundle:
        prompt = f"""
        原问题：{query_bundle.query_str}
        
        生成扩展查询（增加同义词、相关关键词）：
        - 保留原意
        - 添加 2-3 个同义词
        - 添加相关领域术语
        
        扩展查询：
        """
        expanded = self.llm.complete(prompt)
        return QueryBundle(query_str=expanded)

open_engine = TransformQueryEngine(
    base_query_engine=index.as_query_engine(),
    query_transform=ExpandQueryTransform(llm=llm)
)
```

#### 2.2.3 通道路由器设计

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

# 定义 4 个通道作为工具
tools = [
    QueryEngineTool(
        query_engine=simple_engine,
        metadata=ToolMetadata(
            name="simple",
            description="用于简单的单一事实查询，例如：'北京住宿标准是多少'"
        )
    ),
    QueryEngineTool(
        query_engine=complex_engine,
        metadata=ToolMetadata(
            name="complex",
            description="用于需要对比或多步推理的查询，例如：'北京和上海住宿标准哪个高'"
        )
    ),
    QueryEngineTool(
        query_engine=planning_engine,
        metadata=ToolMetadata(
            name="planning",
            description="用于需要规划和组织的任务，例如：'安排3天北京出差行程'"
        )
    ),
    QueryEngineTool(
        query_engine=open_engine,
        metadata=ToolMetadata(
            name="open",
            description="用于开放式问题和建议类查询，例如：'如何提升差旅体验'"
        )
    )
]

# 创建智能路由器（LLM 根据 description 自动选择）
router = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(llm=llm),
    query_engine_tools=tools,
    verbose=True  # 打印路由决策过程
)

# 使用示例
response = router.query("帮我规划北京3天行程")
# 内部自动选择 planning 通道
```

---

### 2.3 实体提取 + 复杂度分析

#### 2.3.1 实体驱动的路由决策

**核心思想**：根据实体数量和类型决定查询复杂度

```python
class EntityDrivenRouter:
    """基于实体特征的智能路由器"""
    
    def route(self, query: str) -> str:
        # 1. 提取实体
        entities = self.extract_entities(query)
        
        # 2. 计算复杂度分数
        score = self.calculate_complexity_score(entities, query)
        
        # 3. 映射到通道
        return self.score_to_channel(score)
    
    def extract_entities(self, query: str) -> dict:
        """
        用 LLM 提取实体
        
        Returns:
            {
                "city": ["北京"],
                "duration": ["3天"],
                "amount": [],
                "person": ["员工"]
            }
        """
        prompt = f"""
        从查询中提取以下类型的实体：
        - city: 城市名称（北京、上海、广州等）
        - duration: 时长（3天、一周、2个月等）
        - amount: 金额（500元、3000元等）
        - person: 人员（张三、员工、高管、经理等）
        
        查询：{query}
        
        返回 JSON 格式：
        {{
            "city": [],
            "duration": [],
            "amount": [],
            "person": []
        }}
        """
        result = self.llm.complete(prompt)
        return json.loads(result)
    
    def calculate_complexity_score(self, entities: dict, query: str) -> int:
        """
        计算查询复杂度分数（0-100）
        
        评分规则：
        - 实体数量：每个实体 +10 分（上限 40）
        - 对比词：+20 分
        - 规划词：+20 分
        - 否定词：+10 分（处理复杂）
        - 长查询（>30字）：+10 分
        """
        score = 0
        
        # 1. 实体数量（每个 +10 分，上限 40）
        total_entities = sum(len(v) for v in entities.values())
        score += min(total_entities * 10, 40)
        
        # 2. 对比词
        comparison_words = ["哪个", "比较", "对比", "vs", "还是", "更"]
        if any(word in query for word in comparison_words):
            score += 20
        
        # 3. 规划词
        planning_words = ["规划", "安排", "制定", "方案", "计划"]
        if any(word in query for word in planning_words):
            score += 20
        
        # 4. 否定词
        negation_words = ["不", "没有", "不能", "禁止", "不可"]
        if any(word in query for word in negation_words):
            score += 10
        
        # 5. 查询长度
        if len(query) > 30:
            score += 10
        
        return min(score, 100)
    
    def score_to_channel(self, score: int) -> str:
        """分数映射到通道"""
        if score < 30:
            return "simple"
        elif score < 60:
            return "complex"
        elif score < 80:
            return "planning"
        else:
            return "open"
```

#### 2.3.2 复杂度评分示例

| 查询 | 实体 | 特征词 | 分数 | 通道 |
|------|-----|--------|------|------|
| "北京住宿标准" | city:1 | 无 | 10 | simple |
| "北京和上海住宿标准哪个高" | city:2 | 对比 | 40 | complex |
| "安排3天北京行程" | city:1, duration:1 | 规划 | 40 | planning |
| "哪些城市不需要审批" | city:0 | 否定 | 10 | simple |
| "如何提升差旅体验并降低成本" | 无 | 无，长查询 | 10 | simple |

---

### 2.4 自适应 RRF 融合

#### 2.4.1 核心思想

**问题**：静态权重无法适应不同查询特征
- 专业术语查询：BM25 更准（精确匹配）
- 口语化查询：Dense 更准（语义理解）

**解决方案**：根据查询特征动态调整权重

#### 2.4.2 实现方案

```python
class AdaptiveRRFRetriever:
    """自适应 RRF 融合检索器"""
    
    def retrieve(self, query: str) -> List[Node]:
        # 1. 分析查询特征
        features = self.analyze_query(query)
        
        # 2. 动态计算权重
        bm25_weight, dense_weight = self.calculate_weights(features)
        
        # 3. 并行检索
        bm25_nodes = self.bm25_retriever.retrieve(query)
        dense_nodes = self.dense_retriever.retrieve(query)
        
        # 4. 加权 RRF 融合
        return self.weighted_rrf_fusion(
            bm25_nodes, 
            dense_nodes,
            (bm25_weight, dense_weight)
        )
    
    def analyze_query(self, query: str) -> dict:
        """分析查询特征"""
        return {
            "has_professional_terms": self._has_professional_terms(query),
            "is_colloquial": self._is_colloquial(query),
            "has_numbers": bool(re.search(r'\d+', query)),
            "entity_count": len(self.extract_entities(query))
        }
    
    def calculate_weights(self, features: dict) -> tuple:
        """
        计算权重
        
        Returns:
            (bm25_weight, dense_weight)
        """
        # 场景 1: 专业术语 → BM25 权重高
        if features["has_professional_terms"]:
            return (0.7, 0.3)
        
        # 场景 2: 口语化 → Dense 权重高
        elif features["is_colloquial"]:
            return (0.3, 0.7)
        
        # 场景 3: 有数字或多实体 → BM25 权重高
        elif features["has_numbers"] or features["entity_count"] >= 2:
            return (0.6, 0.4)
        
        # 默认均衡
        else:
            return (0.5, 0.5)
    
    def _has_professional_terms(self, query: str) -> bool:
        """检测专业术语"""
        keywords = ["管理办法", "第", "条", "款", "项", "规定", "标准", "制度"]
        return any(kw in query for kw in keywords)
    
    def _is_colloquial(self, query: str) -> bool:
        """检测口语化"""
        patterns = ["怎么办", "咋办", "啥", "行不行", "可以吗", "能不能"]
        return any(p in query for p in patterns)
    
    def weighted_rrf_fusion(
        self,
        bm25_nodes: List[Node],
        dense_nodes: List[Node],
        weights: tuple,
        k: int = 60
    ) -> List[Node]:
        """加权 RRF 融合算法"""
        bm25_weight, dense_weight = weights
        scores = defaultdict(float)
        
        # BM25 贡献
        for rank, node in enumerate(bm25_nodes, start=1):
            scores[node.node_id] += bm25_weight / (k + rank)
        
        # Dense 贡献
        for rank, node in enumerate(dense_nodes, start=1):
            scores[node.node_id] += dense_weight / (k + rank)
        
        # 排序并返回
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        node_dict = {n.node_id: n for n in bm25_nodes + dense_nodes}
        return [node_dict[nid] for nid, _ in sorted_ids]
```

#### 2.4.3 权重策略表

| 查询类型 | 示例 | BM25 | Dense | 依据 |
|---------|------|------|-------|------|
| 专业术语 | "差旅管理办法第3条" | 0.7 | 0.3 | BM25 精确匹配 |
| 口语化 | "去北京住哪儿好" | 0.3 | 0.7 | Dense 语义理解 |
| 有数字 | "北京350元住宿" | 0.6 | 0.4 | BM25 对数字敏感 |
| 多实体 | "北京上海对比" | 0.6 | 0.4 | BM25 实体匹配 |
| 均衡 | "北京住宿标准" | 0.5 | 0.5 | 无明显特征 |

---

### 2.5 否定词处理机制

#### 2.5.1 问题分析

**核心问题**：向量 Embedding 对否定词不敏感

```
查询："哪些城市不需要审批？"
召回："北京需要二级审批"（语义相似但答案相反❌）

查询："员工不能报销什么？"
召回："员工可以报销交通费、住宿费"（遗漏"不能"❌）
```

#### 2.5.2 解决方案

**策略**：检测否定 → 改写查询 → Prompt 标记

```python
class NegationAwareQueryEngine:
    """否定词感知查询引擎"""
    
    NEGATION_WORDS = ["不", "没有", "不能", "不可", "禁止", "除外", "不得", "不许"]
    
    def query(self, query_str: str):
        # 1. 检测否定词
        has_negation = any(word in query_str for word in self.NEGATION_WORDS)
        
        if not has_negation:
            # 正常检索
            return self.base_query_engine.query(query_str)
        
        # 2. 否定词处理流程
        return self._handle_negation(query_str)
    
    def _handle_negation(self, query_str: str):
        # 步骤 1: 改写为肯定句
        positive_query = self._remove_negation(query_str)
        # "哪些城市不需要审批" → "哪些城市需要审批"
        
        # 步骤 2: 双路检索
        positive_nodes = self.retriever.retrieve(positive_query)
        exclusion_nodes = self.retriever.retrieve(f"{positive_query} 排除 例外")
        
        # 步骤 3: 合并节点
        all_nodes = positive_nodes + exclusion_nodes
        context = "\n".join([n.text for n in all_nodes])
        
        # 步骤 4: Prompt 明确标记否定逻辑
        prompt = f"""
        【重要提示】用户问的是否定问句：{query_str}
        
        检索到的信息可能是肯定描述，请理解否定逻辑后回答。
        
        理解规则：
        - 用户问"哪些不需要"，信息说"A需要" → 回答"除了A之外都不需要"
        - 用户问"不能做什么"，信息说"可以做X" → 回答"除了X不能做其他"
        
        检索到的信息：
        {context}
        
        请回答用户的否定问句：{query_str}
        答案：
        """
        
        return self.llm.complete(prompt)
    
    def _remove_negation(self, query: str) -> str:
        """去除否定词"""
        for neg_word in self.NEGATION_WORDS:
            query = query.replace(neg_word, "")
        return query.strip()
```

#### 2.5.3 测试用例

| 否定查询 | 改写后 | 召回信息 | 预期答案 |
|---------|-------|---------|---------|
| "哪些城市不需要审批" | "哪些城市需要审批" | "北京、上海需要审批" | "除北京、上海外都不需要" |
| "员工不能报销什么" | "员工能报销什么" | "可报销交通、住宿" | "除交通住宿外不能报销" |

---

### 2.6 Step-Back 后退提示

#### 2.6.1 原理

**问题**：查询过于具体，直接检索失败

```
查询："北京朝阳区建国门附近的住宿标准？"
检索：失败（文档中只有"北京住宿标准"）❌

解决方案：
查询："北京朝阳区建国门附近的住宿标准？"
    ↓ 后退一步
查询："北京的住宿标准？"
检索：成功（找到"北京350元/天"）✅
    ↓ 结合原问题
回答："朝阳区建国门属于北京，标准350元/天"
```

#### 2.6.2 实现方案

```python
class StepBackQueryEngine:
    """后退提示查询引擎"""
    
    def query(self, query_str: str):
        # 1. 判断是否过于具体
        if not self._is_too_specific(query_str):
            return self.base_query_engine.query(query_str)
        
        # 2. 生成后退查询
        step_back_query = self._generate_step_back(query_str)
        
        # 3. 双路检索
        specific_nodes = self.retriever.retrieve(query_str)
        general_nodes = self.retriever.retrieve(step_back_query)
        
        # 4. 合并去重
        all_nodes = self._merge_unique(specific_nodes, general_nodes)
        
        # 5. 生成答案
        context = "\n".join([n.text for n in all_nodes])
        prompt = f"""
        用户原问题（具体）：{query_str}
        后退问题（宽泛）：{step_back_query}
        
        综合以下信息回答用户的原问题：
        {context}
        
        回答：
        """
        return self.llm.complete(prompt)
    
    def _is_too_specific(self, query: str) -> bool:
        """
        判断是否过于具体
        
        特征：
        - 地区细节（朝阳区、海淀区）
        - 具体品牌（希尔顿、万豪）
        - 详细职级（P7、M3）
        - 查询长度 > 20字
        """
        has_district = any(kw in query for kw in ["区", "县", "镇", "街道"])
        has_brand = re.search(r'(希尔顿|万豪|如家|汉庭|7天)', query)
        has_position = re.search(r'(P\d|M\d|总监|经理)', query)
        is_long = len(query) > 20
        
        return (has_district or has_brand or has_position) and is_long
    
    def _generate_step_back(self, query: str) -> str:
        """用 LLM 生成后退查询"""
        prompt = f"""
        原问题：{query}
        
        请生成一个更宽泛的问题，去除具体细节：
        - 去除地区细节：朝阳区 → 北京
        - 去除品牌名称：希尔顿 → 酒店
        - 去除职级细节：P7 → 员工
        
        宽泛问题：
        """
        return self.llm.complete(prompt).strip()
```

#### 2.6.3 适用场景

| 查询 | 是否需要 | 后退查询 |
|------|---------|---------|
| "北京住宿标准" | ❌ | - |
| "北京朝阳区住宿" | ✅ | "北京住宿" |
| "P7员工北京补贴" | ✅ | "员工北京补贴" |
| "希尔顿酒店报销" | ✅ | "酒店住宿报销" |

---

### 2.7 RAG as Tool 集成

#### 2.7.1 核心思想

**RAG 不是全部，只是工具之一**

```
用户："帮我规划北京3天出差"
    ↓
Agent（ReAct 循环）
    ↓
自动分解任务：
  ① search_weather("北京") → 天气
  ② search_policy("北京住宿标准") → RAG 查询
  ③ search_hotel("北京", budget=350) → 酒店搜索
  ④ search_flight("上海", "北京") → 航班搜索
  ⑤ calculate_expense(days=3) → 费用计算
    ↓
综合所有工具结果 → 生成完整方案
```

#### 2.7.2 LlamaIndex 实现

```python
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool, FunctionTool

# === 1. RAG 封装为 Tool ===
rag_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    name="search_policy",
    description=(
        "查询公司差旅政策和标准，包括："
        "- 住宿标准（按城市和职级）"
        "- 交通标准（高铁/飞机）"
        "- 餐饮补贴"
        "- 审批流程"
    )
)

# === 2. 其他工具定义 ===
def search_weather(city: str, date: str = None) -> str:
    """查询天气（调用和风天气API）"""
    ...

def search_hotel(city: str, date: str, budget: int) -> list:
    """搜索酒店（调用飞猪AI CLI）"""
    ...

def search_flight(from_city: str, to_city: str, date: str) -> list:
    """搜索航班（调用飞猪AI CLI）"""
    ...

def calculate_expense(city: str, days: int, role: str = "员工") -> dict:
    """计算预算"""
    ...

# 转为 FunctionTool
weather_tool = FunctionTool.from_defaults(fn=search_weather)
hotel_tool = FunctionTool.from_defaults(fn=search_hotel)
flight_tool = FunctionTool.from_defaults(fn=search_flight)
expense_tool = FunctionTool.from_defaults(fn=calculate_expense)

# === 3. 创建 ReAct Agent ===
agent = ReActAgent.from_tools(
    tools=[rag_tool, weather_tool, hotel_tool, flight_tool, expense_tool],
    llm=llm,
    verbose=True,
    max_iterations=10
)

# === 4. 使用示例 ===
response = agent.chat("帮我规划北京3天出差，预算3000元")

# Agent 内部推理过程：
# Thought: 需要查询北京的住宿标准
# Action: search_policy("北京住宿标准")
# Observation: 350元/天
# 
# Thought: 需要查询北京天气
# Action: search_weather("北京", "2024-01-10")
# Observation: 晴，15-25℃
# 
# Thought: 需要搜索符合预算的酒店
# Action: search_hotel("北京", "2024-01-10", 350)
# Observation: [如家快捷酒店 280元, 7天连锁 250元, ...]
# 
# ... 自动执行所有子任务
# 
# Final Answer: 您的北京3天出差规划如下...
```

---

## 3. 架构设计

### 3.1 模块划分

```
llamaindex_lab/
├── src/
│   ├── retrievers/                      # 检索器模块
│   │   ├── __init__.py
│   │   ├── parent_child_retriever.py    # 父子切片检索
│   │   ├── adaptive_rrf_retriever.py    # 自适应 RRF 融合
│   │   ├── negation_aware_retriever.py  # 否定词处理检索
│   │   └── step_back_retriever.py       # 后退提示检索
│   │
│   ├── query_engines/                   # 查询引擎模块
│   │   ├── __init__.py
│   │   ├── channel_router.py            # 四通道路由器
│   │   ├── transform_engines.py         # 查询改写引擎集合
│   │   └── rag_tool_wrapper.py          # RAG 工具封装
│   │
│   ├── analyzers/                       # 分析器模块
│   │   ├── __init__.py
│   │   ├── entity_extractor.py          # 实体提取器
│   │   └── complexity_analyzer.py       # 复杂度分析器
│   │
│   └── utils/                           # 工具模块
│       ├── __init__.py
│       ├── index_builder.py             # 索引构建工具
│       └── evaluator.py                 # 性能评估工具
```

### 3.2 接口设计原则

**统一接口规范**（兼容 LangChain）：

```python
from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document

class BaseRetriever(ABC):
    """检索器基类"""
    
    @abstractmethod
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        检索相关文档（LangChain 兼容接口）
        
        Args:
            query: 用户查询
        
        Returns:
            List[Document]: LangChain 格式文档列表
        """
        pass

class BaseQueryEngine(ABC):
    """查询引擎基类"""
    
    @abstractmethod
    def query(self, query_str: str) -> str:
        """
        查询并生成答案
        
        Args:
            query_str: 用户查询
        
        Returns:
            str: 答案文本
        """
        pass
```

### 3.3 数据流设计

```
【用户查询】
    ↓
【前处理】
    ├─ 实体提取（EntityExtractor）
    ├─ 复杂度分析（ComplexityAnalyzer）
    └─ 否定词检测
         ↓
【通道路由】（ChannelRouter）
    ├─ Simple → 无改写
    ├─ Complex → HyDE 改写
    ├─ Planning → 子问题分解
    └─ Open → 扩展改写
         ↓
【检索执行】
    ├─ ParentChildRetriever（父子切片）
    ├─ AdaptiveRRFRetriever（自适应融合）
    └─ StepBackRetriever（后退提示）
         ↓
【后处理】
    ├─ 否定词特殊处理
    └─ 上下文整理
         ↓
【LLM 生成】
    ↓
【返回答案】
```

---

## 4. 实施计划

### Phase 1: 环境搭建（1天）

**Day 1**
- [ ] 安装 LlamaIndex 及依赖
- [ ] 准备测试数据（5-10 个政策文档）
- [ ] 创建基础 VectorStoreIndex
- [ ] 验证基础检索功能

**验收标准**：
- ✅ 能成功创建索引
- ✅ 能检索并返回 Top-5 文档
- ✅ 响应时间 < 3秒

---

### Phase 2: 核心功能实现（7天）

**Day 2-3: 父子切片**
- [ ] 实现 `ParentChildRetriever`
- [ ] 编写单元测试
- [ ] 对比单层 vs 父子召回率

**Day 4-5: 自适应 RRF**
- [ ] 实现 `AdaptiveRRFRetriever`
- [ ] 实现权重计算逻辑
- [ ] 测试不同查询类型的权重

**Day 6: 否定词处理**
- [ ] 实现 `NegationAwareQueryEngine`
- [ ] 编写否定词测试用例（10个）
- [ ] 验证准确率

**Day 7: Step-Back**
- [ ] 实现 `StepBackQueryEngine`
- [ ] 实现过度具体检测
- [ ] 验证后退查询生成

**Day 8: 通道路由**
- [ ] 实现 `ChannelRouter`
- [ ] 集成 4 种改写策略
- [ ] 验证路由准确性

---

### Phase 3: 工具集成（2天）

**Day 9: RAG 工具封装**
- [ ] 实现 `QueryEngineTool` 封装
- [ ] 定义工具元数据
- [ ] 编写工具测试

**Day 10: Agent 协作**
- [ ] 实现 `ReActAgent`
- [ ] 集成 5 个工具
- [ ] 验证任务分解

---

### Phase 4: 测试评估（2天）

**Day 11: 基准测试**
- [ ] 准备 50 个测试查询
- [ ] 运行对比测试
- [ ] 收集指标数据

**Day 12: 文档整理**
- [ ] 生成对比报告
- [ ] 整理面试 Q&A
- [ ] 录制演示视频

---

**总计：12天**

---

## 5. 对比测试方案

### 5.1 测试用例设计（50个查询）

| 类别 | 数量 | 示例查询 |
|------|-----|---------|
| 简单查询 | 10 | "北京住宿标准是多少" |
| 对比查询 | 10 | "北京和上海住宿标准哪个高" |
| 规划查询 | 10 | "安排3天北京出差行程" |
| 否定查询 | 10 | "哪些城市不需要审批" |
| 具体查询 | 10 | "朝阳区建国门住宿标准" |

### 5.2 评估指标

| 指标 | 计算方法 | 目标值 |
|------|---------|--------|
| **召回准确率** | Recall@5（人工标注） | > 80% |
| **响应时间** | 平均查询耗时 | < 3s |
| **代码量** | 核心模块 LOC | 减少 30%+ |
| **路由准确率** | 通道选择正确率 | > 90% |

### 5.3 对比维度

| 维度 | LangChain | LlamaIndex | 评估方法 |
|------|-----------|------------|---------|
| 召回准确率 | 基线 | 新实现 | 人工标注相关性 |
| 响应时间 | 基线 | 新实现 | 50次平均值 |
| 代码量 | 150行 | ?行 | 统计 LOC |
| 可维护性 | 主观评分 | 主观评分 | 5分制 |

---

## 6. 风险评估

### 6.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|-----|------|---------|
| 学习曲线陡峭 | 中 | 低 | 提前阅读文档，运行示例 |
| 性能不达预期 | 低 | 中 | 保留 LangChain 降级方案 |
| 依赖冲突 | 低 | 低 | 独立虚拟环境 |

### 6.2 时间风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|-----|------|---------|
| 实现超时 | 中 | 中 | 按优先级实现 |
| 测试不足 | 中 | 低 | 自动化脚本 |

### 6.3 降级方案

**如果 LlamaIndex 不适合**：
1. 保留现有 LangChain 实现
2. 只借鉴设计思路
3. 手动实现核心特性

**如果时间不够**：
1. 只实现核心功能（父子切片 + 自适应 RRF）
2. 其他作为设计方案

---

## 7. 面试准备

### 7.1 核心亮点（60秒版本）

> "为了深入学习 RAG 技术，我搭建了一个 LlamaIndex 实验项目：
> 
> **背景**：主项目用 LangChain，手写了三路召回，代码 150 行
> 
> **实验内容**：
> 1. 用 LlamaIndex 重新实现检索模块
> 2. 添加 7 个高级特性：父子切片、自适应 RRF、否定词处理等
> 3. 对比两个框架的性能
> 
> **技术收获**：
> - LlamaIndex 代码更简洁（80 行 vs 150 行）
> - 内置 QueryFusionRetriever 自动做 RRF 融合
> - 但 LangChain 在复杂编排上更灵活
> 
> **结论**：最优方案是混合架构 - LangChain 负责编排，LlamaIndex 负责检索
> 
> **价值**：理解了专用框架 vs 通用框架的权衡，学会了渐进式技术迁移"

### 7.2 常见问题 Q&A

见 `interview_qa.md` 文档

---

## 附录

### A. 依赖版本

```
llama-index==0.10.0
llama-index-embeddings-huggingface==0.2.0
llama-index-retrievers-bm25==0.1.0
llama-index-llms-dashscope==0.1.0
```

### B. 参考资料

- [LlamaIndex 官方文档](https://docs.llamaindex.ai/)
- [QueryFusionRetriever](https://docs.llamaindex.ai/en/stable/examples/retrievers/reciprocal_rerank_fusion.html)
- [AutoMergingRetriever](https://docs.llamaindex.ai/en/stable/examples/retrievers/auto_merging_retriever.html)

---

**文档版本**: v1.0  
**最后更新**: 2026-09-20  
**作者**: LlamaIndex Lab Team
