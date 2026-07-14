"""
快速路由测试 - 验证所有路由分支
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.agents.intelligent_router import IntelligentRouter
from src.models.llm import get_llm
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

print("=" * 80)
print("快速路由测试 - 验证所有路由分支")
print("=" * 80)

# 准备测试数据
test_text = """
第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚

第三章 组织架构
1. 技术总监陈浩向副总经理李明汇报
2. 副总经理李明向总经理张建国汇报
3. 市场总监周静向副总经理王芳汇报
"""

print("\n[1/4] 初始化组件...")
llm = get_llm(temperature=0.3)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
documents = [Document(page_content=chunk) for chunk in text_splitter.split_text(test_text)]

embeddings = DashScopeEmbeddings(model="text-embedding-v1")
vectorstore = FAISS.from_documents(documents, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

router = IntelligentRouter(llm=llm, retriever=retriever)

print("[2/4] 组件初始化完成\n")

# 测试用例
test_cases = [
    {
        "name": "第零层：工具调用 - 天气查询",
        "query": "北京天气怎么样",
        "expected_route": "intent_weather",
        "description": "明确的天气查询意图，应触发工具调用"
    },
    {
        "name": "第零层：工具调用 - 航班查询",
        "query": "查询CA1234航班状态",
        "expected_route": "intent_flight",
        "description": "明确的航班查询意图，应触发工具调用"
    },
    {
        "name": "第一层：闲聊 - 问候",
        "query": "你好",
        "expected_route": "chitchat",
        "description": "简单问候，直接LLM回答"
    },
    {
        "name": "第一层：闲聊 - 感谢",
        "query": "谢谢",
        "expected_route": "chitchat",
        "description": "礼貌用语，直接LLM回答"
    },
    {
        "name": "第一层：图谱查询 - 汇报关系",
        "query": "陈浩向谁汇报",
        "expected_route": "graph",
        "description": "组织架构关系查询，使用GraphRAG"
    },
    {
        "name": "第一层：图谱查询 - 上级查询",
        "query": "李明的上级是谁",
        "expected_route": "graph",
        "description": "实体关系查询，使用GraphRAG"
    },
    {
        "name": "第二层：简单查询 - 政策查询",
        "query": "北京住宿标准是多少",
        "expected_route": "simple",
        "description": "单一事实查询，单次RAG检索"
    },
    {
        "name": "第二层：简单查询 - 城市列表",
        "query": "一线城市有哪些",
        "expected_route": "simple",
        "description": "列举类查询，单次RAG检索"
    },
]

print("[3/4] 开始测试路由...\n")

results = []
success_count = 0

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
    print(f"{'='*80}")
    print(f"查询: {test_case['query']}")
    print(f"预期路由: {test_case['expected_route']}")
    print(f"说明: {test_case['description']}")
    print(f"{'-'*80}")

    try:
        result = router.route(test_case['query'])
        actual_route = result["route"]
        latency = result["latency"]
        classification = result.get("classification", {})

        # 判断成功
        if test_case['expected_route'].startswith('intent_'):
            success = actual_route.startswith('intent_')
        else:
            success = (actual_route == test_case['expected_route'])

        if success:
            success_count += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"\n结果: {status}")
        print(f"  实际路由: {actual_route}")
        print(f"  延迟: {latency:.0f}ms")
        if classification:
            print(f"  分类类型: {classification.get('type', 'N/A')}")
            print(f"  置信度: {classification.get('confidence', 0):.2f}")

        results.append({
            "test": test_case['name'],
            "query": test_case['query'],
            "expected": test_case['expected_route'],
            "actual": actual_route,
            "success": success,
            "latency": latency
        })

    except Exception as e:
        print(f"\nERROR: {e}")
        results.append({
            "test": test_case['name'],
            "query": test_case['query'],
            "expected": test_case['expected_route'],
            "actual": "error",
            "success": False,
            "latency": 0
        })

# 打印汇总报告
print(f"\n\n{'='*80}")
print("[4/4] 测试结果汇总")
print(f"{'='*80}\n")

success_rate = (success_count / len(test_cases)) * 100
print(f"总测试数: {len(test_cases)}")
print(f"成功数: {success_count}")
print(f"成功率: {success_rate:.1f}%\n")

# 按路由类型分组
layer0 = [r for r in results if r['expected'].startswith('intent_')]
layer1_chat = [r for r in results if r['expected'] == 'chitchat']
layer1_graph = [r for r in results if r['expected'] == 'graph']
layer2_simple = [r for r in results if r['expected'] == 'simple']

print("分层统计:")
print(f"  第零层（工具调用）: {sum(1 for r in layer0 if r['success'])}/{len(layer0)}")
print(f"  第一层（闲聊）: {sum(1 for r in layer1_chat if r['success'])}/{len(layer1_chat)}")
print(f"  第一层（图谱）: {sum(1 for r in layer1_graph if r['success'])}/{len(layer1_graph)}")
print(f"  第二层（简单）: {sum(1 for r in layer2_simple if r['success'])}/{len(layer2_simple)}")

print(f"\n{'='*80}")
if success_rate >= 80:
    print(f"SUCCESS: 测试通过！成功率 {success_rate:.1f}% >= 80%")
else:
    print(f"WARNING: 成功率 {success_rate:.1f}% < 80%")
print(f"{'='*80}\n")

# 打印详细结果表格
print("\n详细结果:")
print(f"{'序号':<4} {'测试名称':<30} {'预期':<15} {'实际':<15} {'状态':<6}")
print("-" * 80)
for i, r in enumerate(results, 1):
    status = "PASS" if r['success'] else "FAIL"
    print(f"{i:<4} {r['test'][:28]:<30} {r['expected']:<15} {r['actual']:<15} {status:<6}")
