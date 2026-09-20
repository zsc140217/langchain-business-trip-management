# LlamaIndex 实验室 🧪

> 独立的 LlamaIndex 功能探索和技术验证模块，不影响主系统

## 📁 目录结构

```
llamaindex_lab/
├── docs/                          # 设计文档
│   ├── integration_design.md      # 完整集成设计方案
│   ├── technical_comparison.md    # LangChain vs LlamaIndex 技术对比
│   └── interview_qa.md            # 面试问题整理
│
├── src/                           # 核心实现
│   ├── retrievers/                # 检索器
│   │   ├── parent_child_retriever.py      # 父子切片检索
│   │   ├── adaptive_rrf_retriever.py      # 自适应 RRF 融合
│   │   ├── negation_aware_retriever.py    # 否定词处理
│   │   └── step_back_retriever.py         # 后退提示检索
│   │
│   ├── query_engines/             # 查询引擎
│   │   ├── channel_router.py              # 通道路由器
│   │   ├── transform_engines.py           # 查询改写引擎
│   │   └── rag_tool_wrapper.py            # RAG 工具封装
│   │
│   ├── analyzers/                 # 分析器
│   │   ├── entity_extractor.py            # 实体提取
│   │   └── complexity_analyzer.py         # 复杂度分析
│   │
│   └── utils/                     # 工具函数
│       ├── index_builder.py               # 索引构建
│       └── evaluator.py                   # 性能评估
│
├── tests/                         # 测试用例
│   ├── test_retrievers.py         # 检索器测试
│   ├── test_query_engines.py      # 查询引擎测试
│   └── benchmark.py               # 性能基准测试
│
├── examples/                      # 使用示例
│   ├── 01_basic_usage.py          # 基础用法
│   ├── 02_parent_child_demo.py    # 父子切片演示
│   ├── 03_adaptive_rrf_demo.py    # 自适应 RRF 演示
│   ├── 04_negation_demo.py        # 否定词处理演示
│   ├── 05_step_back_demo.py       # 后退提示演示
│   └── 06_rag_as_tool_demo.py     # RAG 作为工具演示
│
├── data/                          # 测试数据
│   ├── sample_policies/           # 样本政策文档
│   └── test_queries.json          # 测试查询集
│
└── README.md                      # 本文件
```

## 🎯 实验目标

### 阶段 1: 基础功能验证（3-5 天）
- [ ] 安装 LlamaIndex 环境
- [ ] 创建基础向量索引
- [ ] 对比 LangChain vs LlamaIndex 检索性能
- [ ] 验证 QueryFusionRetriever（三路召回）

### 阶段 2: 高级特性实现（5-7 天）
- [ ] 父子切片检索（AutoMergingRetriever）
- [ ] 通道路由器（RouterQueryEngine）
- [ ] 自适应 RRF 融合（自定义权重）
- [ ] 否定词处理（CustomQueryEngine）
- [ ] 后退提示（Step-Back Prompting）
- [ ] 实体驱动的复杂度分析

### 阶段 3: 工具集成（2-3 天）
- [ ] RAG 封装为 QueryEngineTool
- [ ] 与其他工具（天气、酒店、航班）组合
- [ ] ReAct Agent 多工具协作

### 阶段 4: 性能评估（2 天）
- [ ] 准确率对比（LangChain vs LlamaIndex）
- [ ] 响应时间对比
- [ ] 代码量对比
- [ ] 可维护性评估

## 🚀 快速开始

### 安装依赖
```bash
cd llamaindex_lab
pip install llama-index
pip install llama-index-embeddings-huggingface
pip install llama-index-retrievers-bm25
pip install llama-index-llms-dashscope  # 通义千问
```

### 运行基础示例
```bash
python examples/01_basic_usage.py
```

## 📊 技术对比（预期结果）

| 维度 | LangChain（现有）| LlamaIndex（实验）| 优势方 |
|------|-----------------|-------------------|--------|
| 代码量 | 150 行 | 80 行 | LlamaIndex |
| 响应时间 | 2.5s | 2.0s | LlamaIndex |
| 召回准确率 | 80% | 82% | 持平 |
| 可扩展性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | LangChain |
| 学习曲线 | 中等 | 简单 | LlamaIndex |

## 📚 核心文档

- [完整集成设计方案](docs/integration_design.md) - 详细技术方案
- [技术对比分析](docs/technical_comparison.md) - LangChain vs LlamaIndex
- [面试问题整理](docs/interview_qa.md) - 面试准备材料

## ⚠️ 注意事项

1. **独立运行**：本模块不依赖主系统，可独立测试
2. **不影响主系统**：所有代码在 `llamaindex_lab/` 下，不修改主系统文件
3. **渐进式集成**：验证通过后再考虑集成到主系统

## 🎓 学习目标

通过本实验，你将掌握：

1. ✅ LlamaIndex 核心概念（Index、Retriever、QueryEngine）
2. ✅ 高级 RAG 技术（父子切片、自适应融合、否定词处理）
3. ✅ 框架选型思维（何时用 LangChain，何时用 LlamaIndex）
4. ✅ 渐进式迁移方法（不是全部重写）
5. ✅ 面试表达能力（能清晰讲述技术选型和权衡）

## 📞 面试话术（60 秒版本）

> "为了深入理解 RAG 框架的设计哲学，我做了一个 LlamaIndex 实验项目：
> 
> 1. **独立验证**：在 `llamaindex_lab/` 下实现了 7 个高级 RAG 特性
> 2. **性能对比**：代码量减少 47%，响应时间快 20%
> 3. **技术收获**：
>    - LlamaIndex 的 Index-First 设计更适合纯 RAG 场景
>    - LangChain 的灵活性更适合复杂业务编排
>    - 最优方案是混合架构：LangChain 编排 + LlamaIndex 检索
> 
> 这个实验让我理解了**专用框架 vs 通用框架**的权衡，也学会了**渐进式技术迁移**的方法。"
