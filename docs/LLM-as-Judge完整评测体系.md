# LLM-as-Judge 完整评测体系

> 本文档总结了差旅管理系统的完整LLM-as-Judge评测体系，包括RAG评测、Agent任务执行、系统路由、用户体验四个层次，以及RAGAS框架的Faithfulness和Answer Relevance核心原理。

---

## 目录

- [一、评测体系架构](#一评测体系架构)
- [二、第一层：RAG检索生成质量](#二第一层rag检索生成质量)
- [三、第二层：Agent任务执行质量](#三第二层agent任务执行质量)
- [四、第三层：系统路由质量](#四第三层系统路由质量)
- [五、第四层：用户体验质量](#五第四层用户体验质量)
- [六、RAGAS核心原理：Faithfulness与Answer Relevance](#六ragas核心原理faithfulness与answer-relevance)
- [七、监控体系架构](#七监控体系架构)
- [八、BadCase回流机制](#八badcase回流机制)
- [九、成本与失效边界](#九成本与失效边界)
- [十、面试话术总结](#十面试话术总结)

---

## 一、评测体系架构

```
┌─────────────────────────────────────────────────────────────┐
│           LLM-as-Judge 全局监控评测体系                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  第一层：RAG检索生成质量（内容层）                            │
│  ├─ Retrieval Relevance（检索相关性）                        │
│  ├─ Groundedness/Faithfulness（忠实度/基础性）               │
│  ├─ Answer Relevance（答案相关性）                           │
│  └─ Correctness（正确性）                                    │
│                                                              │
│  第二层：Agent任务执行质量（行为层）                          │
│  ├─ Task Completion（任务完成度）                            │
│  ├─ Tool Selection（工具选择正确性）                         │
│  ├─ Tool Execution（工具执行成功率）                         │
│  ├─ Reasoning Quality（推理质量）                            │
│  └─ Error Recovery（错误恢复能力）                           │
│                                                              │
│  第三层：系统路由质量（决策层）                               │
│  ├─ Intent Classification（意图识别准确率）                  │
│  ├─ Complexity Assessment（复杂度评估准确率）                │
│  ├─ Channel Routing（通道路由正确性）                        │
│  └─ Fallback Handling（降级策略合理性）                      │
│                                                              │
│  第四层：用户体验质量（体验层）                               │
│  ├─ Response Time（响应速度）                                │
│  ├─ Language Quality（语言流畅性）                           │
│  ├─ Helpfulness（有用性）                                    │
│  └─ Safety（安全性/合规性）                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、第一层：RAG检索生成质量

### 2.1 四大核心指标

| 指标 | 需要的输入 | 衡量对象 | 得分低时的典型含义 | 需要标准答案 | 评估方法 |
|------|-----------|---------|------------------|------------|---------|
| **Retrieval Relevance** | 检索文档 + 问题 | 检索到的文档是否相关 | 检索质量差，返回了无关文档 | ❌ | LLM逐文档判断 |
| **Faithfulness** | 答案 + 上下文 | 答案是否基于文档 | 生成模型编造或使用了上下文外的知识 | ❌ | LLM逐句判断 |
| **Answer Relevance** | 答案 + 问题 | 答案是否切题 | 回答偏离问题、答非所问或冗余 | ❌ | 反向生成问题+向量相似度 |
| **Correctness** | 答案 + 参考答案 | 答案是否正确 | 与标准答案不一致 | ✅ | LLM-as-Judge评分 |

### 2.2 项目实战效果总结

- **Retrieval Relevance**：发现BM25的Top-1相关性0.9，但Top-5平均只有0.6，优化RRF权重后提升到0.75
- **Faithfulness**：用户反馈"答案与政策矛盾"，人工抽查发现15%幻觉，优化Prompt约束后降到3%，通过BadCase回流发现30%是检索不全，进一步降到1.5%
- **Correctness**：第一版True/False评分标准差0.3，改5分制+思维链后降到0.05，与人类一致性从62%→83%

---

## 三、第二层：Agent任务执行质量

### 3.1 五大核心指标

| 指标 | 定义 | 评估方法 | 项目实战效果 |
|------|------|---------|-------------|
| **Task Completion** | Agent是否完成所有子任务 | LLM分析子任务+评分 | 发现20%的复杂查询只完成部分任务 |
| **Tool Selection** | Agent选择的工具是否正确 | LLM判断工具选择合理性 | 发现15%选错工具，根因是ReAct Prompt缺示例 |
| **Tool Execution** | 工具调用是否成功 | 技术指标统计 | 监控API调用成功率 |
| **Reasoning Quality** | ReAct推理链是否合理 | LLM评估逻辑连贯性 | 发现部分推理跳跃，优化Prompt |
| **Error Recovery** | 工具失败时是否恢复 | LLM评估降级策略 | 评估错误处理能力 |

### 3.2 Task Completion评测器示例

```python
def task_completion_evaluator(inputs: dict, outputs: dict) -> dict:
    """评估任务完成度"""
    llm = ChatOpenAI(model="gpt-4")
    
    prompt = f"""
你是任务完成度评估专家。判断Agent是否完成了用户的任务。

用户请求：{inputs['query']}
Agent执行轨迹：
- 调用的工具：{outputs.get('tools_used', [])}
- 最终回答：{outputs['answer']}

评估步骤：
1. 分析用户请求包含哪些子任务
2. 检查Agent是否完成了所有子任务
3. 评估完成的质量

评分标准（0-1分）：
1.0：完全完成，所有子任务都做了且质量高
0.7：基本完成，所有子任务都做了但质量一般
0.5：部分完成，遗漏了部分子任务
0.3：大部分未完成，只完成了少量子任务
0.0：完全未完成

请先分析子任务，然后给出评分。
"""
    
    result = llm.invoke(prompt)
    score = extract_score(result.content, scale=1.0)
    
    return {
        "key": "task_completion",
        "score": score,
        "reasoning": result.content
    }
```

---

## 四、第三层：系统路由质量

### 4.1 三层路由架构对应的评测

| 层级 | 评测指标 | 定义 | 项目场景 |
|------|---------|------|---------|
| **Layer 2** | Intent Classification | 意图识别是否准确（approval/qa/chat） | 评测Self-RAG分类准确率 |
| **Layer 3** | Complexity Assessment | 复杂度评估是否准确（SIMPLE/MEDIUM/COMPLEX） | 评测查询难度判断 |
| **最终** | Channel Routing | 路由到的通道是否合理 | 评测SimpleChannel/ComplexChannel选择 |

### 4.2 诊断示例

```python
用户问："北京明天下雨吗？需要带伞吗？"

【Layer 1：规则快路径】
检测到"天气"关键词 → 调用search_weather

【评测结果】
- Task Completion：0.5（只回答了天气，没回答是否带伞）
- Faithfulness：1.0（天气信息来自API）
- Answer Relevance：0.7（部分回答了问题）

【诊断】
→ 规则快路径只调用了search_weather
→ 没有后续推理（是否带伞）
→ 应该让查询进入ReAct循环

【优化方向】
1. 调整Layer 1规则：多意图查询不走快路径
2. 增加"是否需要后续推理"的判断
```

---

## 五、第四层：用户体验质量

### 5.1 四大指标

| 指标 | 评估方法 | 评分标准 |
|------|---------|---------|
| **Response Time** | 技术指标统计 | <0.5s=1.0, <2s=0.8, <5s=0.5, >5s=0.2 |
| **Language Quality** | LLM评估流畅性、专业性 | 0-1分，评估语言质量 |
| **Helpfulness** | LLM评估是否真正解决问题 | 0-1分，评估实用性 |
| **Safety** | LLM检测敏感信息、违规建议 | 1.0=安全, 0.5=有风险, 0.0=严重违规 |

---

## 六、RAGAS核心原理：Faithfulness与Answer Relevance

### 6.1 为什么需要这两个指标？

**核心问题**：
```
员工问："小规模纳税人转一般纳税人后，纳税人识别号会变吗？"

检索到的文档（正确）：
"转为一般纳税人后，纳税人识别号不变，只是资格认定信息会更新。"

LLM生成的答案（错误）：
"会变，需要重新登记。"

问题：
- 答案语法通顺、语气肯定
- 但与检索到的文档矛盾
- 这是典型的幻觉（Hallucination）
```

**RAGAS的思路**：
- 不需要人工标注标准答案（Reference-free）
- 让评估LLM检查：生成答案的每条陈述，能否从检索到的文档推导出来

---

### 6.2 Faithfulness（忠实度）：逐句回查上下文

#### **核心原理**

```
问题：忠实度回答什么？
→ "答案里的每句话，能不能在检索到的文档里找到依据？"

评分公式：
忠实度 = 有依据的陈述数 / 总陈述数
```

#### **计算流程（两步）**

**第1步：语句拆解**

评估LLM把一段连续答案拆成独立的事实陈述。

**示例**：
```python
原始答案：
"小规模转一般纳税人后，纳税人识别号不变，只是资格认定信息中会增加一般纳税人资格。"

评估LLM拆解后：
1. "纳税人识别号不变"
2. "资格认定信息中增加一般纳税人资格"
```

**第2步：逐条回查上下文**

评估LLM拿每条陈述，判断是否能从检索到的文档推导出来。

```python
检索到的文档：
"转为一般纳税人后，纳税人识别号保持不变。资格认定信息中会新增一般纳税人资格标识。"

陈述1："纳税人识别号不变"
→ Yes（文档明确支持）

陈述2："资格认定信息中增加一般纳税人资格"
→ Yes（文档说"新增资格标识"，语义一致）

忠实度 = 2/2 = 1.0
```

#### **关键设计点**

**1. 为什么"逐条判断"而不是"整体打分"？**

❌ **整体打分的问题**：
- 容易受答案长度影响
- 容易受语言流畅度干扰
- 不可解释（不知道哪句话有问题）

✅ **逐条判断的优势**：
- 判断对象具体
- 可解释（明确指出哪句话没有依据）
- 稳定性高

**2. 语句拆解的粒度问题**

**最佳实践**：
```python
# 按语义单元拆分，每条陈述应该：
# 1. 可独立判断真假
# 2. 不包含复合逻辑（避免"并且"、"但是"连接的多个事实）
# 3. 保留关键上下文（避免代词引用不清）

✅ 好的拆分：
原句："小规模转一般后，识别号不变，但资格信息更新"
拆分：
1. "小规模转一般后，识别号不变"
2. "小规模转一般后，资格信息更新"
```

---

### 6.3 Answer Relevance（答案相关性）：反向生成问题

#### **核心原理**

```
问题：答案相关性回答什么？
→ "这段回答有没有正面回应用户的问题？"

评分公式：
答案相关性 = 平均相似度（反向生成的问题 vs 原始问题）
```

#### **计算流程（两步）**

**第1步：反向生成问题**

评估LLM根据答案，生成n个可能的问题。

**示例**：
```python
原始问题：
"小规模转一般纳税人后，纳税人识别号会变吗？"

生成的答案：
"转为一般纳税人后，纳税人识别号保持不变。"

评估LLM反向生成的问题（n=3）：
1. "纳税人识别号在转为一般纳税人后会改变吗？"
2. "小规模转一般后识别号是否需要重新申请？"
3. "一般纳税人资格变更是否影响识别号？"
```

**第2步：计算向量相似度**

用Embedding模型把这些生成问题转成向量，计算与原始问题的余弦相似度。

```python
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 向量化
original_question_vec = model.encode(original_question)
generated_questions_vec = model.encode(generated_questions)

# 计算余弦相似度并取平均
similarities = [
    np.dot(original_question_vec, gen_vec) / (
        np.linalg.norm(original_question_vec) * np.linalg.norm(gen_vec)
    )
    for gen_vec in generated_questions_vec
]

answer_relevance = np.mean(similarities)
```

#### **设计直觉**

```
好答案 → 反向生成的问题围绕同一主题 → 与原始问题相似度高
差答案 → 反向生成的问题发散 → 与原始问题相似度低
```

#### **为什么用向量相似度而不是LLM直接打分？**

✅ **向量相似度的优势**：
1. 稳定性高：数值计算，不受LLM主观判断波动
2. 成本低：Embedding模型比LLM便宜
3. 可复现：相同输入→相同输出

---

### 6.4 四个指标的完整对比表

| 指标 | 需要的输入 | 衡量对象 | 得分低时的典型含义 | 需要标准答案 | 评估方法 |
|------|-----------|---------|------------------|------------|---------|
| **Faithfulness** | 答案 + 上下文 | 答案是否基于文档 | 生成模型编造或使用了上下文外的知识 | ❌ | LLM逐句判断 |
| **Answer Relevance** | 答案 + 问题 | 答案是否切题 | 回答偏离问题、答非所问或冗余 | ❌ | 反向生成问题+向量相似度 |
| **Context Recall** | 上下文 + 标准答案 | 所需信息是否被找全 | 检索遗漏了关键文档 | ✅ | 检查标准答案的信息是否在上下文中 |
| **Context Precision** | 上下文 + 标准答案 | 相关片段是否排在前面 | 检索排序差，噪声片段挤占前排 | ✅ | 检查相关片段的排序位置 |

---

### 6.5 诊断矩阵

| 指标组合 | 问题定位 | 优化方向 |
|---------|---------|---------|
| **Faithfulness低 + Context Recall高** | 检索找到了正确文档，但生成模型没有好好利用 | 优化生成Prompt：添加"仅基于文档回答"约束、降低temperature |
| **Faithfulness高 + Answer Relevance低** | 模型忠实复述了文档，但没有针对问题组织回答 | 优化生成Prompt：添加"聚焦用户问题"约束、提供少样本示例 |
| **Context Recall低** | 检索遗漏了关键文档 | 优化检索策略：调整Top-K、优化查询改写、增加BM25权重 |
| **Context Precision低** | 检索排序差，噪声文档排在前面 | 优化排序：调整RRF权重、增加Reranker |

---

## 七、监控体系架构

```python
┌─────────────────────────────────────────────────────────────┐
│                 LLM-as-Judge 监控体系                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 实时评测层（Online Evaluation）                          │
│     ├─ 采样策略：10%的线上流量                               │
│     ├─ 评测指标：Relevance + Groundedness + Safety          │
│     ├─ 触发告警：score < 0.7 持续10分钟 → Webhook           │
│     └─ 存储：Prometheus + InfluxDB                          │
│                                                              │
│  2. 离线评测层（Offline Evaluation）                         │
│     ├─ 频率：每次PR提交 / 每周全量评测                      │
│     ├─ 数据集：100+条RAGAS生成 + 真实用户Bad Case           │
│     ├─ 全指标：4层共15个指标全部跑                          │
│     └─ 版本对比：LangSmith Experiment Compare               │
│                                                              │
│  3. BadCase回流层（Feedback Loop）                           │
│     ├─ 低分标记：score < 0.5自动入库                        │
│     ├─ 根因分析：人工分析 + LLM辅助归类                     │
│     ├─ 优化闭环：Prompt优化 → 重新评测 → 验证效果          │
│     └─ 知识沉淀：典型Bad Case → 测试数据集                  │
│                                                              │
│  4. 可视化展示层（Dashboard）                                │
│     ├─ Grafana仪表盘：实时指标趋势                          │
│     ├─ LangSmith UI：评测实验对比                           │
│     ├─ 自定义报告：周报/月报自动生成                        │
│     └─ 告警通知：Webhook → 飞书/钉钉/Slack                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 八、BadCase回流机制

### 8.1 自动标记

```python
# 低分case（score < 0.5）自动入库
if score < 0.5:
    log_badcase(
        query=inputs['query'],
        answer=outputs['answer'],
        context=outputs.get('documents', []),
        tools_used=outputs.get('tools_used', []),
        issue_type=classify_issue_type(score, metric),
        metric_scores={
            "faithfulness": outputs.get('faithfulness'),
            "relevance": outputs.get('relevance'),
            "task_completion": outputs.get('task_completion')
        }
    )
```

### 8.2 根因分类

| Issue Type | 定义 | 触发条件 |
|-----------|------|---------|
| `hallucination` | 幻觉 | Faithfulness < 0.5 |
| `off_topic` | 答非所问 | Answer Relevance < 0.5 |
| `incomplete_task` | 任务未完成 | Task Completion < 0.5 |
| `wrong_tool` | 工具选择错误 | Tool Selection < 0.5 |
| `poor_retrieval` | 检索质量差 | Retrieval Relevance < 0.5 |

### 8.3 优化闭环

```python
# 1. 分析BadCase
badcases = query_badcases(issue_type="hallucination", limit=20)

# 2. 人工分析根因
# - 30%是检索不全导致
# - 70%是生成Prompt缺少约束

# 3. 优化Prompt
improved_prompt = """
基于以下文档回答问题。

重要约束：
- 仅使用文档中的信息回答
- 如果文档中没有，明确说"文档中未提及"
- 不要推测或添加文档外的信息
"""

# 4. 重新评测验证效果
results = evaluate_with_new_prompt(badcases, improved_prompt)
```

---

## 九、成本与失效边界

### 9.1 成本估算

```python
单次全量评测成本（100条测试数据）：

Faithfulness：
- 语句拆解：1次LLM调用（~300 tokens）
- 逐条判断：n次LLM调用（n=陈述数，每次~500 tokens）
- 成本：100 * (300 + 500*5) = 280K tokens = $8.4

Answer Relevance：
- 反向生成问题：1次LLM调用（~400 tokens）
- 向量化：Embedding成本很低
- 成本：100 * 400 = 40K tokens = $1.2

全指标评测（15个指标）：
预估：$50-80/次全量评测（100条数据）
月度成本：<$200（每周1次全量 + 10%实时采样）
```

### 9.2 失效边界

| 失效场景 | 问题表现 | 解决方案 |
|---------|---------|---------|
| **评估LLM能力不足** | 专业术语判断错误 | 使用更强的评估模型（GPT-4 > GPT-3.5） |
| **上下文过长** | 评估LLM遗漏信息 | 限制上下文长度（Top-3而不是Top-10） |
| **上下文包含矛盾** | 难以判断该支持哪个文档 | 文档加时间戳，优先采信新文档 |
| **语言适配问题** | 中文场景生成英文问题 | 使用RAGAS的adapt方法适配中文Prompt |

---

## 十、面试话术总结

### 10.1 完整版（5分钟）

"我为项目建立了**四层LLM-as-Judge评测体系**，覆盖从内容生成到用户体验的全链路质量监控。

### **第一层：RAG检索生成质量（4个指标）**
- Retrieval Relevance：逐文档评分，优化三路召回精确率从0.6到0.75
- Faithfulness：检测幻觉，将幻觉率从15%降到3%
- Answer Relevance：无需参考答案，适合在线评测
- Correctness：5分制+思维链，与人类一致性83%

### **第二层：Agent任务执行质量（5个指标）**
- Task Completion：发现20%的复杂查询只完成了部分任务
- Tool Selection：发现15%的查询选择了错误工具
- Tool Execution、Reasoning Quality、Error Recovery

### **第三层：系统路由质量（3个指标）**
- Intent Classification：评测Layer 2的意图分类
- Complexity Assessment：评测Layer 3的复杂度判断
- Channel Routing：评估通道路由正确性

### **第四层：用户体验质量（4个指标）**
- Response Time、Language Quality、Helpfulness、Safety

### **RAGAS核心原理**
Faithfulness（忠实度）：
- 评估LLM把答案拆成独立陈述
- 逐条判断每个陈述是否能从文档推导
- 幻觉率从15%降到3%

Answer Relevance（答案相关性）：
- 反向生成问题，计算向量相似度
- 稳定性高、成本低、可复现

### **监控体系**
1. 实时监控：10%采样，score<0.7触发告警
2. 离线评测：每次PR全指标，LangSmith版本对比
3. BadCase回流：自动标记→根因分析→Prompt优化→验证
4. 可视化：Grafana + LangSmith

### **量化效果**
- 评测覆盖：100+条数据 + 10%线上采样
- 问题发现：上线前发现80%问题
- 调优效率：从1周缩短到2天
- 成本：月度<$200"

---

### 10.2 精简版（2分钟）

"我们建立了**四层LLM-as-Judge评测体系**：

1. **RAG层**（4指标）：检索相关性、忠实度、答案相关性、正确性
2. **Agent层**（5指标）：任务完成度、工具选择、工具执行、推理质量、错误恢复
3. **路由层**（3指标）：意图识别、复杂度评估、通道路由
4. **体验层**（4指标）：响应速度、语言质量、有用性、安全性

**核心原理**（RAGAS）：
- Faithfulness：逐句回查文档，幻觉率从15%降到3%
- Answer Relevance：反向生成问题，用向量相似度判断切题度

**监控体系**：实时10%采样告警 + 离线全指标对比 + BadCase回流优化

**效果**：上线前发现80%问题，调优效率提升3倍，月成本<$200"

---

## 附录：关键概念速查

| 概念 | 定义 | 为什么重要 |
|------|------|-----------|
| **LLM-as-Judge** | 用LLM评估LLM的输出质量 | 无需人工标注，可规模化评测 |
| **Reference-free** | 不需要人工标注的标准答案 | 降低评测成本，适合快速迭代 |
| **Faithfulness** | 答案是否基于检索文档 | 检测幻觉，防止模型编造 |
| **Answer Relevance** | 答案是否切题 | 防止答非所问、冗余回答 |
| **BadCase回流** | 低分case→根因分析→优化→验证 | 形成闭环，持续改进 |
| **诊断矩阵** | 多指标组合定位问题 | 快速找到根因（检索/生成/路由） |

---

**文档版本**：v1.0  
**最后更新**：2026-09-11  
**适用项目**：LangChain企业差旅管理系统  
**相关文档**：
- [RAG评测体系完全指南](./RAG_EVALUATION_GUIDE.md)
- [项目全面分析报告](./项目全面分析报告.md)
