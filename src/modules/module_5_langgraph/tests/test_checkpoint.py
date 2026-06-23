"""
T1.3 Checkpointing 测试
验证状态持久化和恢复功能
"""
import pytest
from dotenv import load_dotenv
load_dotenv()

from ..graphs.checkpoint_graph import create_checkpoint_graph, run_checkpoint_graph, get_checkpoint_history
from ..state import create_initial_state


class TestCheckpointing:
    """测试Checkpointing功能"""

    def test_memory_checkpointer(self):
        """测试内存Checkpointer"""
        result = run_checkpoint_graph("北京住宿标准", "test-mem-001", checkpointer_type="memory")
        assert result is not None
        assert "answer" in result

    def test_checkpoint_history(self):
        """测试checkpoint历史"""
        graph = create_checkpoint_graph("memory")
        config = {"configurable": {"thread_id": "test-hist-001"}}
        graph.invoke(create_initial_state("测试查询", 2), config)
        checkpoints = get_checkpoint_history(graph, "test-hist-001")
        assert len(checkpoints) > 0

    def test_multiple_sessions(self):
        """测试会话隔离"""
        r1 = run_checkpoint_graph("北京", "s1", checkpointer_type="memory")
        r2 = run_checkpoint_graph("上海", "s2", checkpointer_type="memory")
        assert r1["query"] != r2["query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
