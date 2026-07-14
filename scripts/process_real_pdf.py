"""
处理真实企业差旅PDF文档
使用2026年最新技术栈:
- PyMuPDF 1.28.0 (2026-06-29发布)
- EasyOCR 1.7+ (深度学习OCR，跨平台稳定)
- Camelot 2.0.0 (2026-06-04发布，神经网络表格提取)

功能:
1. OCR识别27页扫描PDF
2. 使用ML模式提取表格（补贴标准、审批权限等）
3. 生成结构化Markdown文档
4. 替换data/knowledge_base/中的虚构内容
"""

import sys
import os
from pathlib import Path
import pymupdf
import easyocr
import camelot
import json
from typing import List, Dict, Any

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent
PDF_PATH = PROJECT_ROOT / "关于印发内江嘉宏城建集团有限公司差旅费管理办法暂行的通知《公司各部室》内嘉城建司发（2019）4号.pdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "knowledge_base"
OUTPUT_FILE = OUTPUT_DIR / "01_差旅管理办法.txt"

# 初始化EasyOCR（中英文双语，GPU加速）
print("正在初始化EasyOCR（首次运行会下载模型）...")
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True if os.environ.get('CUDA_VISIBLE_DEVICES') else False)
print("EasyOCR初始化完成")


def extract_text_from_page(pdf_doc: pymupdf.Document, page_num: int) -> str:
    """
    从PDF页面提取文本（使用EasyOCR）

    Args:
        pdf_doc: PyMuPDF文档对象
        page_num: 页码（从0开始）

    Returns:
        识别出的文本内容
    """
    page = pdf_doc[page_num]

    # 将页面渲染为高分辨率图像（提高OCR准确率）
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2倍分辨率
    img_path = f"temp_page_{page_num}.png"
    pix.save(img_path)

    try:
        # 使用EasyOCR识别
        # result格式: List[Tuple[bbox, text, confidence]]
        result = reader.readtext(img_path)

        if not result:
            return ""

        # 提取文本行（按y坐标排序，保持阅读顺序）
        lines = []
        for (bbox, text, confidence) in result:
            if confidence > 0.5:  # 只保留置信度>0.5的结果
                lines.append((bbox[0][1], text))  # (y_coordinate, text)

        # 按y坐标排序（从上到下）
        lines.sort(key=lambda x: x[0])
        sorted_text = [text for _, text in lines]

        return "\n".join(sorted_text)

    finally:
        # 清理临时文件
        if os.path.exists(img_path):
            os.remove(img_path)


def extract_tables_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    使用Camelot 2.0的ML模式提取表格

    Args:
        pdf_path: PDF文件路径

    Returns:
        表格列表，每个表格包含页码和数据
    """
    print("正在提取表格（使用Camelot ML模式）...")

    tables = []
    try:
        # 尝试使用ML模式（2026新特性）
        # 注意：如果ML模式不可用，会回退到lattice模式
        try:
            table_list = camelot.read_pdf(str(pdf_path), pages='all', flavor='ml')
        except Exception as e:
            print(f"ML模式不可用，使用lattice模式: {e}")
            table_list = camelot.read_pdf(str(pdf_path), pages='all', flavor='lattice')

        for i, table in enumerate(table_list):
            tables.append({
                'page': table.page,
                'index': i,
                'data': table.df.to_dict('records'),
                'accuracy': table.accuracy if hasattr(table, 'accuracy') else None
            })

        print(f"提取到 {len(tables)} 个表格")

    except Exception as e:
        print(f"表格提取失败: {e}")

    return tables


def format_markdown_output(pages_text: List[str], tables: List[Dict[str, Any]]) -> str:
    """
    格式化为Markdown文档

    Args:
        pages_text: 每页的文本内容列表
        tables: 提取的表格列表

    Returns:
        格式化的Markdown字符串
    """
    markdown = []

    # 添加文档头部
    markdown.append("# 内江嘉宏城建集团有限公司差旅费管理办法（暂行）")
    markdown.append("")
    markdown.append("**文号**: 内嘉城建司发（2019）4号")
    markdown.append("**来源**: 真实企业差旅制度文档（OCR识别）")
    markdown.append("**处理技术**: PyMuPDF 1.28.0 + EasyOCR 1.7+ + Camelot 2.0.0")
    markdown.append("")
    markdown.append("---")
    markdown.append("")

    # 添加每页内容
    for page_num, text in enumerate(pages_text, start=1):
        if text.strip():
            markdown.append(f"## 第 {page_num} 页")
            markdown.append("")
            markdown.append(text)
            markdown.append("")

    # 添加表格部分
    if tables:
        markdown.append("---")
        markdown.append("")
        markdown.append("## 附录：提取的表格")
        markdown.append("")

        for table in tables:
            markdown.append(f"### 表格 {table['index'] + 1} (第 {table['page']} 页)")
            if table['accuracy']:
                markdown.append(f"**提取准确率**: {table['accuracy']:.2f}%")
            markdown.append("")

            # 转换为Markdown表格
            if table['data']:
                headers = list(table['data'][0].keys())
                markdown.append("| " + " | ".join(headers) + " |")
                markdown.append("| " + " | ".join(["---"] * len(headers)) + " |")

                for row in table['data']:
                    values = [str(row.get(h, "")) for h in headers]
                    markdown.append("| " + " | ".join(values) + " |")

            markdown.append("")

    return "\n".join(markdown)


def process_pdf():
    """主处理流程"""

    print("=" * 60)
    print("开始处理真实企业差旅PDF文档")
    print("=" * 60)

    # 检查PDF文件
    if not PDF_PATH.exists():
        print(f"错误: PDF文件不存在: {PDF_PATH}")
        return

    print(f"PDF路径: {PDF_PATH}")
    print(f"文件大小: {PDF_PATH.stat().st_size / 1024 / 1024:.2f} MB")

    # 打开PDF
    doc = pymupdf.open(PDF_PATH)
    total_pages = len(doc)
    print(f"总页数: {total_pages}")
    print("")

    # Phase 1: OCR识别文本
    print("Phase 1: OCR识别文本内容")
    print("-" * 60)

    pages_text = []
    for page_num in range(total_pages):
        print(f"处理第 {page_num + 1}/{total_pages} 页...", end=" ")
        text = extract_text_from_page(doc, page_num)
        pages_text.append(text)
        print(f"识别 {len(text)} 字符")

    doc.close()
    print("")

    # Phase 2: 提取表格
    print("Phase 2: 提取表格")
    print("-" * 60)
    tables = extract_tables_from_pdf(PDF_PATH)
    print("")

    # Phase 3: 生成Markdown
    print("Phase 3: 生成结构化文档")
    print("-" * 60)
    markdown_content = format_markdown_output(pages_text, tables)

    # 保存输出
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"输出文件: {OUTPUT_FILE}")
    print(f"文件大小: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")
    print("")

    # 保存统计信息
    stats = {
        'total_pages': total_pages,
        'total_characters': sum(len(text) for text in pages_text),
        'total_tables': len(tables),
        'output_file': str(OUTPUT_FILE),
        'technology_stack': {
            'pymupdf': '1.28.0',
            'easyocr': '1.7+',
            'camelot': '2.0.0'
        }
    }

    stats_file = OUTPUT_DIR / "processing_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("处理完成!")
    print("=" * 60)
    print(f"识别文本: {stats['total_characters']} 字符")
    print(f"提取表格: {stats['total_tables']} 个")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"统计信息: {stats_file}")
    print("")

    # 显示前500字符预览
    print("内容预览 (前500字符):")
    print("-" * 60)
    preview = markdown_content[:500].replace('\n\n', '\n')
    print(preview)
    if len(markdown_content) > 500:
        print("...")
    print("")


if __name__ == "__main__":
    try:
        process_pdf()
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
