# extract_policies.py
"""
任务2.1：提取政策文档
从差旅政策文件中提取段落，为训练数据生成做准备
"""
from pathlib import Path
import json

def extract_policies():
    policy_docs = []

    # 查找政策文档目录
    policy_dir = Path("../../data/travel_policies")

    if not policy_dir.exists():
        print(f"警告: 政策目录不存在 {policy_dir}")
        print("正在查找替代路径...")

        # 尝试其他可能的路径
        alternative_paths = [
            Path("../data/travel_policies"),
            Path("data/travel_policies"),
            Path("../../docs"),
        ]

        for alt_path in alternative_paths:
            if alt_path.exists():
                policy_dir = alt_path
                print(f"找到替代路径: {policy_dir}")
                break

    if not policy_dir.exists():
        print("错误: 找不到政策文档目录")
        print("请先创建政策文档或指定正确路径")
        return []

    # 支持多种文件格式
    file_patterns = ["*.txt", "*.md"]
    files_found = []

    for pattern in file_patterns:
        files_found.extend(policy_dir.glob(pattern))

    if not files_found:
        print(f"警告: 在 {policy_dir} 中未找到政策文档")
        return []

    print(f"找到 {len(files_found)} 个政策文档文件")

    for file in files_found:
        print(f"处理: {file.name}")
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

                # 按段落分割（双换行符）
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

                # 过滤太短的段落（少于20字符）
                paragraphs = [p for p in paragraphs if len(p) >= 20]

                policy_docs.extend(paragraphs)
                print(f"  提取了 {len(paragraphs)} 个段落")
        except Exception as e:
            print(f"  错误: {e}")

    return policy_docs

if __name__ == "__main__":
    print("="*60)
    print("任务2.1：提取政策文档")
    print("="*60)

    docs = extract_policies()

    if docs:
        output_file = "policy_docs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

        print(f"\n[SUCCESS] 成功提取 {len(docs)} 个政策段落")
        print(f"[SUCCESS] 保存到: {output_file}")

        # 显示前3个示例
        print("\n前3个示例:")
        for i, doc in enumerate(docs[:3], 1):
            print(f"\n{i}. {doc[:100]}..." if len(doc) > 100 else f"\n{i}. {doc}")
    else:
        print("\n[ERROR] 未提取到任何政策文档")
        print("\n建议:")
        print("1. 检查 data/travel_policies 目录是否存在")
        print("2. 确保目录中有 .txt 或 .md 格式的政策文档")
        print("3. 或者手动创建示例政策文档")
