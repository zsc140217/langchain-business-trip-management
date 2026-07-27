#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版发票识别测试脚本
用于快速验证核心功能，不依赖模型微调
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.multimodal.invoice_recognizer import AdvancedInvoiceRecognizer


def test_single_invoice():
    """测试单张发票识别"""

    print("="*60)
    print("发票识别简单测试")
    print("="*60)

    # 初始化识别器（使用预训练模型，无需微调）
    print("\n[1/3] 初始化识别器...")
    try:
        recognizer = AdvancedInvoiceRecognizer()
        print("[OK] 识别器初始化成功")
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        print("\n提示: 请先安装依赖:")
        print("  pip install paddleocr paddlepaddle transformers torch pillow opencv-python")
        return

    # 选择测试样本
    test_samples = list(Path('train_data/zzsfp/imgs').glob('*.jpg'))
    if not test_samples:
        print("\n[ERROR] 未找到测试图片，请检查 train_data/zzsfp/imgs/ 目录")
        return

    test_image = test_samples[0]
    print(f"\n[2/3] 识别测试发票: {test_image.name}")

    # 执行识别
    try:
        result = recognizer.recognize(str(test_image))

        print("\n[3/3] 识别结果:")
        print("-"*60)
        print(f"发票代码: {result.get('code', 'N/A')}")
        print(f"发票号码: {result.get('number', 'N/A')}")
        print(f"开票日期: {result.get('date', 'N/A')}")
        print(f"金额: {result.get('amount', 'N/A')}")
        print(f"税额: {result.get('tax', 'N/A')}")
        print(f"价税合计: {result.get('total', 'N/A')}")
        print(f"销售方: {result.get('seller', 'N/A')}")
        print(f"购买方: {result.get('buyer', 'N/A')}")
        print(f"\n置信度: {result.get('confidence', 0):.3f}")

        if result.get('warnings'):
            print(f"\n警告:")
            for warning in result['warnings']:
                print(f"  - {warning}")

        print("-"*60)

        if result.get('confidence', 0) > 0.8:
            print("\n[OK] 识别成功 (高置信度)")
        elif result.get('confidence', 0) > 0.6:
            print("\n[WARN] 识别完成，但建议人工复核")
        else:
            print("\n[ERROR] 识别置信度较低，需要人工复核")

    except Exception as e:
        print(f"\n[ERROR] 识别失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    test_single_invoice()
