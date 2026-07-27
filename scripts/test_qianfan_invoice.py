"""
百度千帆发票识别测试脚本
测试零样本准确率并决策是否需要微调
"""

import os
import sys
import json
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.multimodal.qianfan_invoice_recognizer import QianfanInvoiceRecognizer


def extract_number(text: str) -> float:
    """
    从文本中提取数字，忽略货币符号和编码问题

    Args:
        text: 可能包含货币符号的文本

    Returns:
        提取的浮点数
    """
    # 使用正则表达式提取数字（整数和小数）
    match = re.search(r'(\d+\.?\d*)', text)
    if match:
        return float(match.group(1))
    raise ValueError(f"无法从 '{text}' 中提取数字")


def load_ground_truth(train_json_path: str) -> dict:
    """
    从训练数据加载真实标注

    Args:
        train_json_path: train.json 路径

    Returns:
        {filename: {field: value}} 格式的真实标注
    """
    ground_truth = {}

    with open(train_json_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue

            filename = parts[0]
            annotations = json.loads(parts[1])

            # 构建 question-answer 映射
            qa_map = {}
            for item in annotations:
                if item['label'] == 'question':
                    # 找到对应的 answer
                    for link in item.get('linking', []):
                        answer_id = link[1]
                        answer_item = next((a for a in annotations if a['id'] == answer_id), None)
                        if answer_item:
                            qa_map[item['transcription']] = answer_item['transcription']

            # 转换为标准字段
            gt = {}

            # 发票号码
            if 'No' in qa_map:
                gt['invoice_number'] = qa_map['No']

            # 开票日期
            if '开票日期' in qa_map:
                date_str = qa_map['开票日期']
                # 转换格式：2016年06月12日 -> 2016-06-12
                date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                gt['date'] = date_str

            # 销售方名称
            if '名称' in qa_map:
                gt['seller_name'] = qa_map['名称']

            # 纳税人识别号
            if '纳税人识别号' in qa_map:
                gt['seller_tax_id'] = qa_map['纳税人识别号']

            # 金额
            if '金额' in qa_map:
                gt['amount'] = extract_number(qa_map['金额'])

            # 税率
            if '税率' in qa_map:
                tax_rate_str = qa_map['税率'].replace('%', '').strip()
                gt['tax_rate'] = float(tax_rate_str) / 100

            # 税额
            if '税额' in qa_map or '税颜' in qa_map:  # 注意 OCR 错误
                tax_str = qa_map.get('税额', qa_map.get('税颜', '0'))
                gt['tax'] = extract_number(tax_str)

            # 价税合计
            if '价税合计' in qa_map:
                gt['total'] = extract_number(qa_map['价税合计'])

            ground_truth[filename] = gt

    return ground_truth


def print_statistics(accuracy: dict):
    """
    打印准确率统计

    Args:
        accuracy: calculate_accuracy 返回的结果
    """
    print("\n" + "="*60)
    print("准确率统计")
    print("="*60)

    print(f"\n总样本数: {accuracy['total_samples']}")
    print(f"完全匹配率: {accuracy['exact_match_rate']:.2%}")
    print(f"平均字段准确率: {accuracy['average_accuracy']:.2%}")

    print("\n各字段准确率:")
    print("-" * 60)
    for field, acc in sorted(accuracy['field_accuracy'].items()):
        bar_length = int(acc * 30)
        bar = "#" * bar_length + "-" * (30 - bar_length)  # 使用 ASCII 字符
        print(f"  {field:20s} {bar} {acc:.2%}")

    print("="*60)


def recommend_next_step(accuracy: dict):
    """
    根据准确率推荐下一步行动

    Args:
        accuracy: 准确率统计
    """
    avg_acc = accuracy['average_accuracy']

    print("\n" + "="*60)
    print("决策建议")
    print("="*60)

    if avg_acc >= 0.85:
        print("\n[OK] 零样本准确率已达到 85% 以上")
        print("\n推荐方案: 直接使用，无需微调")
        print("\n后续优化方向:")
        print("  1. 优化 Prompt，提高低准确率字段")
        print("  2. 调整置信度阈值，降低人工复核率")
        print("  3. 收集边缘案例，针对性优化")

    elif avg_acc >= 0.70:
        print("\n[WARNING] 零样本准确率在 70-85% 之间")
        print("\n推荐方案: 考虑微调")
        print("\n微调方案:")
        print("  1. 使用 LoRA 参数高效微调")
        print("  2. 数据增强：从 30 个样本生成 200+ 训练样本")
        print("  3. 训练时间：预计 1-2 小时（单 A100）")
        print("  4. 预期效果：准确率提升至 92%+")

    else:
        print("\n[ERROR] 零样本准确率低于 70%")
        print("\n可能原因:")
        print("  1. Prompt 设计不够精确")
        print("  2. 模型不适合中文发票场景")
        print("  3. 数据质量有问题")
        print("\n推荐方案:")
        print("  1. 优化 Prompt，重新测试")
        print("  2. 尝试其他视觉模型（如 deepseek-vl2）")
        print("  3. 检查数据标注质量")

    # 低准确率字段分析
    low_acc_fields = {k: v for k, v in accuracy['field_accuracy'].items() if v < 0.7}
    if low_acc_fields:
        print("\n[WARNING] 低准确率字段（<70%）:")
        for field, acc in sorted(low_acc_fields.items(), key=lambda x: x[1]):
            print(f"  - {field}: {acc:.2%}")
        print("\n建议针对这些字段优化 Prompt 或增加训练数据")

    print("="*60)


def main():
    """主测试流程"""

    # API Key
    API_KEY = "bce-v3/ALTAK-bb5n0uwwEtylRfFVWBnrz/ac8b75364bcb7016af82a0789335a0c8d4ce594e"

    # 路径配置
    train_json_path = project_root / "train_data" / "zzsfp" / "train.json"
    imgs_dir = project_root / "train_data" / "zzsfp" / "imgs"

    print("="*60)
    print("百度千帆发票识别 - 零样本准确率测试")
    print("="*60)

    # 1. 加载真实标注
    print("\n[1/4] 加载真实标注...")
    ground_truth = load_ground_truth(str(train_json_path))
    print(f"  加载了 {len(ground_truth)} 个样本的标注")

    # 2. 初始化识别器
    print("\n[2/4] 初始化识别器...")
    recognizer = QianfanInvoiceRecognizer(
        api_key=API_KEY,
        model="qianfan-ocr",  # 使用百度千帆 OCR 专用模型（小写）
        enable_thinking=True,  # 启用 Layout-as-Thought
        confidence_threshold=0.8
    )
    print("  模型: qianfan-ocr")
    print("  思考模式: 开启")

    # 3. 批量识别（测试前 5 个样本）
    print("\n[3/4] 开始识别...")
    print("  注意: 为节省成本，先测试 5 个样本")
    print("  如需测试全部 30 个样本，请修改脚本中的 test_samples 数量")

    test_samples = 5  # 修改这里可以测试更多样本
    image_files = sorted([f for f in imgs_dir.glob("*.jpg")])[:test_samples]

    results = recognizer.batch_recognize(
        invoice_paths=[str(f) for f in image_files],
        save_results=True,
        output_dir=str(project_root / "results")
    )

    # 4. 计算准确率
    print("\n[4/4] 计算准确率...")
    accuracy = recognizer.calculate_accuracy(results, ground_truth)

    # 打印统计
    print_statistics(accuracy)

    # 推荐下一步
    recommend_next_step(accuracy)

    # 成本估算
    print("\n" + "="*60)
    print("成本估算")
    print("="*60)
    total_tokens = sum(r.get('raw_response', {}).get('usage', {}).get('total_tokens', 0) for r in results)
    print(f"  本次测试消耗 tokens: ~{total_tokens} (估算)")
    print(f"  测试样本数: {test_samples}")
    if test_samples < 30:
        print(f"  全量测试 30 个样本预计消耗: ~{total_tokens * 30 // test_samples} tokens")
    print("="*60)


if __name__ == "__main__":
    main()
