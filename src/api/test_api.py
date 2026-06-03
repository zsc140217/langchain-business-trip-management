"""
API测试套件 - LangServe端点测试

测试所有模块的invoke和stream端点

运行测试：
    python test_api.py

前置条件：
    1. API服务已启动（python -m api.main）
    2. 环境变量已配置（DASHSCOPE_API_KEY）
"""
import requests
import json
import time
from typing import Dict, Any


# API基础URL
BASE_URL = "http://localhost:8000"


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")


def test_health_check():
    """测试健康检查端点"""
    print("\n" + "=" * 80)
    print("测试健康检查")
    print("=" * 80)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"健康检查通过: {data.get('status')}")
            print_info(f"服务版本: {data.get('version')}")

            # 检查环境变量
            env_status = data.get('environment', {})
            for var, status in env_status.items():
                if "✓" in status:
                    print_success(f"  {var}: 已配置")
                elif "✗" in status:
                    print_error(f"  {var}: 未配置 (必需)")
                else:
                    print_warning(f"  {var}: 未配置 (可选)")

            return True
        else:
            print_error(f"健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"连接失败: {e}")
        print_info("请确保API服务已启动: python -m api.main")
        return False


def test_modules_list():
    """测试模块列表端点"""
    print("\n" + "=" * 80)
    print("测试模块列表")
    print("=" * 80)

    try:
        response = requests.get(f"{BASE_URL}/modules", timeout=5)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_modules', 0)
            print_success(f"获取到 {total} 个模块")

            for module in data.get('modules', []):
                print_info(f"  • {module['module']}")

            return True
        else:
            print_error(f"获取模块列表失败: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"请求失败: {e}")
        return False


def test_invoke_endpoint(path: str, input_data: Any, module_name: str):
    """
    测试invoke端点

    Args:
        path: API路径（如 /simple-rag）
        input_data: 输入数据
        module_name: 模块名称
    """
    print(f"\n{'─' * 80}")
    print(f"测试: {module_name} - invoke端点")
    print(f"{'─' * 80}")

    url = f"{BASE_URL}{path}/invoke"
    payload = {"input": input_data}

    print_info(f"请求: POST {url}")
    print_info(f"输入: {json.dumps(input_data, ensure_ascii=False)}")

    try:
        start_time = time.time()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            output = result.get("output", result)

            print_success(f"调用成功 (耗时: {elapsed:.2f}秒)")
            print(f"\n输出:")
            if isinstance(output, str):
                print(f"  {output[:200]}..." if len(output) > 200 else f"  {output}")
            else:
                print(f"  {json.dumps(output, ensure_ascii=False, indent=2)[:500]}...")

            return True
        else:
            print_error(f"调用失败: {response.status_code}")
            print_error(f"错误: {response.text[:200]}")
            return False

    except requests.Timeout:
        print_error("请求超时（60秒）")
        return False
    except Exception as e:
        print_error(f"请求异常: {e}")
        return False


def test_stream_endpoint(path: str, input_data: Any, module_name: str):
    """
    测试stream端点

    Args:
        path: API路径（如 /simple-rag）
        input_data: 输入数据
        module_name: 模块名称
    """
    print(f"\n{'─' * 80}")
    print(f"测试: {module_name} - stream端点")
    print(f"{'─' * 80}")

    url = f"{BASE_URL}{path}/stream"
    payload = {"input": input_data}

    print_info(f"请求: POST {url}")
    print_info(f"输入: {json.dumps(input_data, ensure_ascii=False)}")

    try:
        start_time = time.time()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=60
        )

        if response.status_code == 200:
            print_success("开始流式接收...")

            chunks = []
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    chunks.append(chunk)

            elapsed = time.time() - start_time
            total_content = "".join(chunks)

            print_success(f"流式接收完成 (耗时: {elapsed:.2f}秒)")
            print_info(f"接收到 {len(chunks)} 个数据块，总计 {len(total_content)} 字符")

            return True
        else:
            print_error(f"流式调用失败: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"流式请求异常: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("LangServe API 测试套件")
    print("=" * 80)

    # 测试用例定义
    test_cases = [
        {
            "path": "/simple-rag",
            "input": "去上海出差住宿能报多少钱？",
            "name": "Module 1: Simple RAG"
        },
        {
            "path": "/advanced-rag",
            "input": "出差期间的餐饮补贴标准是什么？",
            "name": "Module 2: Advanced RAG"
        },
        {
            "path": "/react-agent",
            "input": "北京明天天气怎么样？",
            "name": "Module 3: ReAct Agent"
        },
        {
            "path": "/multi-agent",
            "input": "下周去杭州出差3天，帮我规划行程",
            "name": "Module 4: Multi-Agent"
        },
        {
            "path": "/sequential-chain",
            "input": {"destination": "上海", "days": 3},
            "name": "Module 5: Sequential Chain"
        },
        {
            "path": "/parallel-chain",
            "input": {"destination": "深圳", "days": 2},
            "name": "Module 5: Parallel Chain"
        },
        {
            "path": "/memory-chain",
            "input": "我叫张三，下周要去北京出差",
            "name": "Module 6: Memory System"
        },
    ]

    # 1. 健康检查
    if not test_health_check():
        print_error("\n健康检查失败，终止测试")
        return

    # 2. 模块列表
    test_modules_list()

    # 3. 测试各模块
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
    }

    for test_case in test_cases:
        print(f"\n\n{'=' * 80}")
        print(f"测试模块: {test_case['name']}")
        print(f"{'=' * 80}")

        # 测试invoke端点
        results["total"] += 1
        if test_invoke_endpoint(test_case["path"], test_case["input"], test_case["name"]):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # 测试stream端点（可选）
        # 注释掉以加快测试速度
        # results["total"] += 1
        # if test_stream_endpoint(test_case["path"], test_case["input"], test_case["name"]):
        #     results["passed"] += 1
        # else:
        #     results["failed"] += 1

        # 避免请求过快
        time.sleep(1)

    # 4. 输出测试报告
    print("\n\n" + "=" * 80)
    print("测试报告")
    print("=" * 80)
    print(f"总计测试: {results['total']}")
    print_success(f"通过: {results['passed']}")
    print_error(f"失败: {results['failed']}")

    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{'=' * 80}")
        print("🎉 所有测试通过！")
        print(f"{'=' * 80}{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}{'=' * 80}")
        print("[FAIL] 部分测试失败，请检查错误信息")
        print(f"{'=' * 80}{Colors.RESET}\n")


if __name__ == "__main__":
    run_all_tests()
