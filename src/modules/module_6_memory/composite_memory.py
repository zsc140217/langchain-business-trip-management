"""
Composite Memory - 组合记忆

整合三层记忆策略：
1. BufferMemory - 短期缓冲（最近5轮对话）
2. SummaryMemory - 中期摘要（压缩历史）
3. VectorMemory - 长期检索（语义搜索）

提供统一接口，智能组合三层记忆的上下文。
"""

from typing import Dict, Any, Optional, List
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.embeddings.base import Embeddings

from .buffer_memory import BufferMemory
from .summary_memory import SummaryMemory
from .vector_memory import VectorMemory


class CompositeMemory:
    """组合记忆 - 三层记忆架构的统一管理"""

    def __init__(
        self,
        llm: Optional[ChatTongyi] = None,
        embeddings: Optional[Embeddings] = None,
        buffer_max_turns: int = 5,
        summary_max_tokens: int = 2000,
        vector_k: int = 3,
        vector_score_threshold: float = 0.5,
        enable_buffer: bool = True,
        enable_summary: bool = True,
        enable_vector: bool = True
    ):
        """
        初始化组合记忆

        Args:
            llm: 语言模型（用于摘要）
            embeddings: 嵌入模型（用于向量存储）
            buffer_max_turns: 缓冲记忆最大轮次
            summary_max_tokens: 摘要最大token数
            vector_k: 向量检索返回数量
            vector_score_threshold: 向量检索相似度阈值
            enable_buffer: 启用缓冲记忆
            enable_summary: 启用摘要记忆
            enable_vector: 启用向量记忆
        """
        self.enable_buffer = enable_buffer
        self.enable_summary = enable_summary
        self.enable_vector = enable_vector

        # 初始化各层记忆
        self.buffer_memory = BufferMemory(
            max_turns=buffer_max_turns
        ) if enable_buffer else None

        self.summary_memory = SummaryMemory(
            llm=llm,
            max_token_limit=summary_max_tokens
        ) if enable_summary else None

        self.vector_memory = VectorMemory(
            embeddings=embeddings,
            k=vector_k,
            score_threshold=vector_score_threshold
        ) if enable_vector else None

        self._total_exchanges = 0

    def add_exchange(
        self,
        human_message: str,
        ai_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加一次完整对话交互到所有启用的记忆层

        Args:
            human_message: 用户消息
            ai_message: AI响应
            metadata: 元数据（用于向量存储）
        """
        # 添加到缓冲记忆
        if self.buffer_memory:
            self.buffer_memory.add_exchange(human_message, ai_message)

        # 添加到摘要记忆
        if self.summary_memory:
            self.summary_memory.add_exchange(human_message, ai_message)

        # 添加到向量记忆
        if self.vector_memory:
            self.vector_memory.add_exchange(human_message, ai_message, metadata)

        self._total_exchanges += 1

    def get_context(
        self,
        query: Optional[str] = None,
        include_buffer: bool = True,
        include_summary: bool = True,
        include_vector: bool = True
    ) -> str:
        """
        获取组合的上下文信息

        Args:
            query: 查询文本（用于向量检索）
            include_buffer: 包含缓冲记忆
            include_summary: 包含摘要记忆
            include_vector: 包含向量记忆

        Returns:
            组合的上下文字符串
        """
        context_parts = []

        # 1. 缓冲记忆 - 最近的对话
        if include_buffer and self.buffer_memory:
            buffer_context = self.buffer_memory.get_context()
            if buffer_context:
                context_parts.append("=== 最近对话 ===")
                context_parts.append(buffer_context)

        # 2. 摘要记忆 - 历史摘要
        if include_summary and self.summary_memory:
            summary_context = self.summary_memory.get_context()
            if summary_context and "暂无" not in summary_context:
                context_parts.append("\n=== 历史摘要 ===")
                context_parts.append(summary_context)

        # 3. 向量记忆 - 相关历史
        if include_vector and self.vector_memory and query:
            vector_context = self.vector_memory.get_context(query)
            if vector_context and "暂无" not in vector_context:
                context_parts.append("\n=== 相关历史 ===")
                context_parts.append(vector_context)

        if not context_parts:
            return "暂无历史上下文。"

        return "\n".join(context_parts)

    def get_layered_context(self, query: Optional[str] = None) -> Dict[str, str]:
        """
        获取分层的上下文信息

        Args:
            query: 查询文本（用于向量检索）

        Returns:
            包含各层上下文的字典
        """
        result = {}

        if self.buffer_memory:
            result['buffer'] = self.buffer_memory.get_context()

        if self.summary_memory:
            result['summary'] = self.summary_memory.get_summary()

        if self.vector_memory and query:
            result['vector'] = self.vector_memory.get_context(query)

        return result

    def search_relevant_history(
        self,
        query: str,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关历史记录

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            相关记录列表
        """
        if not self.vector_memory:
            return []

        results = self.vector_memory.search_with_score(query, k=k)

        return [
            {
                'content': doc.page_content,
                'score': score,
                'metadata': doc.metadata
            }
            for doc, score in results
        ]

    def clear_all(self) -> None:
        """清空所有记忆层"""
        if self.buffer_memory:
            self.buffer_memory.clear()

        if self.summary_memory:
            self.summary_memory.clear()

        if self.vector_memory:
            self.vector_memory.clear()

        self._total_exchanges = 0

    def clear_buffer(self) -> None:
        """仅清空缓冲记忆"""
        if self.buffer_memory:
            self.buffer_memory.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取记忆系统统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'total_exchanges': self._total_exchanges,
            'enabled_layers': []
        }

        if self.buffer_memory:
            stats['enabled_layers'].append('buffer')
            stats['buffer_turns'] = self.buffer_memory.get_turn_count()
            stats['buffer_full'] = self.buffer_memory.is_full()

        if self.summary_memory:
            stats['enabled_layers'].append('summary')
            summary_vars = self.summary_memory.to_dict()
            stats['summary_message_count'] = summary_vars.get('message_count', 0)

        if self.vector_memory:
            stats['enabled_layers'].append('vector')
            stats['vector_memory_count'] = self.vector_memory.get_memory_count()

        return stats

    def save_vector_memory(
        self,
        folder_path: str,
        index_name: str = "composite_vector_memory"
    ) -> None:
        """
        保存向量记忆到本地

        Args:
            folder_path: 文件夹路径
            index_name: 索引名称
        """
        if self.vector_memory:
            self.vector_memory.save_local(folder_path, index_name)

    @classmethod
    def load_with_vector_memory(
        cls,
        folder_path: str,
        llm: Optional[ChatTongyi] = None,
        embeddings: Optional[Embeddings] = None,
        index_name: str = "composite_vector_memory",
        **kwargs
    ) -> 'CompositeMemory':
        """
        加载包含向量记忆的组合记忆

        Args:
            folder_path: 向量存储文件夹路径
            llm: 语言模型
            embeddings: 嵌入模型
            index_name: 索引名称
            **kwargs: 其他初始化参数

        Returns:
            CompositeMemory实例
        """
        instance = cls(llm=llm, embeddings=embeddings, **kwargs)

        # 加载向量记忆
        if instance.enable_vector:
            instance.vector_memory = VectorMemory.load_local(
                folder_path,
                embeddings or instance.vector_memory.embeddings,
                index_name
            )

        return instance

    def to_dict(self) -> Dict[str, Any]:
        """
        导出配置为字典

        Returns:
            包含配置和统计的字典
        """
        result = {
            'total_exchanges': self._total_exchanges,
            'enable_buffer': self.enable_buffer,
            'enable_summary': self.enable_summary,
            'enable_vector': self.enable_vector
        }

        if self.buffer_memory:
            result['buffer'] = self.buffer_memory.to_dict()

        if self.summary_memory:
            result['summary'] = self.summary_memory.to_dict()

        if self.vector_memory:
            result['vector'] = self.vector_memory.to_dict()

        return result
