import sys
import re

# 读取文件
with open('scripts/process_pdf_with_mineru_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有emoji为ASCII字符
replacements = {
    '✅': '[OK]',
    '❌': '[X]',
    '⚠️': '[!]',
    'ℹ️': '[i]'
}

for emoji, ascii_char in replacements.items():
    content = content.replace(emoji, ascii_char)

# 写回文件
with open('scripts/process_pdf_with_mineru_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emoji替换完成")
