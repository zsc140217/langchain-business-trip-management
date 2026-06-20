#!/usr/bin/env python3
"""
RAGAS Test Dataset Generator for Business Trip Management RAG System

This script generates synthetic test data for evaluating the RAG system using RAGAS framework.
It analyzes the knowledge base documents and creates diverse test questions with reference answers.

Distribution:
- 30% Simple questions (direct queries)
- 40% Medium questions (context understanding)
- 20% Reasoning questions (multi-step reasoning)
- 10% Multi-context questions (synthesizing multiple documents)
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

try:
    from langchain_community.chat_models import ChatTongyi
except ImportError:
    from langchain_community.llms import Tongyi as ChatTongyi

# Load environment variables
load_dotenv()


@dataclass
class TestCase:
    """Single test case for RAG evaluation"""
    question: str
    reference_answer: str
    contexts: List[str]
    difficulty: str  # simple|medium|reasoning|multi_context

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TestDatasetGenerator:
    """Generate test dataset based on knowledge base content"""

    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.llm = ChatTongyi(
            model="qwen-plus",
            temperature=0.7,
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        self.docs_content = {}

    def load_knowledge_base(self) -> Dict[str, str]:
        """Load all documents from knowledge base"""
        print("📚 Loading knowledge base documents...")

        # Load travel policy
        travel_policy_path = self.knowledge_base_path / "travel_policy.txt"
        if travel_policy_path.exists():
            with open(travel_policy_path, 'r', encoding='utf-8') as f:
                self.docs_content['travel_policy'] = f.read()

        # Load documentation files
        docs_dir = self.knowledge_base_path.parent / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.md"):
                with open(doc_file, 'r', encoding='utf-8') as f:
                    self.docs_content[doc_file.stem] = f.read()

        # Load comprehensive research docs
        research_dir = docs_dir / "comprehensive-research"
        if research_dir.exists():
            for doc_file in research_dir.glob("*.md"):
                with open(doc_file, 'r', encoding='utf-8') as f:
                    self.docs_content[f"research_{doc_file.stem}"] = f.read()

        print(f"✅ Loaded {len(self.docs_content)} documents")
        return self.docs_content

    def generate_simple_questions(self, num_questions: int = 15) -> List[TestCase]:
        """Generate simple direct query questions (30%)"""
        print(f"\n🎯 Generating {num_questions} simple questions...")

        prompt = PromptTemplate(
            input_variables=["document_name", "document_content"],
            template="""基于以下文档内容，生成{num}个简单的直接查询问题。这些问题应该能够通过文档中的单一事实直接回答。

文档名称: {document_name}
文档内容:
{document_content}

要求:
1. 问题应该清晰、具体
2. 答案可以从文档中直接找到
3. 不需要复杂推理
4. 每个问题附带准确的参考答案和相关上下文

请生成JSON格式的输出，格式如下:
[
  {{
    "question": "问题文本",
    "reference_answer": "参考答案",
    "context": "相关的文档片段"
  }}
]

生成{num}个问题:"""
        )

        test_cases = []

        # Generate from travel policy
        if 'travel_policy' in self.docs_content:
            questions_data = self._generate_with_llm(
                prompt.format(
                    num=8,
                    document_name="企业差旅管理规章",
                    document_content=self.docs_content['travel_policy'][:2000]
                )
            )
            for q in questions_data[:8]:
                test_cases.append(TestCase(
                    question=q['question'],
                    reference_answer=q['reference_answer'],
                    contexts=[q['context']],
                    difficulty='simple'
                ))

        # Generate from other docs
        doc_keys = [k for k in self.docs_content.keys() if k != 'travel_policy'][:2]
        for doc_key in doc_keys:
            questions_data = self._generate_with_llm(
                prompt.format(
                    num=4,
                    document_name=doc_key,
                    document_content=self.docs_content[doc_key][:2000]
                )
            )
            for q in questions_data[:4]:
                test_cases.append(TestCase(
                    question=q['question'],
                    reference_answer=q['reference_answer'],
                    contexts=[q['context']],
                    difficulty='simple'
                ))

        print(f"✅ Generated {len(test_cases)} simple questions")
        return test_cases[:num_questions]

    def generate_medium_questions(self, num_questions: int = 20) -> List[TestCase]:
        """Generate medium complexity questions requiring context understanding (40%)"""
        print(f"\n🎯 Generating {num_questions} medium questions...")

        prompt = PromptTemplate(
            input_variables=["document_content"],
            template="""基于以下文档内容，生成{num}个中等难度的问题。这些问题需要理解上下文、比较信息或进行简单分析。

文档内容:
{document_content}

要求:
1. 问题需要理解文档的上下文含义
2. 可能需要比较多个信息点
3. 需要一定的分析能力
4. 答案不是简单的事实陈述

请生成JSON格式的输出:
[
  {{
    "question": "问题文本",
    "reference_answer": "参考答案",
    "context": "相关的文档片段"
  }}
]

生成{num}个问题:"""
        )

        test_cases = []

        # Generate from multiple documents
        doc_keys = list(self.docs_content.keys())[:4]
        per_doc = num_questions // len(doc_keys)

        for doc_key in doc_keys:
            questions_data = self._generate_with_llm(
                prompt.format(
                    num=per_doc,
                    document_content=self.docs_content[doc_key][:3000]
                )
            )
            for q in questions_data[:per_doc]:
                test_cases.append(TestCase(
                    question=q['question'],
                    reference_answer=q['reference_answer'],
                    contexts=[q['context']],
                    difficulty='medium'
                ))

        print(f"✅ Generated {len(test_cases)} medium questions")
        return test_cases[:num_questions]

    def generate_reasoning_questions(self, num_questions: int = 10) -> List[TestCase]:
        """Generate reasoning questions requiring multi-step inference (20%)"""
        print(f"\n🎯 Generating {num_questions} reasoning questions...")

        prompt = PromptTemplate(
            input_variables=["document_content"],
            template="""基于以下文档内容，生成{num}个需要推理的问题。这些问题需要多步骤推理、逻辑判断或综合分析。

文档内容:
{document_content}

要求:
1. 问题需要多步骤推理
2. 需要逻辑判断或因果分析
3. 可能需要计算或比较
4. 答案需要解释推理过程

请生成JSON格式的输出:
[
  {{
    "question": "问题文本",
    "reference_answer": "参考答案（包含推理过程）",
    "context": "相关的文档片段"
  }}
]

生成{num}个问题:"""
        )

        test_cases = []

        # Focus on policy and technical docs
        reasoning_docs = ['travel_policy', 'SPRING_AI_VS_LANGCHAIN', 'RAG_EVALUATION_GUIDE']
        available_docs = [k for k in reasoning_docs if k in self.docs_content]

        per_doc = num_questions // max(len(available_docs), 1)

        for doc_key in available_docs:
            questions_data = self._generate_with_llm(
                prompt.format(
                    num=per_doc + 2,
                    document_content=self.docs_content[doc_key][:3000]
                )
            )
            for q in questions_data[:per_doc + 2]:
                test_cases.append(TestCase(
                    question=q['question'],
                    reference_answer=q['reference_answer'],
                    contexts=[q['context']],
                    difficulty='reasoning'
                ))

        print(f"✅ Generated {len(test_cases)} reasoning questions")
        return test_cases[:num_questions]

    def generate_multi_context_questions(self, num_questions: int = 5) -> List[TestCase]:
        """Generate questions requiring synthesis from multiple documents (10%)"""
        print(f"\n🎯 Generating {num_questions} multi-context questions...")

        prompt = PromptTemplate(
            input_variables=["doc1_name", "doc1_content", "doc2_name", "doc2_content"],
            template="""基于以下两个文档的内容，生成{num}个需要综合多个文档信息的问题。

文档1: {doc1_name}
{doc1_content}

文档2: {doc2_name}
{doc2_content}

要求:
1. 问题需要综合两个文档的信息
2. 可能需要对比、关联或整合信息
3. 答案需要引用多个文档
4. 体现跨文档的知识整合能力

请生成JSON格式的输出:
[
  {{
    "question": "问题文本",
    "reference_answer": "参考答案（综合两个文档）",
    "context1": "文档1相关片段",
    "context2": "文档2相关片段"
  }}
]

生成{num}个问题:"""
        )

        test_cases = []

        # Document pairs for multi-context questions
        doc_pairs = [
            ('travel_policy', 'SPRING_AI_VS_LANGCHAIN'),
            ('RAG_EVALUATION_GUIDE', 'SPRING_AI_ANALYSIS'),
            ('INTERVIEW_CHEAT_SHEET', 'FRAMEWORK_RESEARCH_REPORT'),
        ]

        available_pairs = [
            (d1, d2) for d1, d2 in doc_pairs
            if d1 in self.docs_content and d2 in self.docs_content
        ]

        per_pair = num_questions // max(len(available_pairs), 1)

        for doc1_key, doc2_key in available_pairs:
            questions_data = self._generate_with_llm(
                prompt.format(
                    num=per_pair + 1,
                    doc1_name=doc1_key,
                    doc1_content=self.docs_content[doc1_key][:2000],
                    doc2_name=doc2_key,
                    doc2_content=self.docs_content[doc2_key][:2000]
                )
            )
            for q in questions_data[:per_pair + 1]:
                contexts = [q.get('context1', ''), q.get('context2', '')]
                contexts = [c for c in contexts if c]  # Filter empty contexts
                if not contexts:
                    contexts = [q.get('context', '')]

                test_cases.append(TestCase(
                    question=q['question'],
                    reference_answer=q['reference_answer'],
                    contexts=contexts,
                    difficulty='multi_context'
                ))

        print(f"✅ Generated {len(test_cases)} multi-context questions")
        return test_cases[:num_questions]

    def _generate_with_llm(self, prompt: str) -> List[Dict[str, str]]:
        """Helper method to generate questions using LLM"""
        try:
            response = self.llm.invoke(prompt)
            content = response.content

            # Extract JSON from response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                questions = json.loads(json_str)
                return questions
            else:
                print(f"⚠️  Warning: Could not parse LLM response as JSON")
                return []

        except Exception as e:
            print(f"⚠️  Warning: LLM generation failed: {e}")
            return []

    def generate_full_dataset(self, total_questions: int = 50) -> List[TestCase]:
        """Generate complete test dataset with specified distribution"""
        print(f"\n🚀 Generating complete test dataset ({total_questions} questions)...")
        print(f"Distribution:")
        print(f"  - Simple: {int(total_questions * 0.3)} (30%)")
        print(f"  - Medium: {int(total_questions * 0.4)} (40%)")
        print(f"  - Reasoning: {int(total_questions * 0.2)} (20%)")
        print(f"  - Multi-context: {int(total_questions * 0.1)} (10%)")

        # Load knowledge base
        self.load_knowledge_base()

        # Generate questions by difficulty
        all_test_cases = []

        all_test_cases.extend(
            self.generate_simple_questions(int(total_questions * 0.3))
        )
        all_test_cases.extend(
            self.generate_medium_questions(int(total_questions * 0.4))
        )
        all_test_cases.extend(
            self.generate_reasoning_questions(int(total_questions * 0.2))
        )
        all_test_cases.extend(
            self.generate_multi_context_questions(int(total_questions * 0.1))
        )

        print(f"\n✅ Total generated: {len(all_test_cases)} test cases")
        return all_test_cases

    def save_dataset(self, test_cases: List[TestCase], output_path: str):
        """Save test dataset to JSON file"""
        print(f"\n💾 Saving dataset to {output_path}...")

        # Convert to dict format
        dataset = {
            "metadata": {
                "total_questions": len(test_cases),
                "distribution": {
                    "simple": len([tc for tc in test_cases if tc.difficulty == 'simple']),
                    "medium": len([tc for tc in test_cases if tc.difficulty == 'medium']),
                    "reasoning": len([tc for tc in test_cases if tc.difficulty == 'reasoning']),
                    "multi_context": len([tc for tc in test_cases if tc.difficulty == 'multi_context'])
                },
                "knowledge_base_documents": list(self.docs_content.keys())
            },
            "test_cases": [tc.to_dict() for tc in test_cases]
        }

        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        print(f"✅ Dataset saved successfully!")
        print(f"\n📊 Dataset Statistics:")
        print(f"  Total questions: {dataset['metadata']['total_questions']}")
        for difficulty, count in dataset['metadata']['distribution'].items():
            percentage = (count / dataset['metadata']['total_questions']) * 100
            print(f"  - {difficulty}: {count} ({percentage:.1f}%)")


def main():
    """Main execution function"""
    print("=" * 60)
    print("RAG Test Dataset Generator")
    print("=" * 60)

    # Configuration
    project_root = Path(__file__).parent.parent.parent
    knowledge_base_path = project_root / "data"
    output_path = project_root / "tests" / "evaluation" / "test_dataset.json"

    # Initialize generator
    generator = TestDatasetGenerator(knowledge_base_path)

    # Generate dataset
    test_cases = generator.generate_full_dataset(total_questions=50)

    # Save dataset
    generator.save_dataset(test_cases, output_path)

    print("\n" + "=" * 60)
    print("✅ Test dataset generation completed!")
    print(f"📁 Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
