"""
Pydantic Schemas for Multi-Agent Framework
Type-safe data models for all agents and tools

Design Principles:
- Type Safety: Pydantic validation for all inputs/outputs
- Immutability: Use frozen models where appropriate
- Documentation: Clear field descriptions
- Validation: Custom validators for business rules
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime


# ============================================================================
# Enums
# ============================================================================

class QueryComplexity(str, Enum):
    """Query complexity levels for routing"""
    SIMPLE = "SIMPLE"      # Single tool call
    MEDIUM = "MEDIUM"      # Multiple tool calls
    COMPLEX = "COMPLEX"    # Task decomposition required


class TaskType(str, Enum):
    """Subtask types for task decomposition"""
    QUERY_WEATHER = "QUERY_WEATHER"
    QUERY_HOTEL = "QUERY_HOTEL"
    QUERY_CUSTOMER = "QUERY_CUSTOMER"
    QUERY_ROUTE = "QUERY_ROUTE"
    QUERY_POLICY = "QUERY_POLICY"
    VALIDATE_EXPENSE = "VALIDATE_EXPENSE"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"


class ApprovalStatus(str, Enum):
    """Approval workflow status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class ExpenseCategory(str, Enum):
    """Expense categories"""
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    TRANSPORTATION = "transportation"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


# ============================================================================
# Task Models
# ============================================================================

class SubTask(BaseModel):
    """
    Subtask for task decomposition

    Used by TaskDecomposer to break down complex queries into
    structured subtasks with dependency management
    """
    id: int = Field(..., description="Unique task identifier")
    task_type: TaskType = Field(..., description="Type of task to execute")
    description: str = Field(..., description="Human-readable task description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    depends_on: List[int] = Field(default_factory=list, description="List of task IDs this task depends on")
    priority: int = Field(default=0, description="Task priority (higher = more important)")

    # Execution results
    result: Optional[str] = Field(None, description="Task execution result")
    success: bool = Field(False, description="Whether task executed successfully")
    error: Optional[str] = Field(None, description="Error message if task failed")

    class Config:
        use_enum_values = True

    @validator("depends_on")
    def validate_dependencies(cls, v, values):
        """Ensure task doesn't depend on itself"""
        if "id" in values and values["id"] in v:
            raise ValueError("Task cannot depend on itself")
        return v


class TaskDecompositionResult(BaseModel):
    """Result of task decomposition"""
    subtasks: List[SubTask] = Field(..., description="List of decomposed subtasks")
    total_tasks: int = Field(..., description="Total number of subtasks")
    has_dependencies: bool = Field(..., description="Whether tasks have dependencies")
    estimated_time_seconds: Optional[float] = Field(None, description="Estimated execution time")


# ============================================================================
# Agent Request/Response Models
# ============================================================================

class AgentRequest(BaseModel):
    """Base request model for all agents"""
    query: str = Field(..., description="User query or task description")
    user_id: str = Field(default="anonymous", description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier for memory")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AgentResponse(BaseModel):
    """Base response model for all agents"""
    result: str = Field(..., description="Agent execution result")
    success: bool = Field(..., description="Whether execution was successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    sources: List[str] = Field(default_factory=list, description="Source documents or references")


class TripPlanningRequest(AgentRequest):
    """Request for TripPlannerAgent"""
    destinations: List[str] = Field(default_factory=list, description="List of destination cities")
    start_date: Optional[str] = Field(None, description="Trip start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Trip end date (YYYY-MM-DD)")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class PolicyQueryRequest(AgentRequest):
    """Request for PolicyAdvisorAgent"""
    category: Optional[str] = Field(None, description="Policy category (accommodation, meals, etc.)")
    city: Optional[str] = Field(None, description="City for location-specific policies")


class ExpenseValidationRequest(AgentRequest):
    """Request for ExpenseTrackerAgent"""
    amount: float = Field(..., description="Expense amount", gt=0)
    category: ExpenseCategory = Field(..., description="Expense category")
    city: str = Field(..., description="City where expense occurred")
    date: str = Field(..., description="Expense date (YYYY-MM-DD)")
    description: str = Field(..., description="Expense description")
    receipt_url: Optional[str] = Field(None, description="URL to receipt image")

    @validator("date")
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


# ============================================================================
# Expense and Approval Models
# ============================================================================

class Expense(BaseModel):
    """Expense record"""
    id: Optional[str] = Field(None, description="Expense ID")
    user_id: str = Field(..., description="User who submitted expense")
    amount: float = Field(..., description="Expense amount", gt=0)
    category: ExpenseCategory = Field(..., description="Expense category")
    city: str = Field(..., description="City where expense occurred")
    date: str = Field(..., description="Expense date (YYYY-MM-DD)")
    description: str = Field(..., description="Expense description")
    receipt_url: Optional[str] = Field(None, description="URL to receipt image")

    # Validation results
    is_valid: bool = Field(False, description="Whether expense is valid")
    violations: List[str] = Field(default_factory=list, description="Policy violations")
    requires_approval: bool = Field(False, description="Whether approval is required")
    approval_level: Optional[str] = Field(None, description="Required approval level")

    # Approval tracking
    approval_status: ApprovalStatus = Field(ApprovalStatus.PENDING, description="Approval status")
    approver_id: Optional[str] = Field(None, description="ID of approver")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")

    class Config:
        use_enum_values = True


class ApprovalRequest(BaseModel):
    """Approval request"""
    id: Optional[str] = Field(None, description="Approval request ID")
    expense_id: str = Field(..., description="Associated expense ID")
    requester_id: str = Field(..., description="User requesting approval")
    approver_id: str = Field(..., description="User who should approve")
    approval_level: str = Field(..., description="Approval level (manager, director, vp)")
    status: ApprovalStatus = Field(ApprovalStatus.PENDING, description="Approval status")
    created_at: datetime = Field(default_factory=datetime.now, description="Request creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        use_enum_values = True


# ============================================================================
# RAG Models
# ============================================================================

class Document(BaseModel):
    """Retrieved document"""
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Document source")
    score: float = Field(..., description="Relevance score", ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RetrievalResult(BaseModel):
    """RAG retrieval result"""
    query: str = Field(..., description="Original query")
    rewritten_query: Optional[str] = Field(None, description="Rewritten query")
    documents: List[Document] = Field(..., description="Retrieved documents")
    retrieval_time_ms: float = Field(..., description="Retrieval time in milliseconds")


# ============================================================================
# Memory Models
# ============================================================================

class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConversationHistory(BaseModel):
    """Conversation history"""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Conversation start time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class UserProfile(BaseModel):
    """User profile for long-term memory"""
    user_id: str = Field(..., description="User identifier")
    frequent_cities: Dict[str, int] = Field(default_factory=dict, description="City visit frequency")
    preferred_hotels: Dict[str, int] = Field(default_factory=dict, description="Hotel preference frequency")
    preferred_airlines: Dict[str, int] = Field(default_factory=dict, description="Airline preference frequency")
    average_expense: Dict[str, float] = Field(default_factory=dict, description="Average expense by category")
    conversation_count: int = Field(default=0, description="Total conversation count")
    last_trip_date: Optional[str] = Field(None, description="Last trip date")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    created_at: datetime = Field(default_factory=datetime.now, description="Profile creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class WorkingMemoryEntity(BaseModel):
    """Entity in working memory"""
    entity_type: str = Field(..., description="Entity type (city, hotel, customer, etc.)")
    entity_value: str = Field(..., description="Entity value")
    frequency: int = Field(default=1, description="Mention frequency in current conversation")
    first_seen: datetime = Field(default_factory=datetime.now, description="First mention time")
    last_seen: datetime = Field(default_factory=datetime.now, description="Last mention time")
    context: Dict[str, Any] = Field(default_factory=dict, description="Associated context")


# ============================================================================
# API Models
# ============================================================================

class ChatRequest(BaseModel):
    """API chat request"""
    query: str = Field(..., description="User query", min_length=1)
    user_id: str = Field(default="anonymous", description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for memory")
    mode: Literal["default", "thinking"] = Field(default="default", description="Execution mode")
    stream: bool = Field(default=False, description="Whether to stream response")


class ChatResponse(BaseModel):
    """API chat response"""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    complexity: Optional[QueryComplexity] = Field(None, description="Query complexity")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "unhealthy"] = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    components: Dict[str, bool] = Field(default_factory=dict, description="Component health status")


# ============================================================================
# Configuration Models
# ============================================================================

class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str = Field(..., description="Agent name")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    temperature: float = Field(default=0.7, description="LLM temperature", ge=0, le=2)
    max_retries: int = Field(default=3, description="Max retry attempts", ge=0)
    timeout_seconds: float = Field(default=30, description="Execution timeout", gt=0)
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific config")


class SystemConfig(BaseModel):
    """System-wide configuration"""
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="Agent configurations")
    llm_provider: str = Field(default="dashscope", description="LLM provider")
    embedding_model: str = Field(default="text-embedding-v2", description="Embedding model")
    enable_tracing: bool = Field(default=True, description="Enable LangSmith tracing")
    log_level: str = Field(default="INFO", description="Logging level")
