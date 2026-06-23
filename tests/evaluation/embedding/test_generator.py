"""
Embedding评估测试集生成器

生成17个查询 + 10个政策文档的测试数据集
难度分级: Easy(4) / Medium(7) / Hard(5) / Distractor(1)
"""

from typing import Dict, Any, List


def generate_test_set() -> Dict[str, Any]:
    """
    生成完整的评估测试集

    Returns:
        测试集字典，包含：
        - queries: 查询列表（17个）
        - documents: 文档列表（10个）
        - metadata: 元数据统计
    """

    # 10个政策文档
    documents = [
        {
            'id': 'D01',
            'text': '北京市、上海市、广州市、深圳市等一线城市出差住宿标准为500元/晚，超出部分需自行承担。'
        },
        {
            'id': 'D02',
            'text': '杭州市、成都市、武汉市、西安市等二线城市出差住宿标准为400元/晚。'
        },
        {
            'id': 'D03',
            'text': '三线及以下城市出差住宿标准为300元/晚，包括地级市和县级市。'
        },
        {
            'id': 'D04',
            'text': '市内交通费用实报实销，包括出租车、地铁、公交等合理交通工具，需提供发票。'
        },
        {
            'id': 'D05',
            'text': '城际交通标准：距离小于500公里使用高铁二等座，距离大于等于500公里可乘坐飞机经济舱。'
        },
        {
            'id': 'D06',
            'text': '国际出差需提前30天提交申请，经总经理批准后方可预订机票和酒店，住宿标准参考目的地国家物价水平。'
        },
        {
            'id': 'D07',
            'text': '出差补助标准：一线城市100元/天，二线城市80元/天，三线及以下城市60元/天，用于餐饮等杂费。'
        },
        {
            'id': 'D08',
            'text': '出差审批流程：预算低于5000元由部门经理审批，5000-10000元由总监审批，超过10000元由总经理审批。'
        },
        {
            'id': 'D09',
            'text': '发票报销要求：出差结束后7个工作日内提交报销单据，发票抬头必须是公司全称，缺失发票不予报销。'
        },
        {
            'id': 'D10',
            'text': '特殊情况处理：因航班延误、天气等不可抗力因素导致的额外住宿和餐饮费用，凭证明材料可全额报销。'
        }
    ]

    # 17个查询（按难度分级）
    queries = [
        # Easy (4个) - 直接关键词匹配
        {
            'id': 'Q01',
            'text': '北京出差住宿标准是多少',
            'expected_doc_id': 'D01',
            'difficulty': 'easy'
        },
        {
            'id': 'Q02',
            'text': '上海住宿费用标准',
            'expected_doc_id': 'D01',
            'difficulty': 'easy'
        },
        {
            'id': 'Q03',
            'text': '市内交通费用怎么报销',
            'expected_doc_id': 'D04',
            'difficulty': 'easy'
        },
        {
            'id': 'Q04',
            'text': '城际交通使用什么交通工具',
            'expected_doc_id': 'D05',
            'difficulty': 'easy'
        },

        # Medium (7个) - 同义词/语序变化
        {
            'id': 'Q05',
            'text': '去深圳出差酒店标准',
            'expected_doc_id': 'D01',
            'difficulty': 'medium'
        },
        {
            'id': 'Q06',
            'text': '成都的住宿费用上限',
            'expected_doc_id': 'D02',
            'difficulty': 'medium'
        },
        {
            'id': 'Q07',
            'text': '打车费用能报销吗',
            'expected_doc_id': 'D04',
            'difficulty': 'medium'
        },
        {
            'id': 'Q08',
            'text': '北京到上海怎么去',
            'expected_doc_id': 'D05',
            'difficulty': 'medium'
        },
        {
            'id': 'Q09',
            'text': '每天有出差补贴吗',
            'expected_doc_id': 'D07',
            'difficulty': 'medium'
        },
        {
            'id': 'Q10',
            'text': '发票有什么要求',
            'expected_doc_id': 'D09',
            'difficulty': 'medium'
        },
        {
            'id': 'Q11',
            'text': '预算8000元的出差谁审批',
            'expected_doc_id': 'D08',
            'difficulty': 'medium'
        },

        # Hard (5个) - 隐式推理/多跳
        {
            'id': 'Q12',
            'text': '去广州3天2晚住宿预算多少',
            'expected_doc_id': 'D01',
            'difficulty': 'hard'
        },
        {
            'id': 'Q13',
            'text': '武汉到杭州应该坐高铁还是飞机',
            'expected_doc_id': 'D05',
            'difficulty': 'hard'
        },
        {
            'id': 'Q14',
            'text': '去美国出差需要什么流程',
            'expected_doc_id': 'D06',
            'difficulty': 'hard'
        },
        {
            'id': 'Q15',
            'text': '航班取消了额外住一晚能报销吗',
            'expected_doc_id': 'D10',
            'difficulty': 'hard'
        },
        {
            'id': 'Q16',
            'text': '三线城市出差3天总预算包括住宿和补助',
            'expected_doc_id': 'D03',
            'difficulty': 'hard'
        },

        # Distractor (1个) - 不在文档中
        {
            'id': 'Q17',
            'text': '公司年假有多少天',
            'expected_doc_id': 'NONE',
            'difficulty': 'distractor'
        }
    ]

    # 元数据统计
    metadata = {
        'total_queries': len(queries),
        'total_documents': len(documents),
        'difficulty_distribution': {
            'easy': len([q for q in queries if q['difficulty'] == 'easy']),
            'medium': len([q for q in queries if q['difficulty'] == 'medium']),
            'hard': len([q for q in queries if q['difficulty'] == 'hard']),
            'distractor': len([q for q in queries if q['difficulty'] == 'distractor'])
        },
        'description': 'Embedding评估测试集 - 企业差旅政策问答'
    }

    return {
        'queries': queries,
        'documents': documents,
        'metadata': metadata
    }


def print_test_set_summary(test_set: Dict[str, Any]) -> None:
    """打印测试集摘要"""
    print("\n" + "=" * 60)
    print("Embedding评估测试集")
    print("=" * 60)

    metadata = test_set['metadata']
    print(f"\n总查询数: {metadata['total_queries']}")
    print(f"总文档数: {metadata['total_documents']}")

    print("\n难度分布:")
    for difficulty, count in metadata['difficulty_distribution'].items():
        pct = count / metadata['total_queries'] * 100
        print(f"  {difficulty:12s}: {count:2d} ({pct:5.1f}%)")

    print("\n查询样例:")
    for difficulty in ['easy', 'medium', 'hard', 'distractor']:
        sample = next((q for q in test_set['queries'] if q['difficulty'] == difficulty), None)
        if sample:
            print(f"  [{difficulty:10s}] {sample['text']} → {sample['expected_doc_id']}")

    print("\n文档样例:")
    for doc in test_set['documents'][:3]:
        preview = doc['text'][:50] + '...' if len(doc['text']) > 50 else doc['text']
        print(f"  {doc['id']}: {preview}")

    print("=" * 60)


# 测试代码
if __name__ == "__main__":
    test_set = generate_test_set()
    print_test_set_summary(test_set)

    # 验证数据完整性
    print("\n数据完整性检查:")
    assert len(test_set['queries']) == 17, "查询数量应为17个"
    assert len(test_set['documents']) == 10, "文档数量应为10个"
    assert test_set['metadata']['total_queries'] == 17

    # 检查expected_doc_id是否都存在（除了NONE）
    doc_ids = {doc['id'] for doc in test_set['documents']}
    doc_ids.add('NONE')
    for query in test_set['queries']:
        assert query['expected_doc_id'] in doc_ids, f"查询 {query['id']} 的预期文档ID不存在"

    print("[ OK ] 所有检查通过")
