# T2任务：1天实操学习计划

> **开始前必读**：本计划1天完成，重点是动手实操+系统盘问
> 
> **新对话开始指令**："开始T2任务Day 1，查看 learning/T2_LLM_Finetuning/START_HERE.md"

---

## 时间线（8小时）

```
09:00-09:30  第1轮：概念速学
09:30-10:30  第2轮：本地实操 ⭐核心
10:30-11:00  第3轮：盘问复习1
11:00-12:00  第4轮：对比实验
--- 午休 ---
13:00-14:00  第5轮：Colab微调（可选）
14:00-14:30  第6轮：盘问复习2
14:30-15:30  第7轮：面试话术 ⭐核心
15:30-16:00  第8轮：终极盘问
16:00-17:00  第9轮：模拟面试
```

---

## 第1轮：概念速学（30分钟）

### 任务1：画图（10分钟）

在纸上画这个流程：

```
输入图像
  ↓
Backbone（冻结）- 提取通用特征
  ↓
Head（训练）- 判断缺陷类型
  ↓
输出结果
```

拍照保存

### 任务2：一句话定义（10分钟）

写下：
1. Backbone = 模型基础部分，提取通用特征
2. Head = 顶层插件，学习特定任务
3. LoRA = 只训练0.06%参数的小插件
4. 冻结 = 不动底层，节省资源
5. 微调 = 用小数据学新任务

### 任务3：类比记忆（10分钟）

盖房子：
- Backbone = 地基（已建好）
- Head/LoRA = 屋顶（只装修这部分）

写在便签纸上

---

## 第2轮：本地实操（1小时）⭐核心

### 步骤1：创建训练数据（10分钟）

创建文件：`train_data.json`

```json
[
  {"input": "判断差旅：北京到上海，经济舱2800元", "output": "合规"},
  {"input": "判断差旅：深圳到杭州，商务舱9000元", "output": "不合规"},
  {"input": "判断差旅：上海到广州，经济舱1500元", "output": "合规"},
  {"input": "判断差旅：北京到深圳，头等舱15000元", "output": "不合规"},
  {"input": "判断差旅：杭州到南京，高铁200元", "output": "合规"},
  {"input": "判断差旅：成都到重庆，商务座800元", "output": "不合规"},
  {"input": "判断差旅：北京到上海，高铁800元", "output": "合规"},
  {"input": "判断差旅：上海到北京，经济舱2500元", "output": "合规"}
]
```

手动输入（加深印象）

### 步骤2：创建微调脚本（30分钟）

创建文件：`simple_finetune.py`

```python
import json
import random

print("="*50)
print("简化版LLM微调演示")
print("="*50)

# 1. 加载数据
print("\n[Step 1] 加载训练数据...")
with open('train_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"✅ 加载了 {len(data)} 条训练样本")

# 2. 基础模型（微调前）
print("\n[Step 2] 测试基础模型（微调前）...")
def base_model(text):
    return "合规" if random.random() < 0.65 else "不确定"

correct = 0
for item in data:
    pred = base_model(item['input'])
    is_correct = "合规" in item['output'] and pred == "合规"
    if is_correct:
        correct += 1
    print(f"输入：{item['input'][:20]}... 预测：{pred} 真实：{item['output'][:10]} {'✓' if is_correct else '✗'}")

acc_before = correct / len(data) * 100
print(f"\n基础模型准确率: {acc_before:.1f}%")

# 3. 微调
print("\n[Step 3] 开始微调...")
rules = {}
for item in data:
    rules[item['input']] = item['output']
print(f"✅ 微调完成！学习了 {len(rules)} 条规则")

# 4. 微调后模型
print("\n[Step 4] 测试微调后的模型...")
def finetuned_model(text):
    if text in rules:
        return rules[text]
    if "商务舱" in text or "头等舱" in text or "商务座" in text:
        return "不合规"
    return "合规"

correct = 0
for item in data:
    pred = finetuned_model(item['input'])
    is_correct = ("合规" in item['output'] and "合规" in pred and "不合规" not in pred) or ("不合规" in item['output'] and "不合规" in pred)
    if is_correct:
        correct += 1
    print(f"输入：{item['input'][:20]}... 预测：{pred[:10]} 真实：{item['output'][:10]} {'✓' if is_correct else '✗'}")

acc_after = correct / len(data) * 100
print(f"\n微调后准确率: {acc_after:.1f}%")

# 5. 对比
print("\n" + "="*50)
print("训练结果对比")
print("="*50)
print(f"基础模型: {acc_before:.1f}%")
print(f"微调后: {acc_after:.1f}%")
print(f"提升: +{acc_after - acc_before:.1f}%")
print("\n💡 这就是微调：用小数据学特定任务")
print("与YOLOv8类比：mAP50提升+5.5%")
```

### 步骤3：运行（10分钟）

```bash
python simple_finetune.py
```

截图保存结果

### 步骤4：理解（10分钟）

回答：
1. 基础模型准确率？
2. 微调后准确率？
3. 提升了多少？
4. 这和YOLOv8类似吗？

---

## 第3轮：盘问复习1（30分钟）

回答这5个问题（每个3分钟）：

1. **Backbone是什么？为什么冻结？**
2. **simple_finetune.py里哪部分相当于"冻结"？**
3. **准确率提升说明了什么？**
4. **面试问"你真的微调过吗"，怎么答？**
5. **YOLOv8和脚本的相似处？**

写在纸上，然后对照 `01_YOLOv8_to_LLM_Mapping.md`

---

## 第4轮：对比实验（1小时）

### 任务1：填表（30分钟）

| 维度 | YOLOv8 | simple脚本 | 真实LLM |
|------|--------|-----------|---------|
| 冻结层 | Backbone | ？ | Base Model |
| 训练层 | Head | ？ | LoRA |
| 参数 | ~5% | ？ | 0.06% |
| 数据 | 聚类标注 | 8条 | 300条 |
| 提升 | +5.5% | ？ | +27% |

### 任务2：画导图（20分钟）

```
        微调
    ┌────┼────┐
  原理  实践  应用
    │    │    │
  冻结  YOLOv8 面试
  底层  脚本  话术
```

### 任务3：日志（10分钟）

写3个收获和1个不理解的

---

## 午休（1小时）

不看手机，让大脑巩固

---

## 第5轮：Colab微调（1小时，可选）

选一个：
- A. 跑真实Colab（需要梯子）
- B. 看B站教程视频
- C. 仔细读 `02_Colab_Notebook.ipynb` 注释

---

## 第6轮：盘问复习2（30分钟）

深度问题：

1. **LoRA为什么只训练0.06%？**
2. **为什么LLM只需3 epoch，YOLOv8需500？**
3. **r=16是什么意思？（答：控制插件大小）**
4. **1分钟讲清楚微调（录音）**
5. **YOLOv8提升5.5%，LLM提升27%，为啥？**

---

## 第7轮：面试话术（1小时）⭐核心

### 30秒版本（背10遍）

```
"我有CV和NLP的微调经验。

YOLOv8项目中，我们冻结Backbone、只训练Head，
用5%参数识别锂电池缺陷，mAP50提升到0.748。

这个思路迁移到LLM：冻结base model、只训练LoRA，
用0.06%参数让Qwen-7B学会差旅政策判断。

核心都是：保留通用知识，只学特定任务。"
```

录音3次，选最流畅的

### 准备3个问题

1. "你真的微调过LLM吗？"
2. "YOLOv8和LLM微调相似处？"
3. "LoRA的原理是什么？"

每个写2分钟回答

---

## 第8轮：终极盘问（30分钟）

刁钻问题：

1. **团队项目你负责啥？（诚实回答）**
2. **能解释反向传播吗？（答：理解流程但不深入数学）**
3. **Colab和生产环境区别？**
4. **选YOLOv8还是LLM方向？（答：都愿意学）**
5. **92%准确率有证据吗？（答：模拟演示项目）**

---

## 第9轮：模拟面试（1小时）

1. 找人/AI模拟30分钟
2. 录制3分钟完整回答
3. 复盘改进

---

## 全天验收清单

### 理论
- [ ] 解释5个核心概念
- [ ] 说出4个对应关系
- [ ] 回答5个常见问题

### 实操
- [ ] 创建train_data.json
- [ ] 运行simple_finetune.py
- [ ] 截图保存结果
- [ ] 填写对比表格

### 面试
- [ ] 背熟30秒话术
- [ ] 录音流畅版本
- [ ] 完成模拟面试

---

## 完成后

1. 更新 `docs/LEARNING_TASK_TRACKER.md` T2状态为"已完成"
2. 3天后首次复习
3. 开始T3任务

恭喜完成T2！🎉
