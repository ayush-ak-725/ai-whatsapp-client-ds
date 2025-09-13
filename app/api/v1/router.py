"""
API Router for the AI Backend service
"""

from fastapi import APIRouter, Depends, HTTPException
from app.services.conversation_service import ConversationService
from app.services.character_service import CharacterService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.models.conversation import ConversationContext, AIResponse

# Create main router
api_router = APIRouter()

# Include sub-routers
from app.api.v1.endpoints import ai, characters, health

api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(characters.router, prefix="/characters", tags=["Characters"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])



