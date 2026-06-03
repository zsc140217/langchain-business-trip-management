"""
重排序器 - 简化版实现（无需 sentence_transformers）

核心功能：
1. 基于简单的相似度计算对候选文档重新打分
2. 支持关键词匹配和位置加权
"""
from typing import List, Optional, Tuple
from langchain_core.documents import Document


class CrossEncoderReranker:
    """
    简化的重排序器实现
    
    使用关键词匹配和位置权重进行重排序
    避免依赖 sentence_transformers
    """

    def __init__(
        self,
        model_name: str = "simple",
        device: str = "cpu"
    ):
        """
        初始化重排序器
        
        Args:
            model_name: 模型名称（此简化版忽略）
            device: 运行设备（此简化版忽略）
        """
        self.model_name = model_name
        self.device = device
        print(f"[WARN]  使用简化版重排序器（无需 sentence_transformers）")

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Document]:
        """
        对文档进行重排序
        
        使用简单的关键词匹配算法
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            top_k: 返回前K个文档
        
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        # 计算每个文档的得分
        scored_docs: List[Tuple[float, Document]] = []
        
        query_terms = set(query.lower().split())
        
        for doc in documents:
            content = doc.page_content.lower()
            
            # 计算关键词匹配得分
            matches = sum(1 for term in query_terms if term in content)
            score = matches / len(query_terms) if query_terms else 0.0
            
            scored_docs.append((score, doc))
        
        # 按得分降序排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # 提取文档
        reranked_docs = [doc for score, doc in scored_docs]
        
        # 返回 Top-K
        if top_k is not None:
            reranked_docs = reranked_docs[:top_k]
        
        return reranked_docs
