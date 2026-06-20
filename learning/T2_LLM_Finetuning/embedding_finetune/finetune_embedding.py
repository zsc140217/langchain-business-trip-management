"""
Embedding模型微调脚本
使用sentence-transformers框架微调中文embedding模型
"""
import json
import os
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

def load_training_data(json_path):
    """加载训练数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 转换为InputExample格式
    examples = []
    for item in data:
        # 正样本对 (query, positive, label=1.0)
        examples.append(InputExample(texts=[item['query'], item['positive']], label=1.0))
        # 负样本对 (query, negative, label=0.0)
        examples.append(InputExample(texts=[item['query'], item['negative']], label=0.0))

    return examples

def finetune_embedding_model(
    model_name='BAAI/bge-large-zh-v1.5',
    train_data_path='train_data.json',
    output_path='./finetuned_model',
    batch_size=16,
    epochs=3
):
    """
    微调embedding模型

    Args:
        model_name: 预训练模型名称
        train_data_path: 训练数据路径
        output_path: 微调后模型保存路径
        batch_size: 批次大小
        epochs: 训练轮数
    """
    print("="*60)
    print("Embedding模型微调")
    print("="*60)

    # 1. 加载预训练模型
    print(f"\n[Step 1] 加载预训练模型: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"[OK] 模型加载成功，维度: {model.get_sentence_embedding_dimension()}")

    # 2. 加载训练数据
    print(f"\n[Step 2] 加载训练数据: {train_data_path}")
    train_examples = load_training_data(train_data_path)
    print(f"[OK] 加载了 {len(train_examples)} 个训练样本")

    # 3. 创建DataLoader
    print(f"\n[Step 3] 创建DataLoader (batch_size={batch_size})")
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    print(f"[OK] DataLoader创建成功")

    # 4. 定义损失函数 (CosineSimilarityLoss)
    print("\n[Step 4] 定义损失函数: CosineSimilarityLoss")
    train_loss = losses.CosineSimilarityLoss(model)
    print("[OK] 损失函数初始化完成")

    # 5. 开始微调
    print(f"\n[Step 5] 开始微调 (epochs={epochs})")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=100,
        show_progress_bar=True
    )
    print("[OK] 微调完成")

    # 6. 保存模型
    print(f"\n[Step 6] 保存微调后的模型: {output_path}")
    os.makedirs(output_path, exist_ok=True)
    model.save(output_path)
    print("[OK] 模型保存成功")

    print("\n" + "="*60)
    print("微调完成！")
    print("="*60)
    print(f"基础模型: {model_name}")
    print(f"训练样本: {len(train_examples)}")
    print(f"训练轮数: {epochs}")
    print(f"保存路径: {output_path}")
    print("\n[!] 这就是LLM微调：冻结大部分参数，只训练顶层来学习特定任务")

if __name__ == "__main__":
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 执行微调（使用BGE-large-zh-v1.5）
    finetune_embedding_model(
        model_name='BAAI/bge-large-zh-v1.5',  # 1.3GB的中文大模型
        train_data_path=os.path.join(script_dir, 'train_data.json'),
        output_path=os.path.join(script_dir, 'finetuned_model'),
        batch_size=16,  # Large模型用更大的batch
        epochs=5  # 增加训练轮数
    )
