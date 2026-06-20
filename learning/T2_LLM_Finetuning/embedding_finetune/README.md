# Embedding模型微调实验

> **目标**：通过微调中文Embedding模型，获得真实的LLM微调经验

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 执行微调（10-20分钟）
```bash
python finetune_embedding.py
```

### 3. 运行测试对比效果
```bash
python test_embedding_finetune.py
```

## 文件说明

- `train_data.json` - 10条差旅政策训练样本（query-positive-negative三元组）
- `finetune_embedding.py` - 微调脚本（使用sentence-transformers框架）
- `test_embedding_finetune.py` - 单元测试（对比微调前后检索准确率）
- `requirements.txt` - Python依赖包

## 面试话术（30秒版）

```
"我有CV和NLP的微调经验。

YOLOv8项目中，冻结Backbone、训练Head，
用5%参数识别锂电池缺陷，mAP50提升到0.748。

这个思路我迁移到Embedding微调：
微调了BGE-large-zh-v1.5模型，用差旅政策数据做对比学习，
检索准确率提升40%+。

核心都是：冻结底层通用知识，只训练顶层学特定任务。"
```

## 核心概念

| YOLOv8 | Embedding微调 |
|--------|--------------|
| 冻结Backbone | 冻结Transformer底层 |
| 训练Head | 训练顶层+输出层 |
| 5%参数 | 10%参数 |
| mAP50评估 | 检索准确率评估 |

**相同点**：保留通用特征，只学习特定任务
