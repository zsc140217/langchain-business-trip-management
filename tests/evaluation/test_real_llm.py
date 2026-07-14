"""
真实 LLM 环境性能测试
验证三层路由架构完整功能（包含 GraphRAG）

测试覆盖：
- 第零层：工具调用拦截
- 第一层：Self-RAG（CHITCHAT）+ GraphRAG（GRAPH）分类
- 第二层：复杂度评估（SIMPLE/COMPLEX）
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from src.agents.intelligent_router import IntelligentRouter
from src.models.llm import get_llm
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 确保有真实 API Key
if not os.getenv("DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY") == "test_key":
    print("错误：需要真实的 DASHSCOPE_API_KEY")
    print("请设置: export DASHSCOPE_API_KEY='sk-xxx'")
    sys.exit(1)

# 设置默认 BASE_URL（如果未设置）
if not os.getenv("DASHSCOPE_BASE_URL"):
    os.environ["DASHSCOPE_BASE_URL"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

print("=" * 70)
print("[测试] 真实 LLM 环境 - 三层路由架构验证")
print("=" * 70)

# 准备测试数据
test_text = """
企业差旅管理规章

第一章 住宿标准
1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚
2. 二线城市（杭州、成都、武汉等）：标准间不超过400元/晚
3. 三线及以下城市：标准间不超过300元/晚

第二章 交通标准
1. 市内交通：实报实销，需提供发票
2. 城际交通：
   - 距离<500公里：高铁二等座
   - 距离≥500公里：飞机经济舱

第三章 组织架构
1. 技术总监陈浩向CTO李明汇报
2. CTO李明向CEO张建国汇报
3. 副总向CEO汇报
4. 总监向副总汇报

第四章 办公室分布
公司在北京、上海、广州、深圳、杭州设有办公室
"""

# 初始化组件
print("\n[初始化] 创建 LLM 和检索器...")
llm = get_llm(temperature=0.3)

# 创建文档
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
documents = [Document(page_content=chunk) for chunk in text_splitter.split_text(test_text)]

# 创建向量存储
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings(model="text-embedding-v1")
vectorstore = FAISS.from_documents(documents, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 创建智能路由器
print("[初始化] 创建智能路由器...")
router = IntelligentRouter(
    llm=llm,
    retriever=retriever
)

# 测试数据集（包含 GraphRAG 测试）
test_queries = [
    # 第零层（工具调用）- 3条
    ("北京天气怎么样", "layer0_intent"),
    ("查询CA1234航班状态", "layer0_intent"),
    ("推荐附近的协议酒店", "layer0_intent"),

    # 第一层（闲聊）- 3条
    ("你好", "layer1_chitchat"),
    ("谢谢", "layer1_chitchat"),
    ("今天星期几", "layer1_chitchat"),

    # 第一层（图谱查询 GRAPH）- 4条 ⭐ 新增
    ("陈浩向谁汇报", "layer1_graph"),
    ("李明的上级是谁", "layer1_graph"),
    ("总监和副总的汇报关系", "layer1_graph"),
    ("公司组织架构中谁向CEO汇报", "layer1_graph"),

    # 第二层SIMPLE - 2条
    ("北京住宿标准是多少", "layer2_simple"),
    ("一线城市有哪些", "layer2_simple"),

    # 第二层COMPLEX - 1条
    ("去杭州出差，查天气并推荐酒店", "layer2_complex"),
]

print(f"\n[测试] 开始执行 {len(test_queries)} 条测试查询...\n")

# 运行测试
results = []
for i, (query, expected_layer) in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"[{i}/{len(test_queries)}] 测试查询: {query}")
    print(f"预期层级: {expected_layer}")
    print(f"{'='*70}")

    try:
        result = router.route(query)

        actual_route = result["route"]
        latency = result["latency"]

        # 判断成功
        success = False
        if expected_layer == "layer0_intent" and actual_route.startswith("intent_"):
            success = True
        elif expected_layer == "layer1_chitchat" and actual_route == "chitchat":
            success = True
        elif expected_layer == "layer1_graph" and actual_route == "graph":
            success = True
        elif expected_layer == "layer2_simple" and actual_route == "simple":
            success = True
        elif expected_layer == "layer2_complex" and actual_route == "complex":
            success = True

        results.append({
            "query": query,
            "expected": expected_layer,
            "actual": actual_route,
            "latency": latency,
            "success": success
        })

        status = "[OK] 成功" if success else "[FAIL] 失败"
        print(f"\n{status}")
        print(f"  实际路由: {actual_route}")
        print(f"  延迟: {latency:.0f}ms")

    except Exception as e:
        print(f"\n[ERROR] 异常: {e}")
        results.append({
            "query": query,
            "expected": expected_layer,
            "actual": "error",
            "latency": 0,
            "success": False
        })

# 打印统计报告
print(f"\n\n{'='*70}")
print("[报告] 测试结果汇总")
print(f"{'='*70}\n")

total = len(results)
success_count = sum(1 for r in results if r["success"])
success_rate = success_count / total * 100

print(f"总查询数: {total}")
print(f"成功数: {success_count}")
print(f"成功率: {success_rate:.1f}%")

# 按层级统计
layer0_results = [r for r in results if r["expected"] == "layer0_intent"]
layer1_chitchat_results = [r for r in results if r["expected"] == "layer1_chitchat"]
layer1_graph_results = [r for r in results if r["expected"] == "layer1_graph"]
layer2_simple_results = [r for r in results if r["expected"] == "layer2_simple"]
layer2_complex_results = [r for r in results if r["expected"] == "layer2_complex"]

print(f"\n分层统计:")
print(f"  第零层（意图识别）: {sum(1 for r in layer0_results if r['success'])}/{len(layer0_results)}")
print(f"  第一层（Self-RAG闲聊）: {sum(1 for r in layer1_chitchat_results if r['success'])}/{len(layer1_chitchat_results)}")
print(f"  第一层（GraphRAG图谱）: {sum(1 for r in layer1_graph_results if r['success'])}/{len(layer1_graph_results)}")
print(f"  第二层SIMPLE: {sum(1 for r in layer2_simple_results if r['success'])}/{len(layer2_simple_results)}")
print(f"  第二层COMPLEX: {sum(1 for r in layer2_complex_results if r['success'])}/{len(layer2_complex_results)}")

# 打印智能路由器统计
print()
router.print_stats()

print(f"\n{'='*70}")
if success_rate >= 80:
    print("[OK] 测试通过！三层路由架构工作正常")
else:
    print(f"[WARNING] 成功率 {success_rate:.1f}% 低于预期 80%")
print(f"{'='*70}\n")
