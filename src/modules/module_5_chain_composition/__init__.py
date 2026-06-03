"""
Module 5: Chain Composition
Sequential and parallel chain execution with performance comparison

This module demonstrates LCEL chain composition patterns:
- Sequential chains: Execute steps one after another
- Parallel chains: Execute multiple steps concurrently
- Performance comparison: Measure time savings
"""

from .sequential_chain import SequentialChain
from .parallel_chain import ParallelChain

__all__ = [
    "SequentialChain",
    "ParallelChain",
]
