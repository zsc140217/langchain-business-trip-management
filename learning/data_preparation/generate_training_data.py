# generate_training_data.py
"""
任务2.2：生成训练数据
使用LLM为每个政策段落生成口语化问题
"""
import json
import os
from anthropic import Anthropic

def generate_mock_data(policy_docs, num_queries_per_doc=3, max_docs=50):
    """
    生成模拟训练数据（用于演示）
    """
    training_data = []
    docs_to_process = policy_docs[:max_docs]

    print(f"使用mock模式处理 {len(docs_to_process)} 个文档...")

    # 预定义的问题模板
    templates = [
        "关于{topic}的标准是什么？",
        "{topic}有什么具体要求？",
        "请问{topic}的规定是怎样的？",
    ]

    for idx, doc in enumerate(docs_to_process, 1):
        # 简单提取关键词作为topic
        if "住宿" in doc:
            topic = "住宿"
        elif "交通" in doc or "飞机" in doc or "高铁" in doc:
            topic = "交通"
        elif "餐费" in doc:
            topic = "餐费"
        elif "报销" in doc:
            topic = "报销"
        elif "补贴" in doc:
            topic = "补贴"
        else:
            topic = "差旅"

        # 生成问题
        queries = [template.format(topic=topic) for template in templates[:num_queries_per_doc]]

        for query in queries:
            training_data.append({
                "query": query,
                "positive": doc,
                "negatives": []
            })

        if idx % 10 == 0:
            print(f"  处理进度: {idx}/{len(docs_to_process)}")

    return training_data

def generate_training_data(policy_docs, num_queries_per_doc=3, max_docs=50):
    """
    为政策文档生成训练数据

    Args:
        policy_docs: 政策文档列表
        num_queries_per_doc: 每个文档生成的问题数量
        max_docs: 处理的最大文档数量
    """
    # 初始化Anthropic客户端 - 尝试多种环境变量
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

    if not api_key:
        print("[WARN] 未找到 ANTHROPIC_API_KEY 或 CLAUDE_API_KEY")
        print("[INFO] 使用mock数据生成示例（实际应用中需要API密钥）")
        return generate_mock_data(policy_docs, num_queries_per_doc, max_docs)

    client = Anthropic(api_key=api_key)

    training_data = []
    docs_to_process = policy_docs[:max_docs]

    print(f"开始处理 {len(docs_to_process)} 个文档...")

    for idx, doc in enumerate(docs_to_process, 1):
        print(f"\n[{idx}/{len(docs_to_process)}] 处理文档: {doc[:50]}...")

        prompt = f"""基于以下差旅政策，生成{num_queries_per_doc}个用户可能会问的口语化问题。
问题应该自然、口语化，就像员工真实咨询时会问的那样。

政策内容：
{doc}

请直接返回JSON格式，不要有任何其他文字：
{{"queries": ["问题1", "问题2", "问题3"]}}"""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # 提取响应内容
            content = response.content[0].text.strip()

            # 尝试解析JSON
            try:
                result = json.loads(content)
                queries = result.get('queries', [])
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    queries = result.get('queries', [])
                else:
                    print(f"  [WARN] 无法解析响应: {content[:100]}")
                    continue

            # 添加到训练数据
            for query in queries:
                training_data.append({
                    "query": query,
                    "positive": doc,
                    "negatives": []  # 稍后通过Hard Negative Mining添加
                })

            print(f"  [SUCCESS] 生成 {len(queries)} 个问题")

        except Exception as e:
            print(f"  [ERROR] 处理失败: {e}")
            continue

    return training_data

if __name__ == "__main__":
    print("="*60)
    print("任务2.2：生成训练数据")
    print("="*60)

    # 读取政策文档
    input_file = "policy_docs.json"
    if not os.path.exists(input_file):
        print(f"[ERROR] 找不到 {input_file}")
        print("请先运行 extract_policies.py")
        exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    print(f"\n读取到 {len(docs)} 个政策段落")

    # 生成训练数据
    training_data = generate_training_data(docs, num_queries_per_doc=3, max_docs=50)

    if training_data:
        output_file = "training_data_raw.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)

        print(f"\n[SUCCESS] 成功生成 {len(training_data)} 条训练数据")
        print(f"[SUCCESS] 保存到: {output_file}")

        # 显示前2个示例
        print("\n前2个示例:")
        for i, item in enumerate(training_data[:2], 1):
            print(f"\n{i}. Query: {item['query']}")
            print(f"   Positive: {item['positive'][:80]}...")
    else:
        print("\n[ERROR] 未生成任何训练数据")
