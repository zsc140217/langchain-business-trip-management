"""
Skill基类
定义Skill的标准接口

对应Spring AI的：
src/main/java/com/jblmj/aiagent/skill/Skill.java
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class Skill(ABC):
    """
    Skill基类

    设计理念：
    - Skill = 用户可直接理解的任务单元
    - 一个任务对应一个Skill（查天气、规划行程、发送邮件）
    - Skill不是"能力"或"中间件"

    与Service/Tool的区别：
    - Skill：面向用户任务（业务层）
    - Service：框架能力（如ComplexityAssessor、TaskDecomposer）
    - Tool：原子操作（如API调用、数据库查询）

    Skill调用链：
    Skill → Service → Tool
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Skill名称

        Returns:
            Skill的唯一标识
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Skill描述

        Returns:
            Skill的功能描述
        """
        pass

    @property
    @abstractmethod
    def keywords(self) -> List[str]:
        """
        关键词列表

        用于快速判断是否能处理查询

        Returns:
            关键词列表
        """
        pass

    @property
    def priority(self) -> int:
        """
        优先级

        当多个Skill都能处理时，选择优先级最高的
        数值越小，优先级越高

        Returns:
            优先级（默认100）
        """
        return 100

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """
        判断是否能处理该查询

        通过关键词匹配快速判断

        Args:
            query: 用户查询

        Returns:
            是否能处理
        """
        pass

    @abstractmethod
    def execute(self, query: str, chat_id: str) -> str:
        """
        执行Skill

        Args:
            query: 用户查询
            chat_id: 会话ID

        Returns:
            执行结果
        """
        pass


class SkillRegistry:
    """
    Skill注册中心

    功能：
    1. 自动注册Skill
    2. 根据查询选择合适的Skill
    3. 按优先级排序

    对应Spring AI的：
    src/main/java/com/jblmj/aiagent/skill/SkillRegistry.java
    """

    def __init__(self):
        self.skills: List[Skill] = []

    def register(self, skill: Skill):
        """
        注册Skill

        Args:
            skill: Skill实例
        """
        self.skills.append(skill)
        # 按优先级排序
        self.skills.sort(key=lambda s: s.priority)
        print(f"✅ 注册Skill: {skill.name} (优先级:{skill.priority})")

    def select_skill(self, query: str) -> Optional[Skill]:
        """
        根据查询选择Skill

        流程：
        1. 遍历所有Skill
        2. 调用can_handle()判断
        3. 返回第一个能处理的Skill（优先级最高）

        Args:
            query: 用户查询

        Returns:
            匹配的Skill，如果没有则返回None
        """
        for skill in self.skills:
            if skill.can_handle(query):
                print(f"🎯 选中Skill: {skill.name}")
                return skill

        print(f"⚠️  没有Skill能处理该查询")
        return None

    def get_all_skills(self) -> List[Skill]:
        """
        获取所有Skill

        Returns:
            Skill列表
        """
        return self.skills

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """
        根据名称获取Skill

        Args:
            name: Skill名称

        Returns:
            Skill实例，如果不存在则返回None
        """
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None


# 测试代码
if __name__ == "__main__":
    """
    测试Skill基类和注册中心
    """
    print("测试Skill系统...\n")

    # 创建一个简单的测试Skill
    class TestSkill(Skill):
        @property
        def name(self) -> str:
            return "test_skill"

        @property
        def description(self) -> str:
            return "测试Skill"

        @property
        def keywords(self) -> List[str]:
            return ["测试", "test"]

        @property
        def priority(self) -> int:
            return 50

        def can_handle(self, query: str) -> bool:
            return any(keyword in query for keyword in self.keywords)

        def execute(self, query: str, chat_id: str) -> str:
            return f"TestSkill处理: {query}"

    # 创建注册中心
    registry = SkillRegistry()

    # 注册Skill
    test_skill = TestSkill()
    registry.register(test_skill)

    # 测试选择
    query = "这是一个测试查询"
    skill = registry.select_skill(query)

    if skill:
        result = skill.execute(query, "test123")
        print(f"\n执行结果: {result}")

    print("\n✅ Skill系统测试完成！")
