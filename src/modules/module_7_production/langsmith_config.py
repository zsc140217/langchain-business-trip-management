"""
LangSmith Tracing Configuration

Provides LangSmith integration for comprehensive observability:
- Automatic trace collection for all LangChain operations
- Custom run metadata and tags
- Error tracking and debugging
- Performance monitoring

Environment Variables:
- LANGCHAIN_TRACING_V2: Enable tracing (default: "true")
- LANGCHAIN_API_KEY: LangSmith API key
- LANGCHAIN_PROJECT: Project name (default: "business-trip-management")
- LANGCHAIN_ENDPOINT: API endpoint (default: "https://api.smith.langchain.com")
"""

import os
from typing import Dict, Optional, Any, List
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """LangSmith configuration and tracing utilities."""

    def __init__(
        self,
        project_name: str = "business-trip-management",
        enabled: bool = True,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LangSmith configuration.

        Args:
            project_name: LangSmith project name
            enabled: Enable/disable tracing
            tags: Default tags for all traces
            metadata: Default metadata for all traces
        """
        self.project_name = project_name
        self.enabled = enabled and self._check_api_key()
        self.default_tags = tags or []
        self.default_metadata = metadata or {}

        if self.enabled:
            self._configure_environment()
            logger.info(f"LangSmith tracing enabled for project: {project_name}")
        else:
            logger.warning("LangSmith tracing disabled - missing API key or explicitly disabled")

    def _check_api_key(self) -> bool:
        """Check if LangSmith API key is configured."""
        api_key = os.getenv("LANGCHAIN_API_KEY")
        return api_key is not None and len(api_key) > 0

    def _configure_environment(self):
        """Configure environment variables for LangSmith."""
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = self.project_name

        # Set endpoint if not already configured
        if not os.getenv("LANGCHAIN_ENDPOINT"):
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    def get_run_config(
        self,
        run_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get run configuration for LangChain operations.

        Args:
            run_name: Name for this run
            tags: Additional tags for this run
            metadata: Additional metadata for this run

        Returns:
            Configuration dict for chain.invoke(config=...)
        """
        if not self.enabled:
            return {}

        # Merge tags
        all_tags = self.default_tags.copy()
        if tags:
            all_tags.extend(tags)

        # Merge metadata
        all_metadata = self.default_metadata.copy()
        if metadata:
            all_metadata.update(metadata)

        # Add timestamp
        all_metadata["timestamp"] = datetime.utcnow().isoformat()

        config = {
            "tags": all_tags,
            "metadata": all_metadata
        }

        if run_name:
            config["run_name"] = run_name

        return config

    @contextmanager
    def trace_context(
        self,
        operation: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing a specific operation.

        Args:
            operation: Name of the operation
            tags: Tags for this operation
            metadata: Metadata for this operation

        Example:
            with langsmith_config.trace_context("policy_check", tags=["agent"]):
                result = agent.run(query)
        """
        if not self.enabled:
            yield {}
            return

        config = self.get_run_config(
            run_name=operation,
            tags=tags,
            metadata=metadata
        )

        try:
            yield config
        except Exception as e:
            logger.error(f"Error in traced operation '{operation}': {str(e)}")
            raise

    def disable_tracing(self):
        """Temporarily disable tracing."""
        if self.enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.info("LangSmith tracing disabled")

    def enable_tracing(self):
        """Re-enable tracing."""
        if self.enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            logger.info("LangSmith tracing enabled")


# Global default instance
_default_config: Optional[LangSmithConfig] = None


def get_langsmith_config() -> LangSmithConfig:
    """Get or create the default LangSmith configuration."""
    global _default_config

    if _default_config is None:
        _default_config = LangSmithConfig()

    return _default_config


def initialize_langsmith(
    project_name: str = "business-trip-management",
    enabled: bool = True,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> LangSmithConfig:
    """
    Initialize global LangSmith configuration.

    Args:
        project_name: LangSmith project name
        enabled: Enable/disable tracing
        tags: Default tags for all traces
        metadata: Default metadata for all traces

    Returns:
        Configured LangSmith instance
    """
    global _default_config

    _default_config = LangSmithConfig(
        project_name=project_name,
        enabled=enabled,
        tags=tags,
        metadata=metadata
    )

    return _default_config


def get_run_config(**kwargs) -> Dict[str, Any]:
    """
    Convenience function to get run configuration.

    Args:
        **kwargs: Arguments passed to LangSmithConfig.get_run_config()

    Returns:
        Configuration dict for chain.invoke(config=...)
    """
    config = get_langsmith_config()
    return config.get_run_config(**kwargs)


# Example usage patterns
if __name__ == "__main__":
    # Initialize with custom settings
    langsmith = initialize_langsmith(
        project_name="business-trip-management",
        tags=["production", "v1.0"],
        metadata={"environment": "staging"}
    )

    # Get config for a specific run
    config = langsmith.get_run_config(
        run_name="policy_check",
        tags=["agent", "compliance"],
        metadata={"user_id": "12345"}
    )
    print("Run config:", config)

    # Use context manager for tracing
    with langsmith.trace_context("test_operation", tags=["test"]) as trace_config:
        print("Trace config:", trace_config)
