"""
测试双引擎发票识别器

验证：
1. 分类器能否正确区分电子发票和老版发票
2. 双引擎是否自动选择正确的Prompt
3. 识别准确率是否提升（特别是老版发票的seller_name）
"""
import os
import sys
import io
from pathlib import Path

# 修复Windows编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.multimodal.dual_engine_recognizer import DualEngineInvoiceRecognizer
from src.multimodal.invoice_classifier import InvoiceVersionClassifier


def test_classifier():
    """测试分类器"""
    print("=" * 60)
    print("测试 1: 发票版本分类器")
    print("=" * 60)

    classifier = InvoiceVersionClassifier()

    # 测试电子发票
    test_files = [
        "train_data/dzfp_25502000000008817662_四川川海工程管理咨询有限公司_20250121101327.jpg",
    ]

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"[!] 文件不存在: {file_path}")
            continue

        result = classifier.get_classification_confidence(file_path)
        print(f"\n文件: {Path(file_path).name}")
        print(f"  版本: {result['version']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  依据: {', '.join(result['evidence'])}")

    print("\n[OK] 分类器测试完成\n")


def test_dual_engine_recognition():
    """测试双引擎识别"""
    print("=" * 60)
    print("测试 2: 双引擎发票识别")
    print("=" * 60)

    # 初始化识别器
    api_key = os.getenv(
        "QIANFAN_API_KEY",
        "bce-v3/ALTAK-bb5n0uwwEtylRfFVWBnrz/ac8b75364bcb7016af82a0789335a0c8d4ce594e"
    )

    recognizer = DualEngineInvoiceRecognizer(
        api_key=api_key,
        model="qianfan-ocr",
        enable_thinking=True,
        confidence_threshold=0.8
    )

    # 测试文件
    test_cases = [
        {
            "file": "train_data/dzfp_25502000000008817662_四川川海工程管理咨询有限公司_20250121101327.jpg",
            "expected_version": "electronic",
            "expected_seller": "遂宁公路工程有限公司",
        }
    ]

    for case in test_cases:
        file_path = case["file"]

        if not os.path.exists(file_path):
            print(f"[!] 文件不存在: {file_path}")
            continue

        print(f"\n{'='*60}")
        print(f"识别文件: {Path(file_path).name}")
        print(f"{'='*60}")

        try:
            result = recognizer.recognize(file_path)

            # 打印分类信息
            print(f"\n【版本分类】")
            print(f"  识别版本: {result['invoice_version']}")
            print(f"  使用引擎: {result['engine_type']}")
            print(f"  分类置信度: {result['classification_confidence']:.2f}")
            print(f"  分类依据: {', '.join(result['classification_evidence'])}")

            # 打印识别结果
            print(f"\n【识别结果】")
            print(f"  发票代码: {result.get('invoice_code')}")
            print(f"  发票号码: {result.get('invoice_number')}")
            print(f"  开票日期: {result.get('date')}")
            print(f"  销售方名称: {result.get('seller_name')}")
            print(f"  销售方税号: {result.get('seller_tax_id')}")
            print(f"  购买方名称: {result.get('buyer_name')}")
            print(f"  金额: {result.get('amount')}")
            print(f"  税额: {result.get('tax')}")
            print(f"  价税合计: {result.get('total')}")

            # 打印质量指标
            print(f"\n【质量指标】")
            print(f"  置信度: {result['confidence']:.3f}")
            need_review_text = "是" if result['need_review'] else "否"
            print(f"  需要复核: {need_review_text}")
            if result['warnings']:
                print(f"  警告: {len(result['warnings'])} 个")
                for warning in result['warnings']:
                    print(f"    - {warning}")
            else:
                print(f"  警告: 无")

            # 验证结果
            print(f"\n【验证】")
            version_correct = result['invoice_version'] == case['expected_version']
            seller_correct = result.get('seller_name') == case['expected_seller']

            if version_correct:
                print(f"  版本判断: 正确")
            else:
                print(f"  版本判断: 错误")

            if seller_correct:
                print(f"  销售方识别: 正确")
            else:
                print(f"  销售方识别: 错误 (期望: {case['expected_seller']})")

        except Exception as e:
            print(f"\n[ERROR] 识别失败: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("[OK] 双引擎识别测试完成")
    print("="*60)


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("双引擎发票识别器 - 综合测试")
    print("="*60)

    # 测试1: 分类器
    test_classifier()

    # 测试2: 双引擎识别
    test_dual_engine_recognition()

    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)
    print("\n说明：")
    print("1. 分类器根据文件名、发票代码长度、日期自动判断版本")
    print("2. 双引擎根据版本自动选择对应的Prompt")
    print("3. 电子发票使用电子发票Prompt（销售方在上）")
    print("4. 老版发票使用老版Prompt（强调布局相反）")
    print("5. 识别结果中包含版本信息和分类依据\n")


if __name__ == "__main__":
    main()
