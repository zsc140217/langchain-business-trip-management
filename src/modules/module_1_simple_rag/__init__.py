"""
Module 1: Simple RAG
简单检索增强生成模块

导出核心组件供外部使用
"""

from .loader import load_and_split_documents, load_documents_from_text
from .retriever import (
    create_faiss_vectorstore,
    create_retriever,
    save_vectorstore,
    load_vectorstore
)
from .chain import (
    create_rag_chain_lcel,
    create_rag_chain_with_sources,
    format_docs
)

__all__ = [
    # Loader
    "load_and_split_documents",
    "load_documents_from_text",

    # Retriever
    "create_faiss_vectorstore",
    "create_retriever",
    "save_vectorstore",
    "load_vectorstore",

    # Chain
    "create_rag_chain_lcel",
    "create_rag_chain_with_sources",
    "format_docs",
]

__version__ = "1.0.0"
__author__ = "LangChain Business Trip Management"
__description__ = "Simple RAG implementation using FAISS and LCEL"
