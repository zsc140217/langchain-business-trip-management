"""
LLM-as-Judge 基础模块 - 使用LLM评估系统输出质量
"""
import os
import json
from typing import Dict, Optional
import requests
from .cost_tracker import get_tracker


class LLMJudge:
    """LLM评判器基类"""

    def __init__(self, model: str = 'qwen-max'):
        self.model = model
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.base_url = os.getenv(
            'DASHSCOPE_BASE_URL',
            'https://dashscope.aliyuncs.com/compatible-mode/v1'
        )

        if not self.api_key:
            raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    def judge(
        self,
        prompt: str,
        purpose: str = "evaluation"
    ) -> Dict:
        """
        调用LLM进行评判

        Args:
            prompt: 评判提示词
            purpose: 评估目的（用于成本追踪）

        Returns:
            {
                'score': int (1-5),
                'reasoning': str,
                'raw_response': str
            }
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一个专业的RAG系统评估专家。请严格按照要求进行评分，并给出详细理由。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.1,  # 降低随机性，保证评分稳定
            'response_format': {'type': 'json_object'}  # 强制JSON输出
        }

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 提取tokens信息
            usage = result.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)

            # 记录成本
            tracker = get_tracker()
            tracker.record_call(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                purpose=purpose
            )

            # 解析响应
            content = result['choices'][0]['message']['content']
            parsed = json.loads(content)

            return {
                'score': parsed.get('score', 3),
                'reasoning': parsed.get('reasoning', ''),
                'raw_response': content
            }

        except Exception as e:
            print(f"LLM调用失败: {str(e)}")
            return {
                'score': 3,
                'reasoning': f'评估失败: {str(e)}',
                'raw_response': ''
            }

    def judge_with_criteria(
        self,
        query: str,
        system_output: str,
        criteria: str,
        purpose: str = "evaluation"
    ) -> Dict:
        """
        根据特定标准评判

        Args:
            query: 用户问题
            system_output: 系统输出
            criteria: 评判标准
            purpose: 评估目的

        Returns:
            评判结果
        """
        prompt = f"""
请评估以下系统输出的质量。

**用户问题**:
{query}

**系统回答**:
{system_output}

**评判标准**:
{criteria}

请按照1-5分进行评分，并给出详细理由。

返回JSON格式:
{{
  "score": 评分 (1-5的整数),
  "reasoning": "评分理由，必须具体说明优点和不足"
}}
"""
        return self.judge(prompt, purpose)


# 全局单例
_judge = None


def get_judge(model: str = 'qwen-max') -> LLMJudge:
    """获取全局LLM评判器"""
    global _judge
    if _judge is None:
        _judge = LLMJudge(model)
    return _judge
