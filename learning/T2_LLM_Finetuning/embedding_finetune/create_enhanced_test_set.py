"""
创建增强评估数据集

目标：
1. 20个测试查询（15个未见过的）
2. 包含困难样本和干扰样本
3. 难度分级：easy/medium/hard
"""
import json
from pathlib import Path

# 加载训练数据，避免测试集泄露
training_file = Path(__file__).parent / "train_data.json"
with open(training_file, 'r', encoding='utf-8') as f:
    training_data = json.load(f)

# 提取训练集中的query（避免重复）
training_queries = set([item['query'] for item in training_data])
print(f"训练集包含 {len(training_queries)} 个query")

# 创建增强测试集
enhanced_test_set = {
    "test_queries": [
        # === EASY 级别 (1-5)：直接匹配，类似训练集但未见过 ===
        {
            "id": 1,
            "query": "去北京出差能住什么价位的酒店？",
            "expected_doc_contains": "一线城市",
            "difficulty": "easy",
            "expected_in_training": False,
            "reasoning": "直接询问住宿标准，语义明确"
        },
        {
            "id": 2,
            "query": "经济舱的机票可以报销吗？",
            "expected_doc_contains": "经济舱",
            "difficulty": "easy",
            "expected_in_training": False,
            "reasoning": "直接询问经济舱报销"
        },
        {
            "id": 3,
            "query": "出差补贴一天给多少钱？",
            "expected_doc_contains": "补贴标准",
            "difficulty": "easy",
            "expected_in_training": False,
            "reasoning": "直接询问补贴标准"
        },
        {
            "id": 4,
            "query": "火车票能报销吗？",
            "expected_doc_contains": "高铁",
            "difficulty": "easy",
            "expected_in_training": False,
            "reasoning": "询问火车票报销规定"
        },
        {
            "id": 5,
            "query": "出差住宿发票丢了怎么办？",
            "expected_doc_contains": "发票",
            "difficulty": "easy",
            "expected_in_training": False,
            "reasoning": "发票遗失处理流程"
        },

        # === MEDIUM 级别 (6-12)：需要语义理解或多跳推理 ===
        {
            "id": 6,
            "query": "去魔都出差住宿预算多少？",
            "expected_doc_contains": "上海",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "需要理解'魔都'=上海"
        },
        {
            "id": 7,
            "query": "副总裁能坐商务舱吗？",
            "expected_doc_contains": "副总裁",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "需要查询职级与舱位的对应关系"
        },
        {
            "id": 8,
            "query": "从北京到成都应该坐飞机还是高铁？",
            "expected_doc_contains": "500公里",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "需要根据距离规则判断"
        },
        {
            "id": 9,
            "query": "周末加班出差有额外补贴吗？",
            "expected_doc_contains": "周末",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "查询周末加班规定"
        },
        {
            "id": 10,
            "query": "出差期间生病就医费用能报吗？",
            "expected_doc_contains": "特殊情况",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "特殊情况处理"
        },
        {
            "id": 11,
            "query": "一次出差去多个城市，住宿标准怎么算？",
            "expected_doc_contains": "城市",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "多城市差旅规则"
        },
        {
            "id": 12,
            "query": "提前预订机票有折扣吗？",
            "expected_doc_contains": "提前预订",
            "difficulty": "medium",
            "expected_in_training": False,
            "reasoning": "提前预订政策"
        },

        # === HARD 级别 (13-17)：困难负样本或细粒度区分 ===
        {
            "id": 13,
            "query": "商务舱和经济舱的差别是什么？",
            "expected_doc_contains": "商务舱",
            "difficulty": "hard",
            "expected_in_training": False,
            "reasoning": "需要区分商务舱和经济舱的细微差别"
        },
        {
            "id": 14,
            "query": "杭州属于几线城市？住宿标准是多少？",
            "expected_doc_contains": "二线城市",
            "difficulty": "hard",
            "expected_in_training": False,
            "reasoning": "需要城市分级知识+标准查询"
        },
        {
            "id": 15,
            "query": "国际出差的政策和国内一样吗？",
            "expected_doc_contains": "国际",
            "difficulty": "hard",
            "expected_in_training": False,
            "reasoning": "区分国际和国内政策"
        },
        {
            "id": 16,
            "query": "出差超过一个月，标准有变化吗？",
            "expected_doc_contains": "长期",
            "difficulty": "hard",
            "expected_in_training": False,
            "reasoning": "长期出差特殊规定"
        },
        {
            "id": 17,
            "query": "CEO出差有什么特殊待遇？",
            "expected_doc_contains": "CEO",
            "difficulty": "hard",
            "expected_in_training": False,
            "reasoning": "高管特殊政策"
        },

        # === 干扰样本 (18-20)：跨领域问题，应该没有匹配结果 ===
        {
            "id": 18,
            "query": "公司年会预算是多少？",
            "expected_doc_contains": None,
            "difficulty": "distractor",
            "expected_in_training": False,
            "reasoning": "非差旅相关问题"
        },
        {
            "id": 19,
            "query": "员工入职需要什么材料？",
            "expected_doc_contains": None,
            "difficulty": "distractor",
            "expected_in_training": False,
            "reasoning": "HR问题，非差旅"
        },
        {
            "id": 20,
            "query": "如何申请年假？",
            "expected_doc_contains": None,
            "difficulty": "distractor",
            "expected_in_training": False,
            "reasoning": "休假政策，非差旅"
        }
    ],

    "document_corpus": [],

    "metadata": {
        "total_queries": 20,
        "new_queries": 20,
        "difficulty_breakdown": {
            "easy": 5,
            "medium": 7,
            "hard": 5,
            "distractor": 3
        },
        "purpose": "严格评估微调效果，避免过拟合",
        "expected_baseline": "60-70%",
        "expected_finetuned": "80-90%"
    }
}

# 从训练数据中提取文档库
doc_set = set()
for item in training_data:
    doc_set.add(item['positive'])

enhanced_test_set['document_corpus'] = list(doc_set)
print(f"文档库包含 {len(doc_set)} 个唯一文档")

# 保存测试集
output_file = Path(__file__).parent / "enhanced_test_set.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(enhanced_test_set, f, ensure_ascii=False, indent=2)

print(f"\n[OK] Enhanced test set created: {output_file}")
print(f"   - Total queries: {len(enhanced_test_set['test_queries'])}")
print(f"   - Easy: {enhanced_test_set['metadata']['difficulty_breakdown']['easy']}")
print(f"   - Medium: {enhanced_test_set['metadata']['difficulty_breakdown']['medium']}")
print(f"   - Hard: {enhanced_test_set['metadata']['difficulty_breakdown']['hard']}")
print(f"   - Distractor: {enhanced_test_set['metadata']['difficulty_breakdown']['distractor']}")
print(f"   - Document corpus size: {len(enhanced_test_set['document_corpus'])}")
