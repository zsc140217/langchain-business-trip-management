"""
使用MinerU v4精准解析API处理PDF文档

API版本: v4
模式: 本地文件批量上传解析
优势:
- 支持200MB/200页
- 表格提取准确率90%+
- vlm模型推荐（比pipeline更准确）

文档: https://opendatalab.github.io/MinerU/api/api_intro/
"""
import requests
import json
import time
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

# 修复Windows终端编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# API配置
API_KEY = os.environ.get("MINERU_API_KEY", "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxMTYwMDM2MiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc4MzU5ODcwNiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTM0MTk0OTgzODEiLCJvcGVuSWQiOm51bGwsInV1aWQiOiJkZGM0MjJlMC1jMTFjLTQ5MzQtODM2YS0xNTk2ZDQ5NGU0OTIiLCJlbWFpbCI6IiIsImV4cCI6MTc5MTM3NDcwNn0.Yva-bQNP7u9rMfUD9t1706OSHTOPPBEpiAXk7nHyD-NaMvZovP7ii_SdVRGju_s2Dh2E-VW3dEaQNt04UfN9AA")
API_BASE_URL = "https://mineru.net/api/v4"

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
PDF_PATH = PROJECT_ROOT / "关于印发内江嘉宏城建集团有限公司差旅费管理办法暂行的通知《公司各部室》内嘉城建司发（2019）4号.pdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "mineru_api_output"


def get_proxies():
    """获取代理配置"""
    if 'HTTP_PROXY' in os.environ or 'HTTPS_PROXY' in os.environ:
        return {
            'http': os.environ.get('HTTP_PROXY'),
            'https': os.environ.get('HTTPS_PROXY')
        }
    return None


def upload_and_parse_pdf(pdf_path: Path, output_dir: Path) -> Optional[Path]:
    """
    使用v4批量上传API处理PDF

    流程:
    1. 申请上传URL
    2. PUT上传文件
    3. 系统自动解析
    4. 轮询获取结果
    5. 下载解压ZIP包
    """
    print("=" * 60)
    print("MinerU v4 API 处理流程")
    print("=" * 60)
    print(f"PDF文件: {pdf_path}")
    print(f"文件大小: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
    print("")

    # 检查API Key
    if not API_KEY or len(API_KEY) < 50:
        print("[X] 错误: 未配置有效的API Key")
        print("请设置环境变量: export MINERU_API_KEY='your_key'")
        return None

    proxies = get_proxies()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # Step 1: 申请上传URL
    print("Phase 1: 申请上传URL")
    print("-" * 60)

    file_name = pdf_path.name
    data = {
        "files": [
            {"name": file_name, "data_id": "travel_policy_2019"}
        ],
        "model_version": "vlm",  # 推荐使用vlm模型
        "enable_table": True,
        "enable_formula": True,
        "language": "ch"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/file-urls/batch",
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        if result["code"] != 0:
            print(f"[X] 申请失败: {result.get('msg', '未知错误')}")
            return None

        batch_id = result["data"]["batch_id"]
        file_urls = result["data"]["file_urls"]
        upload_url = file_urls[0]

        print(f"[OK] 申请成功")
        print(f"Batch ID: {batch_id}")
        print("")

    except requests.exceptions.RequestException as e:
        print(f"[X] 申请失败: {e}")
        print("\n网络诊断:")
        print("- 检查代理设置: HTTP_PROXY=http://127.0.0.1:7897")
        print("- 测试API可达性: curl https://mineru.net")
        return None

    # Step 2: PUT上传文件
    print("Phase 2: 上传文件到OSS")
    print("-" * 60)

    try:
        with open(pdf_path, 'rb') as f:
            upload_response = requests.put(
                upload_url,
                data=f,
                proxies=proxies,
                timeout=180  # 11MB文件可能需要较长时间
            )

        if upload_response.status_code not in (200, 201):
            print(f"[X] 上传失败: HTTP {upload_response.status_code}")
            return None

        print(f"[OK] 上传成功 (用时 {upload_response.elapsed.total_seconds():.1f}s)")
        print("")

    except requests.exceptions.RequestException as e:
        print(f"[X] 上传失败: {e}")
        return None

    # Step 3: 轮询解析状态
    print("Phase 3: 等待云端解析")
    print("-" * 60)

    max_wait_time = 900  # 最多等待15分钟
    start_time = time.time()
    poll_interval = 10

    state_labels = {
        "waiting-file": "等待文件确认",
        "pending": "排队中",
        "running": "正在解析",
        "converting": "格式转换中",
        "done": "完成",
        "failed": "失败"
    }

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_time:
            print(f"\n[X] 超时: 处理时间超过 {max_wait_time/60:.0f} 分钟")
            print(f"Batch ID: {batch_id} (可稍后手动查询)")
            return None

        try:
            status_response = requests.get(
                f"{API_BASE_URL}/extract-results/batch/{batch_id}",
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data["code"] != 0:
                print(f"\n[X] 查询失败: {status_data.get('msg')}")
                return None

            extract_result = status_data["data"]["extract_result"][0]
            state = extract_result["state"]
            state_label = state_labels.get(state, state)

            # 显示进度
            progress_info = ""
            if "extract_progress" in extract_result:
                prog = extract_result["extract_progress"]
                progress_info = f" ({prog['extracted_pages']}/{prog['total_pages']} 页)"

            print(f"[{elapsed:.0f}s] {state_label}{progress_info}", end='\r')

            if state == "done":
                print(f"\n[OK] 解析完成 (用时 {elapsed:.0f}s)")
                full_zip_url = extract_result["full_zip_url"]
                print(f"ZIP URL: {full_zip_url}")
                print("")
                break

            elif state == "failed":
                err_msg = extract_result.get("err_msg", "未知错误")
                print(f"\n[X] 解析失败: {err_msg}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"\n[X] 查询状态失败: {e}")
            return None

        time.sleep(poll_interval)

    # Step 4: 下载并解压ZIP包
    print("Phase 4: 下载解析结果")
    print("-" * 60)

    try:
        zip_response = requests.get(
            full_zip_url,
            proxies=proxies,
            timeout=180
        )
        zip_response.raise_for_status()

        # 保存ZIP文件
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = output_dir / "result.zip"

        with open(zip_path, 'wb') as f:
            f.write(zip_response.content)

        print(f"[OK] ZIP下载完成 ({len(zip_response.content) / 1024 / 1024:.2f} MB)")

        # 解压ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        print(f"[OK] 解压完成")

        # 查找full.md文件
        md_files = list(output_dir.glob("**/full.md"))
        if not md_files:
            print("[X] 未找到full.md文件")
            return None

        md_file = md_files[0]
        print(f"[OK] Markdown: {md_file}")
        print(f"   大小: {md_file.stat().st_size / 1024:.2f} KB")

        # 复制到标准位置
        final_md = output_dir / "差旅管理办法.md"
        with open(md_file, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(final_md, 'w', encoding='utf-8') as dst:
            dst.write(content)

        print("")
        print("=" * 60)
        print("[OK] MinerU v4 API处理完成")
        print("=" * 60)

        return final_md

    except requests.exceptions.RequestException as e:
        print(f"[X] 下载失败: {e}")
        return None
    except zipfile.BadZipFile:
        print(f"[X] ZIP文件损坏")
        return None


if __name__ == "__main__":
    # 检查PDF文件
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
        print("\n\n[!] 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n[X] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
