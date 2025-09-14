from fastapi import HTTPException, Request
from app.services.character_service import CharacterService
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService

def get_conversation_service(request: Request) -> ConversationService:
    if not hasattr(request.app.state, "conversation_service"):
        raise HTTPException(status_code=503, detail="Conversation service not initialized")
    return request.app.state.conversation_service

def get_llm_service(request: Request) -> LLMService:
    if not hasattr(request.app.state, "llm_service"):
        raise HTTPException(status_code=503, detail="LLM service not initialized")
    return request.app.state.llm_service

def get_character_service(request: Request) -> CharacterService:
    if not hasattr(request.app.state, "character_service"):
        raise HTTPException(status_code=503, detail="Character service not initialized")
    return request.app.state.character_service

def get_vector_service(request: Request) -> VectorService:
    if not hasattr(request.app.state, "vector_service"):
        raise HTTPException(status_code=503, detail="Vector service not initialized")
    return request.app.state.vector_service
