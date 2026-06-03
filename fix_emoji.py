#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量替换源代码中的 emoji 字符，避免 Windows GBK 编码错误
"""
import os
import re

# Emoji 替换映射
EMOJI_MAP = {
    '🔄': '[INFO]',
    '✅': '[OK]',
    '⚠️': '[WARN]',
    '🔍': '[SEARCH]',
    '💾': '[SAVE]',
    '📂': '[LOAD]',
    '❌': '[FAIL]',
    '1️⃣': 'Step 1:',
    '2️⃣': 'Step 2:',
    '3️⃣': 'Step 3:',
    '4️⃣': 'Step 4:',
    '5️⃣': 'Step 5:',
    '6️⃣': 'Step 6:',
    '7️⃣': 'Step 7:',
    '8️⃣': 'Step 8:',
    '9️⃣': 'Step 9:',
}

def fix_emoji_in_file(filepath):
    """修复单个文件中的 emoji"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 替换所有 emoji
        for emoji, replacement in EMOJI_MAP.items():
            content = content.replace(emoji, replacement)

        # 只有内容变化时才写入
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Fixed: {filepath}")
            return True
        else:
            print(f"[SKIP] No emoji found: {filepath}")
            return False

    except Exception as e:
        print(f"[FAIL] Error processing {filepath}: {e}")
        return False

def main():
    """主函数"""
    src_dir = os.path.join(os.path.dirname(__file__), 'src')

    # 需要处理的目录
    target_dirs = [
        'modules/module_1_simple_rag',
        'modules/module_2_advanced_rag',
        'api',
    ]

    fixed_count = 0

    for target_dir in target_dirs:
        full_dir = os.path.join(src_dir, target_dir)
        if not os.path.exists(full_dir):
            print(f"[WARN] Directory not found: {full_dir}")
            continue

        print(f"\n[INFO] Processing directory: {target_dir}")

        for root, dirs, files in os.walk(full_dir):
            for filename in files:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    if fix_emoji_in_file(filepath):
                        fixed_count += 1

    print(f"\n{'='*60}")
    print(f"[SUMMARY] Fixed {fixed_count} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
