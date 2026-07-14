"""
知识图谱实体关系提取器

使用 LLM 从文本中提取实体和关系，用于构建知识图谱

实体类型：
- PERSON: 人物（员工、领导）
- ORGANIZATION: 组织（部门、公司、机构）
- LOCATION: 地点（城市、国家）
- POLICY: 政策（差旅政策、报销规定）
- CONCEPT: 概念（职级、标准等）

关系类型：
- WORKS_FOR: 工作于（人物 -> 组织）
- LOCATED_IN: 位于（组织/人物 -> 地点）
- APPLIES_TO: 适用于（政策 -> 对象）
- REQUIRES: 需要（政策 -> 条件）
- RELATES_TO: 相关（通用关系）
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from src.models.llm import get_llm
import json
import re


class Entity(BaseModel):
    """实体模型"""
    name: str = Field(description="实体名称")
    type: str = Field(description="实体类型：PERSON, ORGANIZATION, LOCATION, POLICY, CONCEPT")
    properties: Dict[str, str] = Field(default_factory=dict, description="实体属性")

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name == other.name and self.type == other.type


class Relationship(BaseModel):
    """关系模型"""
    source: str = Field(description="源实体名称")
    target: str = Field(description="目标实体名称")
    type: str = Field(description="关系类型：WORKS_FOR, LOCATED_IN, APPLIES_TO, REQUIRES, RELATES_TO")
    properties: Dict[str, str] = Field(default_factory=dict, description="关系属性")


class GraphExtractor:
    """
    知识图谱提取器

    使用 LLM 从文本中提取实体和关系，支持中英文
    """

    def __init__(self, llm=None, temperature=0.1):
        """
        初始化提取器

        Args:
            llm: 语言模型实例，如果为 None 则自动创建
            temperature: 温度参数，默认 0.1（更确定性的输出）
        """
        self.llm = llm if llm else get_llm(temperature=temperature)

        # 实体提取提示词
        self.entity_extraction_prompt = """你是一个实体提取专家，请从以下文本中提取所有重要实体。

实体类型定义：
- PERSON: 人物（员工、领导、姓名）
- ORGANIZATION: 组织（部门、公司、机构）
- LOCATION: 地点（城市、省份、国家、具体地点）
- POLICY: 政策名称（差旅政策、报销规定、管理办法等）
- CONCEPT: 概念（职级、标准、类别等抽象概念）

提取规则：
1. 提取所有明确的实体，包括专有名词和关键概念
2. 对于中文实体，保持原文
3. 提取实体的重要属性（如职级、金额、时间等）
4. 去重：相同名称和类型的实体只保留一个
5. 规范化：统一格式（如"北京市" -> "北京"）

返回 JSON 格式：
{{
    "entities": [
        {{
            "name": "实体名称",
            "type": "实体类型",
            "properties": {{"属性名": "属性值"}}
        }}
    ]
}}

只返回 JSON，不要其他内容。

文本：
{text}"""

        # 关系提取提示词
        self.relationship_extraction_prompt = """你是一个关系提取专家，请根据给定的实体列表和原文本，提取实体之间的关系。

关系类型定义：
- WORKS_FOR: 工作于（人物 -> 组织）
- LOCATED_IN: 位于（组织/地点 -> 地点）
- APPLIES_TO: 适用于（政策 -> 对象，如职级、地区）
- REQUIRES: 需要（政策/流程 -> 条件）
- RELATES_TO: 相关（通用关系，用于其他类型）

提取规则：
1. 只提取明确表达的关系，不要推测
2. 关系必须连接已提取的实体
3. 每个关系可以有属性（如金额、时间、条件等）
4. 避免冗余关系

实体列表：
{entities}

原文本：
{text}

返回 JSON 格式：
{{
    "relationships": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型",
            "properties": {{"属性名": "属性值"}}
        }}
    ]
}}

只返回 JSON，不要其他内容。"""

    def extract_entities(self, text: str) -> List[Entity]:
        """
        从文本中提取实体

        Args:
            text: 输入文本

        Returns:
            List[Entity]: 提取的实体列表

        Raises:
            ValueError: 如果文本为空
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        text = text.strip()

        # 构建消息
        prompt = self.entity_extraction_prompt.format(text=text)
        messages = [
            SystemMessage(content="你是一个专业的实体提取专家。"),
            HumanMessage(content=prompt)
        ]

        # 调用 LLM
        try:
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
        except Exception as e:
            # LLM 调用失败，返回空列表
            print(f"[警告] LLM 调用失败：{e}")
            return []

        # 解析 JSON 响应
        try:
            # 清理可能的 markdown 代码块标记
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            # 尝试提取 JSON 部分（使用更宽松的正则）
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    print(f"[警告] JSON 解析失败：{e}")
                    print(f"[调试] 原始响应：{result_text[:200]}")
                    return []
            else:
                print(f"[警告] 未找到 JSON：{e}")
                print(f"[调试] 原始响应：{result_text[:200]}")
                return []

        # 转换为 Entity 对象
        entities = []
        if "entities" in result:
            for entity_data in result["entities"]:
                try:
                    entity = Entity(
                        name=entity_data["name"],
                        type=entity_data["type"],
                        properties=entity_data.get("properties", {})
                    )
                    entities.append(entity)
                except (KeyError, TypeError) as e:
                    print(f"[警告] 实体数据格式错误：{entity_data}, {e}")
                    continue

        # 去重
        unique_entities = list(set(entities))
        return unique_entities

    def extract_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """
        从文本中提取实体之间的关系

        Args:
            text: 输入文本
            entities: 已提取的实体列表

        Returns:
            List[Relationship]: 提取的关系列表

        Raises:
            ValueError: 如果文本为空或实体列表为空
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        if not entities:
            return []  # 没有实体则没有关系

        text = text.strip()

        # 构建实体列表字符串
        entity_names = [f"- {e.name} ({e.type})" for e in entities]
        entities_str = "\n".join(entity_names)

        # 构建消息
        prompt = self.relationship_extraction_prompt.format(
            entities=entities_str,
            text=text
        )
        messages = [
            SystemMessage(content="你是一个专业的关系提取专家。"),
            HumanMessage(content=prompt)
        ]

        # 调用 LLM
        try:
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
        except Exception as e:
            print(f"[警告] LLM 调用失败：{e}")
            return []

        # 解析 JSON 响应
        try:
            # 清理可能的 markdown 代码块标记
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            # 尝试提取 JSON 部分（使用更宽松的正则）
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    print(f"[警告] JSON 解析失败：{e}")
                    print(f"[调试] 原始响应：{result_text[:200]}")
                    return []
            else:
                print(f"[警告] 未找到 JSON：{e}")
                print(f"[调试] 原始响应：{result_text[:200]}")
                return []

        # 转换为 Relationship 对象
        relationships = []
        if "relationships" in result:
            entity_names_set = {e.name for e in entities}
            for rel_data in result["relationships"]:
                try:
                    # 验证实体存在
                    source = rel_data["source"]
                    target = rel_data["target"]

                    if source not in entity_names_set:
                        print(f"[警告] 源实体不存在：{source}")
                        continue
                    if target not in entity_names_set:
                        print(f"[警告] 目标实体不存在：{target}")
                        continue

                    relationship = Relationship(
                        source=source,
                        target=target,
                        type=rel_data["type"],
                        properties=rel_data.get("properties", {})
                    )
                    relationships.append(relationship)
                except (KeyError, TypeError) as e:
                    print(f"[警告] 关系数据格式错误：{rel_data}, {e}")
                    continue

        return relationships

    def extract(self, text: str) -> Dict[str, List]:
        """
        一次性提取实体和关系

        Args:
            text: 输入文本

        Returns:
            Dict: {"entities": [...], "relationships": [...]}
        """
        entities = self.extract_entities(text)
        relationships = self.extract_relationships(text, entities)

        return {
            "entities": entities,
            "relationships": relationships
        }


# 使用示例
if __name__ == "__main__":
    """测试知识图谱提取器"""
    print("测试知识图谱提取器...\n")

    extractor = GraphExtractor()

    # 测试文本
    test_text = """
    北京市差旅住宿标准规定：
    - 副总及以上职级，住宿标准为每晚800元
    - 经理职级，住宿标准为每晚500元
    - 普通员工，住宿标准为每晚300元

    所有员工需要在出差前提交差旅申请，经部门经理审批后方可出差。
    财务部负责差旅费用的审核和报销。
    """

    print("=" * 60)
    print("测试文本：")
    print(test_text)
    print("=" * 60)

    # 提取实体
    print("\n提取实体...")
    entities = extractor.extract_entities(test_text)
    print(f"\n共提取 {len(entities)} 个实体：")
    for entity in entities:
        print(f"  - {entity.name} ({entity.type})")
        if entity.properties:
            print(f"    属性：{entity.properties}")

    # 提取关系
    print("\n提取关系...")
    relationships = extractor.extract_relationships(test_text, entities)
    print(f"\n共提取 {len(relationships)} 个关系：")
    for rel in relationships:
        print(f"  - {rel.source} --[{rel.type}]--> {rel.target}")
        if rel.properties:
            print(f"    属性：{rel.properties}")

    print("\n" + "=" * 60)
    print("测试完成！")
