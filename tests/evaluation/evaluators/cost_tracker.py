"""
成本追踪器 - 记录评测过程中的LLM调用成本
"""
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class APICall:
    """单次API调用记录"""
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cny: float
    purpose: str  # 用于什么评估维度


class CostTracker:
    """成本追踪器"""

    # 模型定价（人民币/1K tokens）
    PRICING = {
        'qwen-max': {'input': 0.04, 'output': 0.12},
        'qwen-plus': {'input': 0.002, 'output': 0.006},
        'qwen-turbo': {'input': 0.0008, 'output': 0.002},
        'gpt-4': {'input': 0.21, 'output': 0.63},
        'gpt-3.5-turbo': {'input': 0.01, 'output': 0.02}
    }

    def __init__(self):
        self.calls: List[APICall] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def record_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        purpose: str = "evaluation"
    ):
        """记录一次API调用"""
        pricing = self.PRICING.get(model, self.PRICING['qwen-max'])

        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        total_cost = input_cost + output_cost

        call = APICall(
            timestamp=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cny=round(total_cost, 4),
            purpose=purpose
        )

        self.calls.append(call)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += total_cost

    def get_summary(self) -> Dict:
        """获取成本汇总"""
        return {
            'total_calls': len(self.calls),
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'total_cost_cny': round(self.total_cost, 2),
            'avg_cost_per_call': round(self.total_cost / len(self.calls), 4) if self.calls else 0,
            'breakdown_by_purpose': self._breakdown_by_purpose()
        }

    def _breakdown_by_purpose(self) -> Dict:
        """按评估目的分组统计"""
        breakdown = {}
        for call in self.calls:
            if call.purpose not in breakdown:
                breakdown[call.purpose] = {
                    'calls': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            breakdown[call.purpose]['calls'] += 1
            breakdown[call.purpose]['tokens'] += call.input_tokens + call.output_tokens
            breakdown[call.purpose]['cost'] += call.cost_cny

        # 格式化
        for purpose in breakdown:
            breakdown[purpose]['cost'] = round(breakdown[purpose]['cost'], 2)

        return breakdown

    def export_to_file(self, filepath: str):
        """导出详细记录到文件"""
        import json

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': self.get_summary(),
                'calls': [vars(call) for call in self.calls]
            }, f, ensure_ascii=False, indent=2)


# 全局单例
_tracker = CostTracker()


def get_tracker() -> CostTracker:
    """获取全局成本追踪器"""
    return _tracker
