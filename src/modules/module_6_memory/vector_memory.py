"""
Vector Memory - 向量记忆

实现基于向量检索的长期记忆，使用FAISS存储和检索历史对话。
支持语义相似度搜索，快速检索相关历史上下文。
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.messages import Document
import os
import json
from datetime import datetime


class VectorMemory:
    """向量记忆 - 基于语义检索的长期记忆"""

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        k: int = 3,
        score_threshold: float = 0.5
    ):
        """
        初始化向量记忆

        Args:
            embeddings: 嵌入模型
            k: 检索返回的最大结果数
            score_threshold: 相似度阈值
        """
        self.k = k
        self.score_threshold = score_threshold

        # 初始化嵌入模型
        if embeddings is None:
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY not found in environment")

            self.embeddings = DashScopeEmbeddings(
                model="text-embedding-v2",
                dashscope_api_key=api_key
            )
        else:
            self.embeddings = embeddings

        # 向量存储（延迟初始化）
        self.vector_store: Optional[FAISS] = None
        self._memory_count = 0

    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加记忆到向量存储

        Args:
            content: 记忆内容
            metadata: 元数据（可选）
        """
        if metadata is None:
            metadata = {}

        # 添加时间戳
        metadata['timestamp'] = datetime.now().isoformat()
        metadata['memory_id'] = self._memory_count

        # 创建文档
        doc = Document(page_content=content, metadata=metadata)

        # 初始化或更新向量存储
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents([doc], self.embeddings)
        else:
            self.vector_store.add_documents([doc])

        self._memory_count += 1

    def add_exchange(
        self,
        human_message: str,
        ai_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加一次完整对话交互

        Args:
            human_message: 用户消息
            ai_message: AI响应
            metadata: 额外元数据
        """
        if metadata is None:
            metadata = {}

        # 组合对话内容
        content = f"用户：{human_message}\n助手：{ai_message}"

        metadata['exchange_type'] = 'conversation'
        metadata['human_message'] = human_message
        metadata['ai_message'] = ai_message

        self.add_memory(content, metadata)

    def search(
        self,
        query: str,
        k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        搜索相关记忆

        Args:
            query: 查询文本
            k: 返回结果数（默认使用初始化时的k）
            filter_metadata: 元数据过滤条件

        Returns:
            相关文档列表
        """
        if self.vector_store is None:
            return []

        k = k or self.k

        # 执行相似度搜索
        docs = self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter_metadata
        )

        return docs

    def search_with_score(
        self,
        query: str,
        k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """
        搜索相关记忆并返回相似度分数

        Args:
            query: 查询文本
            k: 返回结果数

        Returns:
            (文档, 相似度分数) 元组列表
        """
        if self.vector_store is None:
            return []

        k = k or self.k

        # 执行带分数的搜索
        results = self.vector_store.similarity_search_with_score(query, k=k)

        # 过滤低于阈值的结果
        filtered_results = [
            (doc, score) for doc, score in results
            if score >= self.score_threshold
        ]

        return filtered_results

    def get_context(self, query: str, k: Optional[int] = None) -> str:
        """
        获取与查询相关的上下文

        Args:
            query: 查询文本
            k: 返回结果数

        Returns:
            格式化的上下文字符串
        """
        results = self.search_with_score(query, k=k)

        if not results:
            return "暂无相关历史记忆。"

        context_parts = ["相关历史记忆："]

        for i, (doc, score) in enumerate(results, 1):
            context_parts.append(f"\n记忆 {i} (相似度: {score:.2f}):")
            context_parts.append(doc.page_content)

        return "\n".join(context_parts)

    def get_all_memories(self) -> List[Document]:
        """
        获取所有存储的记忆

        Returns:
            所有文档列表
        """
        if self.vector_store is None:
            return []

        # FAISS doesn't have a direct "get all" method
        # We use a dummy search with high k value
        return self.vector_store.similarity_search("", k=self._memory_count)

    def clear(self) -> None:
        """清空向量记忆"""
        self.vector_store = None
        self._memory_count = 0

    def get_memory_count(self) -> int:
        """
        获取记忆总数

        Returns:
            记忆数量
        """
        return self._memory_count

    def save_local(self, folder_path: str, index_name: str = "vector_memory") -> None:
        """
        保存向量存储到本地

        Args:
            folder_path: 文件夹路径
            index_name: 索引名称
        """
        if self.vector_store is None:
            raise ValueError("No vector store to save")

        self.vector_store.save_local(folder_path, index_name)

        # 保存元数据
        metadata = {
            'memory_count': self._memory_count,
            'k': self.k,
            'score_threshold': self.score_threshold
        }

        metadata_path = os.path.join(folder_path, f"{index_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_local(
        cls,
        folder_path: str,
        embeddings: Optional[Embeddings] = None,
        index_name: str = "vector_memory"
    ) -> 'VectorMemory':
        """
        从本地加载向量存储

        Args:
            folder_path: 文件夹路径
            embeddings: 嵌入模型
            index_name: 索引名称

        Returns:
            VectorMemory实例
        """
        # 加载元数据
        metadata_path = os.path.join(folder_path, f"{index_name}_metadata.json")

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            k = metadata.get('k', 3)
            score_threshold = metadata.get('score_threshold', 0.5)
            memory_count = metadata.get('memory_count', 0)
        else:
            k = 3
            score_threshold = 0.5
            memory_count = 0

        # 创建实例
        instance = cls(embeddings=embeddings, k=k, score_threshold=score_threshold)

        # 加载向量存储
        if embeddings is None:
            embeddings = instance.embeddings

        instance.vector_store = FAISS.load_local(
            folder_path,
            embeddings,
            index_name,
            allow_dangerous_deserialization=True
        )
        instance._memory_count = memory_count

        return instance

    def to_dict(self) -> Dict[str, Any]:
        """
        导出配置为字典

        Returns:
            包含配置的字典
        """
        return {
            'k': self.k,
            'score_threshold': self.score_threshold,
            'memory_count': self._memory_count,
            'has_vector_store': self.vector_store is not None
        }
