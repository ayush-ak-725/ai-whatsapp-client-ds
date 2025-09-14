"""
Bakchod AI WhatsApp - AI Backend Service

This FastAPI service handles AI/ML operations including:
- LLM integration with multiple providers
- Character personality management
- Conversation context processing
- Vector database operations
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import structlog
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.character_service import CharacterService
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.api.v1.router import api_router
from app.models.conversation import ConversationContext, AIResponse

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Bakchod AI WhatsApp Backend")
    
    # Initialize services
    try:
        # Initialize vector service
        vector_service = VectorService()
        await vector_service.initialize()
        app.state.vector_service = vector_service
        
        # Initialize LLM service
        llm_service = LLMService()
        await llm_service.initialize()
        app.state.llm_service = llm_service
        
        # Initialize character service
        character_service = CharacterService(vector_service)
        app.state.character_service = character_service
        
        # Initialize conversation service
        conversation_service = ConversationService(llm_service, vector_service, character_service)
        app.state.conversation_service = conversation_service
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Bakchod AI WhatsApp Backend")
    if hasattr(app.state, 'vector_service'):
        await app.state.vector_service.close()
    if hasattr(app.state, 'llm_service'):
        await app.state.llm_service.close()


# Create FastAPI app
app = FastAPI(
    title="Bakchod AI WhatsApp - AI Backend",
    description="AI/ML backend service for WhatsApp-style group chat with AI celebrities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bakchod AI WhatsApp - AI Backend Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if services are healthy
        services_status = {}
        
        if hasattr(app.state, 'llm_service'):
            services_status['llm_service'] = await app.state.llm_service.is_healthy()
        
        if hasattr(app.state, 'vector_service'):
            services_status['vector_service'] = await app.state.vector_service.is_healthy()
        
        all_healthy = all(services_status.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "services": services_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


@app.get("/info")
async def info():
    """Service information endpoint"""
    return {
        "name": "Bakchod AI WhatsApp - AI Backend",
        "version": "1.0.0",
        "description": "AI/ML backend service for WhatsApp-style group chat",
        "features": [
            "Multi-LLM support (Gemini, OpenAI, Anthropic, Hugging Face)",
            "Character personality management",
            "Conversation context processing",
            "Vector database integration",
            "Real-time response generation"
        ],
        "supported_llms": [
            "Google Gemini",
            "OpenAI GPT-4",
            "Anthropic Claude",
            "Hugging Face Models"
        ]
    }


# Dependency injection functions moved to app.api.v1.dependencies


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


