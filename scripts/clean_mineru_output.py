"""
清洗MinerU输出的Markdown文件
问题：
1. OCR噪音（数学公式、页码误识别）
2. 内容重复
3. 表格内杂质
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import hashlib


def remove_math_formulas(text: str) -> str:
    """移除OCR错误识别的数学公式"""
    # 移除行内公式 $...$
    text = re.sub(r'\$[^$\n]+\$', '', text)

    # 移除行间公式 $$...$$
    text = re.sub(r'\$\$[^$]+\$\$', '', text, flags=re.DOTALL)

    return text


def remove_page_number_noise(text: str) -> str:
    """移除页码误识别为公式的内容"""
    # 移除类似 "(1) $\frac{1}{2}$ (2) $\frac{1}{2}$ ... (10)" 的噪音
    text = re.sub(r'\(\d+\)\s*\$[^$]+\$\s*(?:\(\d+\)\s*\$[^$]+\$\s*)*', '', text)

    # 移除单独的页码行（如 "-4" "6" "10"）
    text = re.sub(r'^\s*-?\d+\s*$', '', text, flags=re.MULTILINE)

    return text


def preserve_image_links(text: str) -> str:
    """保留图片链接（转换为本地相对路径）"""
    # 保留 ![alt](path) 格式，不做任何替换
    # MinerU API已经将URL替换为本地相对路径（images/xxx.jpg）
    return text


def deduplicate_content(text: str) -> str:
    """去除重复内容（改进版：按大块内容去重）"""
    lines = text.split('\n')

    # 按空行分割大块内容
    blocks = []
    current_block = []

    for line in lines:
        if line.strip() == '':
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        blocks.append('\n'.join(current_block))

    # 使用内容hash去重（保留第一次出现）
    seen_hashes = set()
    unique_blocks = []

    for block in blocks:
        # 计算内容hash（忽略空白差异）
        normalized = re.sub(r'\s+', ' ', block.strip())
        block_hash = hashlib.md5(normalized.encode()).hexdigest()

        if block_hash not in seen_hashes:
            seen_hashes.add(block_hash)
            unique_blocks.append(block)

    return '\n\n'.join(unique_blocks)


def clean_tables(text: str) -> str:
    """清理表格（保守策略：不删除任何表格）"""
    # 不再删除任何表格，保留所有内容
    return text


def normalize_whitespace(text: str) -> str:
    """规范化空白字符"""
    # 移除行尾空格
    text = re.sub(r' +\n', '\n', text)

    # 移除多余的空行（保留最多2个连续空行）
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text


def add_metadata_header(text: str) -> str:
    """添加元数据头部"""
    header = """# 内江嘉宏城建集团有限公司差旅费管理办法（暂行）

**文号**: 内嘉城建司发（2019）4号
**来源**: 真实企业差旅制度文档（MinerU解析）
**处理技术**: MinerU 3.4.3 + 后处理清洗
**处理日期**: 2026-07-09

---

"""
    return header + text


def clean_mineru_output(input_file: str, output_file: str):
    """主清洗流程"""
    print(f"开始清洗: {input_file}")

    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"原始文件大小: {len(text)} 字符")

    # 应用清洗步骤
    print("1. 移除数学公式...")
    text = remove_math_formulas(text)

    print("2. 移除页码噪音...")
    text = remove_page_number_noise(text)

    print("3. 保留图片链接...")
    text = preserve_image_links(text)

    print("4. 清理表格...")
    text = clean_tables(text)

    print("5. 去除重复内容...")
    text = deduplicate_content(text)

    print("6. 规范化空白...")
    text = normalize_whitespace(text)

    print("7. 添加元数据...")
    text = add_metadata_header(text)

    print(f"清洗后文件大小: {len(text)} 字符")

    # 保存清洗后的文件
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"清洗完成: {output_file}")

    # 统计信息
    print("\n统计信息:")
    print(f"- 总字符数: {len(text)}")
    print(f"- 总行数: {len(text.splitlines())}")
    print(f"- 章节数: {text.count('## 第')}")
    print(f"- 表格数: {text.count('<table>')}")


if __name__ == "__main__":
    # 默认路径
    INPUT_FILE = "data/mineru_api_output/差旅管理办法.md"
    OUTPUT_FILE = "data/knowledge_base/01_差旅管理办法.md"

    # 支持命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='清洗MinerU输出的Markdown文件')
    parser.add_argument('--input', default=INPUT_FILE, help='输入文件路径')
    parser.add_argument('--output', default=OUTPUT_FILE, help='输出文件路径')
    args = parser.parse_args()

    INPUT_FILE = args.input
    OUTPUT_FILE = args.output

    try:
        clean_mineru_output(INPUT_FILE, OUTPUT_FILE)
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
