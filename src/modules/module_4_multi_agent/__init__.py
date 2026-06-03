"""
Module 4: Multi-Agent Orchestration
LangGraph-based multi-agent system with supervisor-worker pattern
"""
from .state_graph import MultiAgentGraph, AgentState, create_initial_state, extract_final_answer, get_execution_trace
from .supervisor import SupervisorAgent, LLMSupervisorAgent
from .workers import PolicyWorkerAgent, WeatherWorkerAgent, ItineraryWorkerAgent

__all__ = [
    "MultiAgentGraph",
    "AgentState",
    "create_initial_state",
    "extract_final_answer",
    "get_execution_trace",
    "SupervisorAgent",
    "LLMSupervisorAgent",
    "PolicyWorkerAgent",
    "WeatherWorkerAgent",
    "ItineraryWorkerAgent"
]

__version__ = "1.0.0"
