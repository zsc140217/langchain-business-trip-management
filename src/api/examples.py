"""
LangServe API 使用示例

展示如何在不同场景下调用API

目录：
1. Python示例
2. JavaScript/Node.js示例
3. cURL示例
4. 流式调用示例
5. 批量请求示例
"""

# ============================================================================
# 1. Python示例
# ============================================================================

import requests
from typing import Dict, Any


class LangChainAPI:
    """LangChain API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def invoke(self, module: str, input_data: Any) -> Dict[str, Any]:
        """
        同步调用API

        Args:
            module: 模块路径（如 "simple-rag"）
            input_data: 输入数据

        Returns:
            API响应
        """
        url = f"{self.base_url}/{module}/invoke"
        response = requests.post(
            url,
            json={"input": input_data},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def stream(self, module: str, input_data: Any):
        """
        流式调用API

        Args:
            module: 模块路径
            input_data: 输入数据

        Yields:
            流式响应块
        """
        url = f"{self.base_url}/{module}/stream"
        response = requests.post(
            url,
            json={"input": input_data},
            headers={"Content-Type": "application/json"},
            stream=True,
        )
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


# 使用示例
def python_examples():
    """Python调用示例"""
    client = LangChainAPI()

    # 示例1: Simple RAG
    print("=== 示例1: Simple RAG ===")
    result = client.invoke("simple-rag", "去上海出差住宿能报多少钱？")
    print(f"答案: {result['output']}\n")

    # 示例2: ReAct Agent
    print("=== 示例2: ReAct Agent ===")
    result = client.invoke("react-agent", "北京明天天气怎么样？")
    print(f"结果: {result['output']}\n")

    # 示例3: Sequential Chain (复杂输入)
    print("=== 示例3: Sequential Chain ===")
    result = client.invoke("sequential-chain", {
        "destination": "上海",
        "days": 3
    })
    print(f"规划: {result['output']}\n")

    # 示例4: 流式调用
    print("=== 示例4: 流式调用 ===")
    print("流式输出: ", end="", flush=True)
    for chunk in client.stream("simple-rag", "出差餐饮补贴标准？"):
        print(chunk, end="", flush=True)
    print("\n")


# ============================================================================
# 2. JavaScript/Node.js示例
# ============================================================================

JS_EXAMPLE = """
// LangChain API客户端 (JavaScript/Node.js)

class LangChainAPI {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // 同步调用
  async invoke(module, inputData) {
    const url = `${this.baseUrl}/${module}/invoke`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input: inputData }),
    });

    if (!response.ok) {
      throw new Error(`API调用失败: ${response.statusText}`);
    }

    return await response.json();
  }

  // 流式调用
  async *stream(module, inputData) {
    const url = `${this.baseUrl}/${module}/stream`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input: inputData }),
    });

    if (!response.ok) {
      throw new Error(`流式调用失败: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value);
    }
  }
}

// 使用示例
async function examples() {
  const client = new LangChainAPI();

  // 示例1: Simple RAG
  console.log('=== 示例1: Simple RAG ===');
  const result1 = await client.invoke('simple-rag', '去上海出差住宿能报多少钱？');
  console.log('答案:', result1.output);

  // 示例2: ReAct Agent
  console.log('\\n=== 示例2: ReAct Agent ===');
  const result2 = await client.invoke('react-agent', '北京明天天气怎么样？');
  console.log('结果:', result2.output);

  // 示例3: 流式调用
  console.log('\\n=== 示例3: 流式调用 ===');
  process.stdout.write('流式输出: ');
  for await (const chunk of client.stream('simple-rag', '出差餐饮补贴标准？')) {
    process.stdout.write(chunk);
  }
  console.log('\\n');
}

// 运行示例
examples().catch(console.error);
"""


# ============================================================================
# 3. cURL示例
# ============================================================================

CURL_EXAMPLES = """
# cURL调用示例

# 1. 健康检查
curl http://localhost:8000/health

# 2. 获取模块列表
curl http://localhost:8000/modules

# 3. Simple RAG - invoke
curl -X POST "http://localhost:8000/simple-rag/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "去上海出差住宿能报多少钱？"}'

# 4. Simple RAG - stream
curl -X POST "http://localhost:8000/simple-rag/stream" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "去上海出差住宿能报多少钱？"}'

# 5. ReAct Agent
curl -X POST "http://localhost:8000/react-agent/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "北京明天天气怎么样？"}'

# 6. Multi-Agent
curl -X POST "http://localhost:8000/multi-agent/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "下周去杭州出差3天，帮我规划行程"}'

# 7. Sequential Chain (复杂输入)
curl -X POST "http://localhost:8000/sequential-chain/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": {"destination": "上海", "days": 3}}'

# 8. Parallel Chain
curl -X POST "http://localhost:8000/parallel-chain/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": {"destination": "深圳", "days": 2}}'

# 9. Memory System
curl -X POST "http://localhost:8000/memory-chain/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "我叫张三，下周要去北京出差"}'

# 10. 使用jq格式化输出
curl -X POST "http://localhost:8000/simple-rag/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "去上海出差住宿能报多少钱？"}' | jq .

# 11. 保存响应到文件
curl -X POST "http://localhost:8000/simple-rag/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "去上海出差住宿能报多少钱？"}' \\
     -o response.json

# 12. 显示详细信息（包括headers）
curl -v -X POST "http://localhost:8000/simple-rag/invoke" \\
     -H "Content-Type: application/json" \\
     -d '{"input": "去上海出差住宿能报多少钱？"}'
"""


# ============================================================================
# 4. 流式调用示例
# ============================================================================

def streaming_example():
    """
    流式调用示例

    适用场景：
    - 长文本生成
    - 实时反馈
    - 改善用户体验
    """
    import requests
    import sys

    url = "http://localhost:8000/simple-rag/stream"
    payload = {"input": "详细说明企业差旅管理的所有规章制度"}

    print("开始流式接收...\n")
    print("输出: ", end="", flush=True)

    response = requests.post(
        url,
        json=payload,
        stream=True,
    )

    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end="", flush=True)
            sys.stdout.flush()

    print("\n\n流式接收完成！")


# ============================================================================
# 5. 批量请求示例
# ============================================================================

def batch_requests_example():
    """
    批量请求示例

    适用场景：
    - 批量处理问题
    - 性能测试
    - 数据处理流水线
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    questions = [
        "去上海出差住宿能报多少钱？",
        "从北京到上海应该坐什么交通工具？",
        "出差期间每天的餐补是多少？",
        "出差报销有什么时间要求？",
        "三线城市的住宿标准是多少？",
    ]

    def query_api(question: str) -> Dict[str, Any]:
        """查询API"""
        url = "http://localhost:8000/simple-rag/invoke"
        response = requests.post(url, json={"input": question})
        return {
            "question": question,
            "answer": response.json()["output"],
            "status": response.status_code,
        }

    print(f"批量处理 {len(questions)} 个问题...\n")
    start_time = time.time()

    # 使用线程池并发请求
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_question = {
            executor.submit(query_api, q): q for q in questions
        }

        for future in as_completed(future_to_question):
            try:
                result = future.result()
                results.append(result)
                print(f"✓ {result['question']}")
                print(f"  {result['answer'][:100]}...\n")
            except Exception as e:
                print(f"✗ 请求失败: {e}\n")

    elapsed = time.time() - start_time
    print(f"完成！总耗时: {elapsed:.2f}秒")
    print(f"平均每个问题: {elapsed / len(questions):.2f}秒")


# ============================================================================
# 6. 错误处理示例
# ============================================================================

def error_handling_example():
    """
    错误处理示例

    展示如何优雅地处理各种错误
    """
    import requests
    from requests.exceptions import Timeout, ConnectionError, HTTPError

    def safe_api_call(module: str, input_data: Any) -> Dict[str, Any]:
        """安全的API调用，包含完整错误处理"""
        url = f"http://localhost:8000/{module}/invoke"

        try:
            response = requests.post(
                url,
                json={"input": input_data},
                timeout=30,  # 30秒超时
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        except Timeout:
            return {"success": False, "error": "请求超时"}

        except ConnectionError:
            return {"success": False, "error": "无法连接到API服务器"}

        except HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP错误: {e.response.status_code}",
                "detail": e.response.text,
            }

        except Exception as e:
            return {"success": False, "error": f"未知错误: {str(e)}"}

    # 使用示例
    result = safe_api_call("simple-rag", "去上海出差住宿能报多少钱？")

    if result["success"]:
        print(f"成功: {result['data']['output']}")
    else:
        print(f"失败: {result['error']}")


# ============================================================================
# 7. 性能测试示例
# ============================================================================

def performance_test():
    """
    性能测试示例

    测试API的响应时间和吞吐量
    """
    import requests
    import time
    import statistics

    url = "http://localhost:8000/simple-rag/invoke"
    test_input = "去上海出差住宿能报多少钱？"
    num_requests = 10

    print(f"性能测试: 发送 {num_requests} 个请求...\n")

    times = []
    for i in range(num_requests):
        start = time.time()
        response = requests.post(url, json={"input": test_input})
        elapsed = time.time() - start

        times.append(elapsed)
        print(f"请求 {i + 1}: {elapsed:.3f}秒")

    print("\n统计结果:")
    print(f"  最小值: {min(times):.3f}秒")
    print(f"  最大值: {max(times):.3f}秒")
    print(f"  平均值: {statistics.mean(times):.3f}秒")
    print(f"  中位数: {statistics.median(times):.3f}秒")
    if len(times) > 1:
        print(f"  标准差: {statistics.stdev(times):.3f}秒")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("LangServe API 使用示例")
    print("=" * 80)

    print("\n请选择要运行的示例:")
    print("1. Python基础示例")
    print("2. 流式调用示例")
    print("3. 批量请求示例")
    print("4. 错误处理示例")
    print("5. 性能测试示例")
    print("6. 查看JavaScript示例代码")
    print("7. 查看cURL示例命令")

    choice = input("\n请输入选项 (1-7): ").strip()

    if choice == "1":
        python_examples()
    elif choice == "2":
        streaming_example()
    elif choice == "3":
        batch_requests_example()
    elif choice == "4":
        error_handling_example()
    elif choice == "5":
        performance_test()
    elif choice == "6":
        print("\n" + "=" * 80)
        print("JavaScript/Node.js示例代码")
        print("=" * 80)
        print(JS_EXAMPLE)
    elif choice == "7":
        print("\n" + "=" * 80)
        print("cURL示例命令")
        print("=" * 80)
        print(CURL_EXAMPLES)
    else:
        print("无效的选项")
