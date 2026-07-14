"""
使用MinerU API处理PDF文档

优势：
- 云端GPU加速，无本地环境依赖
- 表格提取准确率90%+
- 稳定可靠，成本可控（约$2-5/100页）

API文档：https://mineru.openxlab.org.cn/api/v1/docs
"""
import requests
import json
import time
import os
import sys
from pathlib import Path
from typing import Optional

# 修复Windows终端编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# API配置
API_KEY = os.environ.get("MINERU_API_KEY", "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxMTYwMDM2MiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc4MzU5ODcwNiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTM0MTk0OTgzODEiLCJvcGVuSWQiOm51bGwsInV1aWQiOiJkZGM0MjJlMC1jMTFjLTQ5MzQtODM2YS0xNTk2ZDQ5NGU0OTIiLCJlbWFpbCI6IiIsImV4cCI6MTc5MTM3NDcwNn0.Yva-bQNP7u9rMfUD9t1706OSHTOPPBEpiAXk7nHyD-NaMvZovP7ii_SdVRGju_s2Dh2E-VW3dEaQNt04UfN9AA")
API_URL = "https://mineru.openxlab.org.cn/api/v1"

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
PDF_PATH = PROJECT_ROOT / "关于印发内江嘉宏城建集团有限公司差旅费管理办法暂行的通知《公司各部室》内嘉城建司发（2019）4号.pdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "mineru_api_output"


def upload_and_parse_pdf(pdf_path: Path, output_dir: Path) -> Optional[Path]:
    """
    上传PDF到MinerU API并获取解析结果

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录

    Returns:
        生成的Markdown文件路径
    """
    print("=" * 60)
    print("MinerU API 处理流程")
    print("=" * 60)
    print(f"PDF文件: {pdf_path}")
    print(f"文件大小: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
    print("")

    # 检查API Key
    if not API_KEY or API_KEY == "your_api_key_here":
        print("[X] 错误: 未配置API Key")
        print("请设置环境变量: export MINERU_API_KEY='your_key'")
        return None

    # 1. 上传文件
    print("Phase 1: 上传PDF到MinerU API")
    print("-" * 60)

    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        headers = {'Authorization': f'Bearer {API_KEY}'}

        try:
            # 检测代理设置
            proxies = {}
            if 'HTTP_PROXY' in os.environ or 'HTTPS_PROXY' in os.environ:
                print("检测到代理设置，尝试使用代理...")
                proxies = {
                    'http': os.environ.get('HTTP_PROXY'),
                    'https': os.environ.get('HTTPS_PROXY')
                }

            response = requests.post(
                f"{API_URL}/parse",
                files=files,
                headers=headers,
                proxies=proxies if proxies else None,
                timeout=120
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[X] 上传失败: {e}")
            print("\n网络诊断:")
            print("- 检查网络连接是否正常")
            print("- 如在中国大陆，可能需要配置代理")
            print("- 尝试直接访问: https://mineru.openxlab.org.cn")
            if hasattr(e, 'response') and e.response is not None:
                print(f"- 响应状态码: {e.response.status_code}")
                print(f"- 响应内容: {e.response.text[:200]}")
            return None

    result = response.json()
    task_id = result.get('task_id')

    if not task_id:
        print(f"[X] 未返回任务ID: {result}")
        return None

    print(f"[OK] 上传成功")
    print(f"任务ID: {task_id}")
    print("")

    # 2. 轮询任务状态
    print("Phase 2: 等待云端处理")
    print("-" * 60)

    max_wait_time = 600  # 最多等待10分钟
    start_time = time.time()
    poll_interval = 5

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_time:
            print(f"[X] 超时：处理时间超过 {max_wait_time} 秒")
            return None

        try:
            status_response = requests.get(
                f"{API_URL}/task/{task_id}",
                headers=headers,
                timeout=30
            )
            status_response.raise_for_status()
            status_data = status_response.json()
        except requests.exceptions.RequestException as e:
            print(f"[X] 查询状态失败: {e}")
            return None

        status = status_data.get('status')
        progress = status_data.get('progress', 0)

        print(f"[{elapsed:.0f}s] 状态: {status} | 进度: {progress}%", end='\r')

        if status == 'completed':
            print(f"\n[OK] 处理完成 (用时 {elapsed:.0f}s)")
            break
        elif status == 'failed':
            error_msg = status_data.get('error', '未知错误')
            print(f"\n[X] 处理失败: {error_msg}")
            return None

        time.sleep(poll_interval)

    print("")

    # 3. 下载Markdown结果
    print("Phase 3: 下载结果文件")
    print("-" * 60)

    try:
        markdown_response = requests.get(
            f"{API_URL}/task/{task_id}/markdown",
            headers=headers,
            timeout=60
        )
        markdown_response.raise_for_status()
        markdown_content = markdown_response.text
        print(f"[OK] Markdown下载完成 ({len(markdown_content)} 字符)")
    except requests.exceptions.RequestException as e:
        print(f"[X] Markdown下载失败: {e}")
        return None

    # 4. 下载图片（如果有）
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    try:
        images_response = requests.get(
            f"{API_URL}/task/{task_id}/images",
            headers=headers,
            timeout=60
        )

        if images_response.status_code == 200:
            images_data = images_response.json()
            image_count = len(images_data) if isinstance(images_data, list) else 0

            if image_count > 0:
                print(f"下载 {image_count} 个图片...", end=" ")

                for img in images_data:
                    img_url = img.get('url')
                    img_name = img.get('filename', 'unknown.jpg')

                    if not img_url:
                        continue

                    try:
                        img_response = requests.get(img_url, timeout=30)
                        img_response.raise_for_status()

                        img_path = images_dir / img_name
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)

                        # 替换Markdown中的URL为本地相对路径
                        markdown_content = markdown_content.replace(
                            img_url,
                            f"images/{img_name}"
                        )
                    except Exception as e:
                        print(f"\n警告: 图片 {img_name} 下载失败: {e}")

                print("[OK]")
            else:
                print("[i]  无图片")
        else:
            print("[i]  无图片数据")
    except Exception as e:
        print(f"警告: 图片下载异常: {e}")

    print("")

    # 5. 保存Markdown文件
    print("Phase 4: 保存文件")
    print("-" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)
    md_file = output_dir / "差旅管理办法.md"

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"[OK] Markdown: {md_file}")
    print(f"   大小: {md_file.stat().st_size / 1024:.2f} KB")

    # 6. 保存JSON格式（含结构化数据）
    try:
        json_response = requests.get(
            f"{API_URL}/task/{task_id}/json",
            headers=headers,
            timeout=60
        )

        if json_response.status_code == 200:
            json_file = output_dir / "差旅管理办法.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_response.json(), f, ensure_ascii=False, indent=2)
            print(f"[OK] JSON: {json_file}")
            print(f"   大小: {json_file.stat().st_size / 1024:.2f} KB")
    except Exception as e:
        print(f"警告: JSON保存失败: {e}")

    print("")
    print("=" * 60)
    print("[OK] MinerU API处理完成")
    print("=" * 60)

    return md_file


if __name__ == "__main__":
    import sys

    # 检查PDF文件是否存在
    if not PDF_PATH.exists():
        print(f"[X] 错误: PDF文件不存在")
        print(f"期望路径: {PDF_PATH}")
        sys.exit(1)

    try:
        result_file = upload_and_parse_pdf(PDF_PATH, OUTPUT_DIR)

        if result_file:
            print(f"\n下一步: 运行清洗脚本")
            print(f"python scripts/clean_mineru_output.py \\")
            print(f"    --input {result_file} \\")
            print(f"    --output data/knowledge_base/01_差旅管理办法.md")
        else:
            print("\n[X] 处理失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[!]  用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
