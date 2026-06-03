"""
FastAPI Routes
REST API endpoints for multi-agent system

Endpoints:
- POST /api/chat/sync - Synchronous chat
- POST /api/chat/stream - Server-Sent Events streaming
- DELETE /api/memory/clear - Clear conversation history
- GET /api/health - Health check
- GET /api/agents - List available agents
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from models.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    QueryComplexity
)
from agents.workflow_orchestrator import WorkflowOrchestrator
from memory.memory_service import MemoryService
import logging
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["api"])


# Dependency injection (will be configured in main.py)
def get_orchestrator() -> WorkflowOrchestrator:
    """Get workflow orchestrator instance"""
    # This will be overridden in main.py with actual instance
    raise NotImplementedError("Orchestrator not configured")


def get_memory_service() -> MemoryService:
    """Get memory service instance"""
    # This will be overridden in main.py with actual instance
    raise NotImplementedError("Memory service not configured")


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
    memory_service: MemoryService = Depends(get_memory_service)
) -> ChatResponse:
    """
    Synchronous chat endpoint

    Args:
        request: Chat request with query and user info

    Returns:
        Complete chat response

    Example:
        POST /api/chat/sync
        {
            "query": "What's the accommodation policy for Shanghai?",
            "user_id": "user123",
            "conversation_id": "conv456"
        }
    """
    start_time = time.time()

    try:
        logger.info(f"Chat request from user {request.user_id}: {request.query}")

        # Process user message through memory
        conversation_id = request.conversation_id or f"conv_{int(time.time())}"
        memory_service.process_user_message(
            user_id=request.user_id,
            conversation_id=conversation_id,
            message=request.query
        )

        # Route query through orchestrator
        response_text = orchestrator.route(
            query=request.query,
            chat_id=conversation_id,
            mode=request.mode
        )

        # Process assistant response through memory
        memory_service.process_assistant_message(
            user_id=request.user_id,
            conversation_id=conversation_id,
            message=response_text
        )

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000

        # Build response
        response = ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            complexity=None,  # Could be extracted from orchestrator
            execution_time_ms=execution_time,
            sources=[],
            metadata={
                "mode": request.mode,
                "user_id": request.user_id
            }
        )

        logger.info(f"Chat completed in {execution_time:.2f}ms")
        return response

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
    memory_service: MemoryService = Depends(get_memory_service)
) -> StreamingResponse:
    """
    Streaming chat endpoint using Server-Sent Events

    Args:
        request: Chat request with query and user info

    Returns:
        SSE stream of response chunks

    Example:
        POST /api/chat/stream
        {
            "query": "Plan a trip to Hangzhou",
            "user_id": "user123"
        }

        Response (SSE):
        data: {"chunk": "Planning", "done": false}
        data: {"chunk": " your trip", "done": false}
        data: {"chunk": "...", "done": true}
    """
    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE stream"""
        try:
            conversation_id = request.conversation_id or f"conv_{int(time.time())}"

            # Process user message
            memory_service.process_user_message(
                user_id=request.user_id,
                conversation_id=conversation_id,
                message=request.query
            )

            # Send initial event
            yield f"data: {json.dumps({'status': 'processing', 'done': False})}\n\n"

            # Route query (non-streaming for now, could be enhanced)
            response_text = orchestrator.route(
                query=request.query,
                chat_id=conversation_id,
                mode=request.mode
            )

            # Stream response in chunks
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

            # Process assistant response
            memory_service.process_assistant_message(
                user_id=request.user_id,
                conversation_id=conversation_id,
                message=response_text
            )

            # Send completion event
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/memory/clear")
async def clear_memory(
    user_id: str,
    conversation_id: str = None,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Clear conversation history

    Args:
        user_id: User identifier
        conversation_id: Conversation to clear (optional, clears all if not provided)

    Returns:
        Success message

    Example:
        DELETE /api/memory/clear?user_id=user123&conversation_id=conv456
    """
    try:
        if conversation_id:
            memory_service.clear_conversation(user_id, conversation_id)
            message = f"Cleared conversation {conversation_id}"
        else:
            memory_service.clear_all_conversations(user_id)
            message = f"Cleared all conversations for user {user_id}"

        logger.info(message)
        return {"success": True, "message": message}

    except Exception as e:
        logger.error(f"Clear memory failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clear memory failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
    memory_service: MemoryService = Depends(get_memory_service)
) -> HealthResponse:
    """
    Health check endpoint

    Returns:
        Service health status

    Example:
        GET /api/health
    """
    components = {}

    # Check orchestrator
    try:
        components["orchestrator"] = orchestrator is not None
    except:
        components["orchestrator"] = False

    # Check memory service
    try:
        components["memory_service"] = memory_service is not None
    except:
        components["memory_service"] = False

    # Overall status
    status = "healthy" if all(components.values()) else "unhealthy"

    return HealthResponse(
        status=status,
        version="1.0.0",
        timestamp=datetime.now(),
        components=components
    )


@router.get("/agents")
async def list_agents(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """
    List available agents

    Returns:
        List of agent names and descriptions

    Example:
        GET /api/agents
    """
    agents = [
        {
            "name": "ComplexityAssessor",
            "description": "Assesses query complexity for routing (80% rule + 20% LLM)",
            "status": "active"
        },
        {
            "name": "TaskDecomposer",
            "description": "Decomposes complex queries into subtasks with dependency management",
            "status": "active"
        },
        {
            "name": "TripPlannerAgent",
            "description": "Coordinates multi-city trip planning with parallel execution",
            "status": "active"
        },
        {
            "name": "PolicyAdvisorAgent",
            "description": "Answers policy questions using hybrid RAG (80% accuracy)",
            "status": "active"
        },
        {
            "name": "ExpenseTrackerAgent",
            "description": "Tracks and validates expenses against policy",
            "status": "planned"
        },
        {
            "name": "ApprovalOrchestratorAgent",
            "description": "Manages approval workflows with state machine",
            "status": "planned"
        },
        {
            "name": "TravelIntelligenceAgent",
            "description": "Provides real-time travel information (weather, flights, hotels)",
            "status": "planned"
        },
        {
            "name": "MemoryManagerAgent",
            "description": "Manages three-layer memory system for personalization",
            "status": "active"
        }
    ]

    return {
        "agents": agents,
        "total": len(agents),
        "active": len([a for a in agents if a["status"] == "active"])
    }


@router.get("/stats")
async def get_stats(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Get system statistics

    Returns:
        System usage statistics

    Example:
        GET /api/stats
    """
    # This would be enhanced with actual metrics
    return {
        "total_conversations": 0,  # Would query from memory service
        "total_users": 0,
        "avg_response_time_ms": 0,
        "cache_hit_rate": 0,
        "uptime_seconds": 0
    }
