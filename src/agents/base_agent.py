"""
Base Agent Class
Provides common functionality for all specialized agents

Design Principles:
- Single Responsibility: Each agent focuses on one domain
- Observability: Automatic LangSmith tracing
- Error Handling: Graceful degradation with fallbacks
- Type Safety: Pydantic models for inputs/outputs
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialized agents

    Provides:
    - LLM integration
    - Tool management
    - Error handling
    - Observability (automatic tracing)
    - Common utilities

    Usage:
        class MyAgent(BaseAgent):
            def execute(self, task: Dict[str, Any]) -> str:
                # Implementation
                pass
    """

    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        tools: Optional[List[BaseTool]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent

        Args:
            name: Agent name (used for logging and tracing)
            llm: Language model instance
            tools: List of tools available to this agent
            config: Agent-specific configuration
        """
        self.name = name
        self.llm = llm
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.config = config or {}

        logger.info(f"Initialized {self.name} with {len(self.tools)} tools")

    @abstractmethod
    @traceable(name="agent_execute")
    def execute(self, task: Dict[str, Any]) -> str:
        """
        Execute agent task

        Args:
            task: Task parameters (agent-specific schema)

        Returns:
            Execution result as string

        Raises:
            ValueError: Invalid task parameters
            RuntimeError: Execution failure
        """
        pass

    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Invoke a tool with error handling

        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: Tool not found
            RuntimeError: Tool execution failed
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}")

        try:
            tool = self.tools[tool_name]
            logger.debug(f"{self.name} invoking tool: {tool_name} with params: {parameters}")
            result = tool.invoke(parameters)
            logger.debug(f"Tool {tool_name} returned: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise RuntimeError(f"Tool execution failed: {e}") from e

    def call_llm(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Call LLM with error handling

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (overrides default)

        Returns:
            LLM response

        Raises:
            RuntimeError: LLM call failed
        """
        try:
            logger.debug(f"{self.name} calling LLM with prompt length: {len(prompt)}")

            # Use temperature from config if not specified
            temp = temperature if temperature is not None else self.config.get("temperature", 0.7)

            response = self.llm.predict(prompt, temperature=temp)
            logger.debug(f"LLM returned: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM call failed: {e}") from e

    def validate_task(self, task: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate task parameters

        Args:
            task: Task parameters
            required_fields: List of required field names

        Raises:
            ValueError: Missing required fields
        """
        missing = [field for field in required_fields if field not in task]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', tools={list(self.tools.keys())})"


class AgentExecutionError(Exception):
    """Custom exception for agent execution failures"""
    pass


class ToolInvocationError(Exception):
    """Custom exception for tool invocation failures"""
    pass
