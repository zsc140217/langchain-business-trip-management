"""
测试老版发票识别 - 验证双引擎效果
"""
import os
import sys
import io
from pathlib import Path

# 修复Windows编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.multimodal.dual_engine_recognizer import DualEngineInvoiceRecognizer

def test_old_invoices():
    """测试老版发票"""
    print("=" * 60)
    print("老版发票识别测试 - 验证Prompt优化效果")
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

    # 测试3张老版发票
    test_files = [
        "train_data/zzsfp/imgs/b0.jpg",
        "train_data/zzsfp/imgs/b1.jpg",
        "train_data/zzsfp/imgs/b2.jpg",
    ]

    results_summary = []

    for idx, file_path in enumerate(test_files, 1):
        if not os.path.exists(file_path):
            print(f"\n[!] 文件不存在: {file_path}")
            continue

        print(f"\n{'='*60}")
        print(f"测试 {idx}/3: {Path(file_path).name}")
        print(f"{'='*60}")

        try:
            result = recognizer.recognize(file_path)

            # 打印分类信息
            print(f"\n[分类结果]")
            print(f"  版本识别: {result['invoice_version']}")
            print(f"  使用引擎: {result['engine_type']}")
            print(f"  分类置信度: {result['classification_confidence']:.2f}")
            print(f"  分类依据: {', '.join(result['classification_evidence'])}")

            # 打印核心字段
            print(f"\n[识别结果]")
            print(f"  发票代码: {result.get('invoice_code')}")
            print(f"  开票日期: {result.get('date')}")
            print(f"  销售方名称: {result.get('seller_name')}")
            print(f"  销售方税号: {result.get('seller_tax_id')}")
            print(f"  购买方名称: {result.get('buyer_name')}")
            print(f"  金额: {result.get('amount')}")
            print(f"  税额: {result.get('tax')}")
            print(f"  价税合计: {result.get('total')}")

            # 打印质量指标
            print(f"\n[质量评估]")
            print(f"  置信度: {result['confidence']:.3f}")
            print(f"  需要复核: {'是' if result['need_review'] else '否'}")
            if result['warnings']:
                print(f"  警告数: {len(result['warnings'])}")
                for warning in result['warnings']:
                    print(f"    - {warning}")

            # 统计
            results_summary.append({
                'file': Path(file_path).name,
                'version': result['invoice_version'],
                'engine': result['engine_type'],
                'seller_name': result.get('seller_name'),
                'has_seller': bool(result.get('seller_name')),
                'confidence': result['confidence'],
                'need_review': result['need_review']
            })

        except Exception as e:
            print(f"\n[ERROR] 识别失败: {str(e)}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'file': Path(file_path).name,
                'error': str(e)
            })

    # 汇总统计
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    success_count = len([r for r in results_summary if 'error' not in r])
    old_version_count = len([r for r in results_summary if r.get('version') == 'old'])
    old_engine_count = len([r for r in results_summary if r.get('engine') == 'old'])
    seller_identified = len([r for r in results_summary if r.get('has_seller')])

    print(f"\n识别成功: {success_count}/3")
    print(f"版本判断为'old': {old_version_count}/3")
    print(f"使用老版引擎: {old_engine_count}/3")
    print(f"seller_name识别成功: {seller_identified}/3")

    if success_count > 0:
        avg_confidence = sum(r.get('confidence', 0) for r in results_summary if 'error' not in r) / success_count
        print(f"平均置信度: {avg_confidence:.3f}")

    print("\n[详细结果]")
    for r in results_summary:
        if 'error' in r:
            print(f"  {r['file']}: 失败 - {r['error']}")
        else:
            status = "[OK]" if r['has_seller'] else "[NO_SELLER]"
            print(f"  {r['file']}: {status} 版本={r['version']}, 引擎={r['engine']}, seller={r.get('seller_name', 'None')}")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

    # 评估效果
    print("\n[效果评估]")
    if seller_identified >= 2:
        print("[SUCCESS] seller_name识别率 >= 67%, Prompt优化有效!")
    elif seller_identified == 1:
        print("[PARTIAL] seller_name识别率 33%, 效果一般，建议考虑LoRA微调")
    else:
        print("[FAIL] seller_name识别率 0%, Prompt优化无效，需要LoRA微调")

if __name__ == "__main__":
    test_old_invoices()
