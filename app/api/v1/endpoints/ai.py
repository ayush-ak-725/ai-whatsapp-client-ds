"""
AI endpoints for response generation
"""

import time
from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.conversation import ConversationContext, AIResponse
from app.api.v1.dependencies import get_conversation_service, get_llm_service
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/generate-response", response_model=AIResponse)
async def generate_response(
    request: Request,
    context: ConversationContext,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> AIResponse:
    """
    Generate AI response for the given conversation context
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(
        "AI generation request received",
        client_ip=client_ip,
        group_id=str(context.group.id),
        character_id=str(context.current_character.id),
        character_name=context.current_character.name,
        group_name=context.group.name,
        message_count=len(context.recent_messages),
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        # Log the incoming context details
        logger.debug(
            "Conversation context details",
            group_id=str(context.group.id),
            character_id=str(context.current_character.id),
            recent_messages=[{
                "id": str(msg.id),
                "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "is_ai_generated": msg.is_ai_generated
            } for msg in context.recent_messages[-3:]],  # Log last 3 messages
            active_characters=[{
                "id": str(char.id),
                "name": char.name,
                "is_active": char.is_active
            } for char in context.active_characters],
            mood=context.mood,
            current_topic=context.current_topic
        )
        
        response = await conversation_service.generate_response(context)
        
        processing_time = time.time() - start_time
        
        logger.info(
            "AI generation completed successfully",
            client_ip=client_ip,
            group_id=str(context.group.id),
            character_id=str(context.current_character.id),
            character_name=context.current_character.name,
            response_length=len(response.content),
            response_time_ms=int(processing_time * 1000),
            model_used=response.model_used,
            confidence=response.confidence
        )
        
        # Log the response content (truncated for security)
        logger.debug(
            "AI response content",
            group_id=str(context.group.id),
            character_id=str(context.current_character.id),
            response_content=response.content[:200] + "..." if len(response.content) > 200 else response.content,
            metadata=response.metadata
        )
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            "AI generation failed",
            client_ip=client_ip,
            group_id=str(context.group.id),
            character_id=str(context.current_character.id),
            character_name=context.current_character.name,
            error=str(e),
            response_time_ms=int(processing_time * 1000),
            exc_info=True
        )
        
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@router.post("/enhance-context")
async def enhance_context(
    group_id: str,
    character_id: str,
    query: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Enhance conversation context with relevant memories
    """
    try:
        from uuid import UUID
        memories = await conversation_service.get_character_memories(
            character_id=UUID(character_id),
            query=query
        )
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enhance context: {str(e)}")


@router.get("/models")
async def get_available_models(
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Get list of available AI models
    """
    try:
        # This would return available models from the LLM service
        return {
            "available_models": [
                "gemini-pro",
                "gpt-4",
                "claude-3-sonnet",
                "microsoft/DialoGPT-medium"
            ],
            "current_model": "auto-selected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")
