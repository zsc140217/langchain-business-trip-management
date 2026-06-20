# 新会话启动提示词

## 📋 任务背景

我正在进行**Embedding微调项目**，已完成Day 1-4的微调训练和评估。现在需要将微调后的模型集成到RAG系统中，并进行端到端的性能评估。

## 🎯 当前状态

### 已完成
- ✅ BGE-large-zh-v1.5模型微调（102条训练数据）
- ✅ 纯Embedding层评估（20个测试查询）
- ✅ 评估报告：Accuracy@1从55%提升到65%
- ✅ RAG系统综合分析报告（理论推断）

### 待完成
- ⏳ 将微调模型集成到RAG系统（配置4：本地微调+Query重写）
- ⏳ 运行端到端RAG评估（使用现有Eval系统）
- ⏳ 收集真实性能数据并更新报告

## 📚 必读文件（按顺序）

请先阅读以下4个文件理解当前处境：

### 1️⃣ `RAG_EMBEDDING_COMPREHENSIVE_ANALYSIS.md`
**用途**: 了解整体评估方案和核心结论
**关键内容**:
- 4种配置对比（云端API vs 本地微调，有无Query重写）
- 预期性能：配置4（本地微调+重写）最优，预计85%准确率
- 核心问题：Query重写能否弥补embedding不足？

### 2️⃣ `EMBEDDING_EVALUATION_REPORT.md`
**用途**: 了解纯Embedding层的微调效果
**关键内容**:
- 微调后Accuracy@1: 55% → 65% (+18.2%)
- Medium难度（同义词匹配）提升为0%！这是关键问题
- 微调在Easy/Hard级别有显著提升，但Medium级别需要Query重写

### 3️⃣ `../../src/rag/hybrid_retriever.py`
**用途**: 理解RAG系统的Query重写和混合检索架构
**关键内容**:
- `EnterpriseQueryRewriter`: LLM驱动的查询重写（"魔都"→"上海"）
- `EnterpriseHybridRetriever`: 三路召回（BM25 + Dense原始 + Dense改写）
- RRF融合机制

### 4️⃣ `../../tests/evaluation/evaluators.py`
**用途**: 了解现有的RAG评估系统（LLM-as-Judge）
**关键内容**:
- 4个核心指标：Correctness, Relevance, Groundedness, Retrieval Relevance
- `ComprehensiveEvaluator`: 可直接用于端到端RAG评估
- 已有完整的三层评估框架（Code-based + Model-based + Human）

## 🚀 下一步行动

### 优先级P0：集成微调模型到RAG系统

**目标**: 部署配置4（本地微调 + Query重写）

**步骤**:
1. ✅ 微调模型路径已确认：`learning/models/bge-large-zh-travel-finetuned/`
2. 修改 `src/rag/retriever.py`，将embedding模型从云端API切换为本地微调模型
3. 确保 `src/rag/hybrid_retriever.py` 的Query重写功能已启用
4. 写一个测试脚本验证集成成功

**关键代码位置**:
- `src/rag/retriever.py:55` - 当前使用DashScope云端API
- 需要改为加载本地微调模型

### 优先级P1：运行端到端RAG评估

**目标**: 收集配置4的真实性能数据

**步骤**:
1. 使用 `enhanced_test_set.json` 的20个测试查询
2. 对每个查询执行完整RAG流程：Query → Rewrite → Retrieve → Generate
3. 使用 `tests/evaluation/evaluators.py` 的 `ComprehensiveEvaluator` 评估生成的答案
4. 计算4个指标：Correctness, Relevance, Groundedness, Retrieval Relevance
5. 按难度分级统计（Easy/Medium/Hard）

### 优先级P2：更新报告为实测版本

**目标**: 将 `RAG_EMBEDDING_COMPREHENSIVE_ANALYSIS.md` 从理论推断更新为实测数据

**步骤**:
1. 替换所有"预期"为"实测"
2. 更新性能数据（Accuracy@1, 各难度级别准确率）
3. 添加实测的4个LLM-as-Judge指标
4. 更新状态从"⚠️ 待实测验证"改为"✅ 已实测"

## 💬 启动新会话的提示词

```
我正在做Embedding微调项目的RAG系统集成。已完成模型微调（Accuracy@1从55%→65%），现在需要：

1. 将微调后的BGE-large-zh-v1.5模型集成到RAG系统
2. 部署"配置4"：本地微调 + Query重写
3. 运行端到端评估，验证预期的85%准确率

请先阅读以下文件理解背景：
- learning/T2_LLM_Finetuning/embedding_finetune/RAG_EMBEDDING_COMPREHENSIVE_ANALYSIS.md
- learning/T2_LLM_Finetuning/embedding_finetune/EMBEDDING_EVALUATION_REPORT.md
- src/rag/hybrid_retriever.py
- tests/evaluation/evaluators.py

然后帮我从"集成微调模型"开始执行。
```

## 📊 关键数据参考

### 微调模型信息
- **模型**: BGE-large-zh-v1.5（1024维，326M参数）
- **训练数据**: 102条query-doc对（34政策 × 3问题）
- **训练时间**: 3.2分钟
- **模型路径**: `learning/models/bge-large-zh-travel-finetuned/` ✅ 已确认存在

### 测试数据
- **测试集**: `enhanced_test_set.json`（20个查询）
- **难度分布**: Easy 5个, Medium 7个, Hard 5个, Distractor 3个
- **文档库**: 29个差旅政策文档片段

### 预期性能（配置4）
- Accuracy@1: ~85%
- Easy级别: ~85%
- Medium级别: ~80%（Query重写解决同义词）
- Hard级别: ~70%

### 现有Eval系统
- **位置**: `tests/evaluation/`
- **核心评估器**: `ComprehensiveEvaluator`（4指标LLM-as-Judge）
- **运行命令**: `python tests/evaluation/run_comprehensive_eval.py`

## ⚠️ 注意事项

1. **成本控制**: LLM-as-Judge评估会调用LLM API，20个查询 × 4指标 = 80次LLM调用，预计成本~5-10元
2. **虚拟环境**: 微调模型在 `venv_embedding_finetune` 环境中，RAG系统可能在其他环境
3. **模型路径**: 确认微调模型文件完整性（应该有 `config.json`, `model.safetensors`, `tokenizer.json` 等）
4. **Query重写**: 需要LLM支持，确保 `DASHSCOPE_API_KEY` 或其他LLM API配置正确

## 🔗 相关文件路径

```
项目根目录: E:\Desktop\langchain-business-trip-management\

关键文件:
├── learning/T2_LLM_Finetuning/embedding_finetune/
│   ├── RAG_EMBEDDING_COMPREHENSIVE_ANALYSIS.md  ← 综合分析报告
│   ├── EMBEDDING_EVALUATION_REPORT.md           ← 纯Embedding评估
│   ├── enhanced_test_set.json                   ← 测试数据
│   └── models/bge-large-zh-travel-finetuned/    ← 微调模型
├── src/rag/
│   ├── retriever.py                             ← 需要修改的文件
│   └── hybrid_retriever.py                      ← Query重写实现
└── tests/evaluation/
    ├── evaluators.py                            ← LLM-as-Judge评估器
    └── run_comprehensive_eval.py                ← 评估主程序
```

## 🎯 成功标准

集成和评估成功的标志：

- [ ] 微调模型成功加载，无报错
- [ ] Query重写功能正常工作（"魔都"→"上海"）
- [ ] 混合检索三路召回都有结果
- [ ] 端到端RAG评估完成，收集到真实数据
- [ ] Accuracy@1达到80%+（目标85%）
- [ ] Medium难度准确率显著提升（目标80%）
- [ ] 报告更新为实测版本

---

**最后更新**: 2026-06-14  
**下次会话**: 从"集成微调模型到RAG系统"开始
