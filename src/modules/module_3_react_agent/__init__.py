"""
Module 3: ReAct Agent

ReAct (Reasoning + Acting) agent implementation with tool integration.
Demonstrates autonomous reasoning and tool selection for complex tasks.
"""

# 使用简化版实现
try:
    from .agent_simple import create_react_agent_with_tools, run_react_agent
    __all__ = ['create_react_agent_with_tools', 'run_react_agent']
except ImportError:
    # 如果简化版也导入失败，提供占位符
    __all__ = []

__version__ = "0.1.0"
