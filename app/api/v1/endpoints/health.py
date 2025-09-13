"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from app.services.conversation_service import ConversationService
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from main import get_conversation_service, get_character_service, get_llm_service, get_vector_service

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check
    """
    return {"status": "healthy", "service": "ai-backend"}


@router.get("/detailed")
async def detailed_health_check(
    conversation_service: ConversationService = Depends(get_conversation_service),
    character_service: CharacterService = Depends(get_character_service),
    llm_service: LLMService = Depends(get_llm_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Detailed health check for all services
    """
    services_status = {
        "conversation_service": await conversation_service.is_healthy(),
        "character_service": await character_service.is_healthy(),
        "llm_service": await llm_service.is_healthy(),
        "vector_service": await vector_service.is_healthy()
    }
    
    all_healthy = all(services_status.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "services": services_status
    }



