"""
BGE-large-zh-v1.5 微调训练脚本
使用 Sentence-Transformers + MultipleNegativesRankingLoss
"""

import json
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from sentence_transformers.evaluation import InformationRetrievalEvaluator
import torch
from datetime import datetime

print("=" * 60)
print("BGE-large-zh-v1.5 Embedding 微调训练")
print("=" * 60)

# 1. 加载基础模型
print("\n[1/6] 加载基础模型...")
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
print(f"模型维度: {model.get_sentence_embedding_dimension()}")
print(f"设备: {model.device}")

# 2. 加载训练数据
print("\n[2/6] 加载训练数据...")
with open('data_preparation/training_data_final.json', 'r', encoding='utf-8') as f:
    training_data = json.load(f)

print(f"训练样本数: {len(training_data)}")

# 3. 转换为 InputExample 格式
print("\n[3/6] 准备训练样本...")
train_examples = []

for item in training_data:
    query = item['query']
    positive = item['positive']

    # 为BGE模型添加查询指令前缀（官方推荐）
    query_with_instruction = f"为这个句子生成表示以用于检索相关文章：{query}"

    # 创建 InputExample (query, positive)
    train_examples.append(InputExample(texts=[query_with_instruction, positive]))

print(f"生成训练样本: {len(train_examples)} 对")

# 4. 创建 DataLoader
print("\n[4/6] 创建数据加载器...")
batch_size = 16
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
print(f"Batch size: {batch_size}")
print(f"Batches per epoch: {len(train_dataloader)}")

# 5. 配置损失函数和训练参数
print("\n[5/6] 配置训练...")
train_loss = losses.MultipleNegativesRankingLoss(model=model)
print(f"损失函数: MultipleNegativesRankingLoss")
print(f"In-Batch Negatives: {batch_size - 1} per query")

# 训练参数
num_epochs = 3
warmup_steps = int(len(train_dataloader) * 0.1)  # 10% warmup
output_dir = './models/bge-large-zh-travel-finetuned'

print(f"\n训练配置:")
print(f"  - Epochs: {num_epochs}")
print(f"  - Warmup steps: {warmup_steps}")
print(f"  - Learning rate: 2e-5 (默认)")
print(f"  - 输出目录: {output_dir}")

# 6. 开始训练
print("\n[6/6] 开始训练...")
print("=" * 60)

start_time = datetime.now()

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=num_epochs,
    warmup_steps=warmup_steps,
    output_path=output_dir,
    show_progress_bar=True,
    save_best_model=True,
)

end_time = datetime.now()
training_duration = (end_time - start_time).total_seconds()

print("=" * 60)
print("\n[OK] 训练完成!")
print(f"\n训练统计:")
print(f"  - 总时长: {training_duration:.1f}秒 ({training_duration/60:.1f}分钟)")
print(f"  - 每个epoch: {training_duration/num_epochs:.1f}秒")
print(f"  - 模型保存路径: {output_dir}")

# 7. 保存训练日志
log_info = {
    "base_model": "BAAI/bge-large-zh-v1.5",
    "training_samples": len(training_data),
    "batch_size": batch_size,
    "epochs": num_epochs,
    "loss_function": "MultipleNegativesRankingLoss",
    "training_duration_seconds": training_duration,
    "output_path": output_dir,
    "timestamp": datetime.now().isoformat()
}

with open(f'{output_dir}/training_log.json', 'w', encoding='utf-8') as f:
    json.dump(log_info, f, ensure_ascii=False, indent=2)

print(f"  - 训练日志: {output_dir}/training_log.json")
print("\n下一步: 运行 evaluate_model.py 评估模型效果")
