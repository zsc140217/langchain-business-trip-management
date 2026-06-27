# 模块6：高级RAG - 详细实施计划

> 完成时间：2026-06-27  
> 估计工时：30小时（约4天）  
> 优先级：P2（优化型功能）

---

## 📊 现有架构分析

**已实现组件**：
- ✅ `src/rag/retriever.py` - FAISS向量检索（支持cloud和local_finetuned embedding）
- ✅ `src/rag/hybrid_retriever.py` - 三路召回（BM25 + Dense原始 + Dense改写）+ RRF融合
- ✅ `src/rag/chain.py` - RAG链（RetrievalQA和LCEL两种方式）
- ✅ `src/rag/loader.py` - 文档加载与切分
- ✅ 微调Embedding模型（bge-large-zh-travel-finetuned）

**技术栈**：
- 向量数据库：FAISS
- Embedding：DashScope API / 微调BGE模型
- 关键词检索：BM25 + jieba分词
- 融合算法：加权RRF（Reciprocal Rank Fusion）

---

## 🎯 模块6任务清单

### T6.1 Self-RAG（自适应检索）⭐ P0
- 时间：6小时
- 依赖：无
- 产出：`src/rag/self_rag.py`, `src/rag/query_classifier.py`

### T6.2 GraphRAG（知识图谱）🟡 P1
- 时间：14小时（约2天）
- 依赖：Neo4j Docker环境
- 产出：`src/rag/graph_*.py`

### T6.3 Fusion Retrieval（融合检索）⭐ P0
- 时间：5小时
- 依赖：T6.2（可选图谱部分）
- 产出：`src/rag/fusion_retriever.py`

### T6.4 评估对比⭐ P0
- 时间：5小时
- 依赖：T6.1, T6.3
- 产出：`tests/evaluation/rag_comparison.py`

---

## 📋 T6.1 Self-RAG（自适应检索）

### 技术方案

**核心思想**：LLM判断查询类型，动态决策是否需要检索
- **闲聊/通用知识**：直接回复（节省成本）
- **事实性查询**：触发RAG检索（保证准确性）

**判断标准**：
```
需要检索：
- 政策查询（"报销标准"、"差旅规定"）
- 具体数值（"多少钱"、"几天"）
- 地点相关（"北京"、"上海"）
- 流程问题（"如何申请"、"怎么审批"）

不需要检索：
- 问候语（"你好"、"谢谢"）
- 通用知识（"今天星期几"）
- 系统功能（"你能做什么"）
```

### 实施步骤

**Step 1: 创建查询分类器（2小时）**

文件：`src/rag/query_classifier.py`

```python
class QueryClassifier:
    """
    查询分类器
    基于LLM + Few-shot判断是否需要检索
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.few_shot_examples = """
示例1:
输入: "你好"
分类: CHITCHAT
原因: 普通问候

示例2:
输入: "去上海出差住宿能报多少钱"
分类: FACTUAL
原因: 涉及具体政策和数值

示例3:
输入: "今天天气怎么样"
分类: CHITCHAT
原因: 通用知识，不涉及企业政策
        """
    
    def classify(self, query: str) -> dict:
        """
        分类查询
        Returns:
            {
                "type": "FACTUAL" | "CHITCHAT",
                "confidence": 0.0-1.0,
                "reason": "原因说明"
            }
        """
```

**Step 2: 实现Self-RAG主流程（3小时）**

文件：`src/rag/self_rag.py`

```python
class SelfRAG:
    """
    Self-RAG检索器
    根据查询类型动态决策是否检索
    """
    
    def answer(self, query: str) -> dict:
        """
        智能回答
        
        流程:
        1. 查询分类
        2. 如果是闲聊，直接回复
        3. 如果是事实性，执行RAG检索
        
        Returns:
            {
                "answer": "回答内容",
                "retrieved": True/False,
                "sources": [...] or None,
                "classification": {...}
            }
        """
```

**Step 3: 编写测试用例（1小时）**

文件：`tests/test_self_rag.py`

### 产出文件
- `src/rag/query_classifier.py` (~150行)
- `src/rag/self_rag.py` (~200行)
- `tests/test_self_rag.py` (~100行)

### 时间估算
**总计：6小时**

---

## 📋 T6.2 GraphRAG（知识图谱检索）

### 技术方案

**核心思想**：构建企业差旅政策知识图谱，支持多跳推理

**图谱结构**：
```
节点类型：
- City（城市）: 北京、上海、杭州
- Policy（政策）: 住宿标准、交通标准
- Amount（金额）: 500元、400元
- Category（分类）: 一线城市、二线城市

关系类型：
- BELONGS_TO: 北京 -[BELONGS_TO]-> 一线城市
- HAS_STANDARD: 一线城市 -[HAS_STANDARD{type:"住宿"}]-> 500元
- RELATED_TO: 住宿标准 -[RELATED_TO]-> 交通标准
```

**多跳推理示例**：
```
查询："北京出差住宿能报多少"
推理路径：
北京 -[BELONGS_TO]-> 一线城市 -[HAS_STANDARD{type:"住宿"}]-> 500元/晚
```

### 实施步骤

**Step 1: 搭建Neo4j环境（2小时）**

更新 `docker-compose.yml`：

```yaml
  neo4j:
    image: neo4j:5.15-community
    container_name: travel-agent-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/password123
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "neo4j", "status"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  neo4j_data:
```

**Step 2: 实体关系提取（4小时）**

文件：`src/rag/graph_extractor.py`

```python
class GraphExtractor:
    """
    从文档中提取实体和关系
    使用LLM进行信息抽取
    """
    
    def extract_entities(self, document: str) -> List[Entity]:
        """提取实体（城市、金额、政策名称、分类）"""
        
    def extract_relations(self, document: str, entities: List[Entity]) -> List[Relation]:
        """提取关系（BELONGS_TO、HAS_STANDARD等）"""
```

**Step 3: 图谱构建（3小时）**

文件：`src/rag/graph_builder.py`

```python
class GraphBuilder:
    """将提取的实体和关系写入Neo4j"""
    
    def build_graph(self, entities: List[Entity], relations: List[Relation]):
        """
        构建图谱
        1. 创建节点（MERGE避免重复）
        2. 创建关系
        3. 创建索引（加速查询）
        """
```

**Step 4: 图谱检索（4小时）**

文件：`src/rag/graph_retriever.py`

```python
class GraphRetriever:
    """
    基于Neo4j的图谱检索
    支持单跳和多跳查询
    """
    
    def retrieve(self, query: str, max_hops: int = 2) -> List[dict]:
        """
        图谱检索
        1. 实体识别
        2. 图谱匹配（Cypher查询）
        3. 路径遍历（多跳推理）
        """
```

**Step 5: 图谱可视化（可选，1小时）**

文件：`scripts/visualize_graph.py`

### 产出文件
- `src/rag/graph_extractor.py` (~200行)
- `src/rag/graph_builder.py` (~150行)
- `src/rag/graph_retriever.py` (~250行)
- `tests/test_graph_rag.py` (~150行)
- `scripts/build_graph.py` (~100行)
- `scripts/visualize_graph.py` (~80行)

### 依赖安装
```bash
pip install neo4j py2neo pyvis
```

### 时间估算
**总计：14小时（约2天）**

---

## 📋 T6.3 Fusion Retrieval（融合检索）

### 技术方案

**核心思想**：整合三种检索方式，通过RRF算法融合结果

**三路检索**：
1. **向量检索**：FAISS + 微调Embedding（已有）
2. **关键词检索**：BM25 + jieba分词（已有）
3. **图谱检索**：Neo4j多跳推理（T6.2新增）

**融合算法**：加权RRF
```
score(doc) = w1/(k+rank_vector) + w2/(k+rank_bm25) + w3/(k+rank_graph)

参数：
- k=60（平滑因子）
- w1=1.0（向量权重）
- w2=1.0（BM25权重）
- w3=0.8（图谱权重）
```

### 实施步骤

**Step 1: 扩展现有混合检索器（3小时）**

文件：`src/rag/fusion_retriever.py`

```python
class FusionRetriever:
    """
    融合检索器
    整合向量、BM25、图谱三路检索
    """
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """
        三路召回 + RRF融合
        1. 查询改写（可选）
        2. 三路并行检索
        3. RRF融合
        4. 返回Top-K
        """
```

**Step 2: 集成测试（2小时）**

文件：`tests/test_fusion_retriever.py`

### 产出文件
- `src/rag/fusion_retriever.py` (~300行)
- `tests/test_fusion_retriever.py` (~150行)

### 时间估算
**总计：5小时**

---

## 📋 T6.4 评估对比

### 技术方案

**评估维度**：
1. **准确率**：Top-K召回准确率（Recall@K）
2. **响应延迟**：P50/P95/P99延迟
3. **成本**：API调用成本
4. **覆盖率**：能回答的查询类型占比

**对比方案**：
- 方案1：仅向量检索
- 方案2：向量 + BM25（现有hybrid_retriever）
- 方案3：向量 + BM25 + 图谱（fusion_retriever）
- 方案4：Self-RAG + 融合检索

### 实施步骤

**Step 1: 准备测试数据集（3小时）**

文件：`tests/evaluation/rag_test_dataset.py`

包含20条测试查询：
- Easy: 8条（简单查询）
- Medium: 8条（需要推理）
- Hard: 4条（多跳推理）

类型分布：
- factual（事实性）
- comparison（对比）
- calculation（计算）
- chitchat（闲聊）
- negation（否定）

**Step 2: 实现评估框架（4小时）**

文件：`tests/evaluation/rag_evaluator.py`

```python
class RAGEvaluator:
    """
    RAG评估器
    支持多种检索策略对比
    """
    
    def evaluate(self, retriever, strategy_name: str) -> Dict:
        """
        评估单个检索策略
        返回：Recall@K、延迟、成本等指标
        """
    
    def compare_strategies(self, strategies: List[Tuple]) -> pd.DataFrame:
        """对比多个策略"""
```

**Step 3: 生成评估报告（2小时）**

文件：`tests/evaluation/rag_comparison.py`

```python
def generate_report():
    """
    生成HTML评估报告
    包含：
    - 总体性能对比表
    - 按难度分级对比
    - 按查询类型对比
    - 延迟分布图
    - 成本对比图
    """
```

### 产出文件
- `tests/evaluation/rag_test_dataset.py` (~150行)
- `tests/evaluation/rag_evaluator.py` (~300行)
- `tests/evaluation/rag_comparison.py` (~200行)
- `tests/evaluation/rag_comparison_report.html`

### 时间估算
**总计：9小时**

---

## 📅 实施时间线

### Day 1（8小时）
- ✅ 规划完成（已完成）
- [ ] T6.1 Self-RAG（6小时）
- [ ] 代码审查（1小时）
- [ ] 提交代码（1小时）

### Day 2（8小时）
- [ ] T6.2 GraphRAG - Step 1-3（9小时）
  - Neo4j环境搭建（2小时）
  - 实体关系提取（4小时）
  - 图谱构建（3小时）

### Day 3（8小时）
- [ ] T6.2 GraphRAG - Step 4-5（5小时）
  - 图谱检索（4小时）
  - 可视化（1小时）
- [ ] T6.3 Fusion Retrieval（3小时）

### Day 4（6小时）
- [ ] T6.3 Fusion Retrieval完成（2小时）
- [ ] T6.4 评估对比（4小时）

**总计：30小时（约4天）**

---

## ⚠️ 关键风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Neo4j环境搭建失败 | GraphRAG无法实现 | 降级为文件存储的简化图谱 |
| 实体提取准确率低 | 图谱质量差 | 人工标注核心实体，Few-shot优化 |
| 图谱检索性能差 | 延迟过高 | 限制max_hops，添加缓存层 |
| 评估数据集质量不足 | 评估结果不可信 | 参考MODULE1的评估数据，扩充难度 |

---

## 🎯 成功标准

### T6.1 Self-RAG
- ✅ 闲聊查询准确分类（准确率>95%）
- ✅ 事实性查询触发检索（召回率>90%）
- ✅ 测试覆盖率>80%

### T6.2 GraphRAG
- ✅ Neo4j容器成功运行
- ✅ 提取20+实体，30+关系
- ✅ 单跳查询延迟<500ms
- ✅ 多跳查询延迟<1000ms

### T6.3 Fusion Retrieval
- ✅ 三路检索成功整合
- ✅ RRF融合正确实现
- ✅ 测试覆盖率>80%

### T6.4 评估对比
- ✅ 生成完整HTML报告
- ✅ 对比4种策略
- ✅ 包含20条测试查询
- ✅ 统计Recall@1/3/5、延迟、成本

---

## 📚 参考资料

### 论文
1. **Self-RAG**: "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (2023)
2. **GraphRAG**: "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" (2024)
3. **Fusion Retrieval**: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (2009)

### 开源实现
- LangChain Self-RAG: https://python.langchain.com/docs/how_to/self_query/
- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- LangChain Graph Databases: https://python.langchain.com/docs/integrations/graph_databases/neo4j/

### 博客文章
- "Advanced RAG Techniques: An Illustrated Overview" (LlamaIndex)
- "GraphRAG: Unlocking LLM discovery on narrative private data" (Microsoft Research)

---

## 📝 学习产出

每完成一个任务，产出：
1. **代码实现**：完整可运行的代码
2. **技术笔记**：原理 + 实现 + 坑
3. **面试话术**：30秒电梯演讲 + 2分钟深入版
4. **复习清单**：口头问答题（10-15道）

---

**准备好开始了吗？从T6.1 Self-RAG开始！**
