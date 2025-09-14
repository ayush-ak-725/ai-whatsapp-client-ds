"""
AI endpoints for response generation
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.conversation import ConversationContext, AIResponse
from app.api.v1.dependencies import get_conversation_service, get_llm_service
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService
# from main import get_conversation_service, get_llm_service

router = APIRouter()


@router.post("/generate-response", response_model=AIResponse)
async def generate_response(
    context: ConversationContext,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> AIResponse:
    """
    Generate AI response for the given conversation context
    """
    try:
        response = await conversation_service.generate_response(context)
        return response
    except Exception as e:
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






