"""
Conversation Service for managing AI conversations and context
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from uuid import UUID

import structlog
from app.core.config import settings
from app.models.conversation import (
    ConversationContext, 
    AIResponse, 
    CharacterMemory, 
    ConversationSummary,
    Message,
    ConversationMood,
    MessageType
)
from app.services.llm_service import LLMService, LLMRequest
from app.services.vector_service import VectorService
from app.services.character_service import CharacterService

logger = structlog.get_logger(__name__)


class ConversationService:
    """Service for managing AI conversations and context"""
    
    def __init__(self, llm_service: LLMService, vector_service: VectorService, character_service: CharacterService):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.character_service = character_service
    
    async def generate_response(self, context: ConversationContext) -> AIResponse:
        """Generate AI response for the given conversation context"""
        start_time = time.time()
        
        try:
            logger.info("Generating AI response", 
                       character=context.current_character.name,
                       group=context.group.name)
            
            # Build the prompt
            prompt = await self._build_prompt(context)
            
            # Generate response using LLM
            llm_request = LLMRequest(
                prompt=prompt,
                max_tokens=settings.MAX_RESPONSE_LENGTH,
                temperature=0.8,
                top_p=0.9
            )
            
            llm_response = await self.llm_service.generate_response(llm_request)
            
            # Process and enhance the response
            ai_response = await self._process_response(llm_response, context)
            
            # Store conversation context
            await self._store_conversation_context(context, ai_response)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            ai_response.response_time_ms = response_time_ms
            
            logger.info("Generated AI response", 
                       character=context.current_character.name,
                       response_time_ms=response_time_ms,
                       content_length=len(ai_response.content))
            
            return ai_response
            
        except Exception as e:
            logger.error("Failed to generate AI response", error=str(e))
            # Return fallback response
            return self._create_fallback_response()
    
    async def _build_prompt(self, context: ConversationContext) -> str:
        """Build the prompt for AI response generation"""
        
        # Character system prompt
        system_prompt = context.current_character.system_prompt or ""
        personality_traits = context.current_character.personality_traits or ""
        speaking_style = context.current_character.speaking_style or ""
        background = context.current_character.background or ""
        
        # Build character context
        character_context = f"""
You are {context.current_character.name}, a {personality_traits} character.
{system_prompt}

Speaking style: {speaking_style}
Background: {background}
"""
        
        # Build conversation context
        conversation_context = f"""
You are participating in a group chat with the following members:
{', '.join([char.name for char in context.active_characters])}

Current conversation mood: {context.mood.value if context.mood else 'CASUAL'}
Current topic: {context.current_topic or 'General conversation'}
"""
        
        # Build recent messages context
        messages_context = ""
        if context.recent_messages:
            messages_context = "\nRecent conversation:\n"
            for msg in context.recent_messages[-10:]:  # Last 10 messages
                messages_context += f"{msg.character_id}: {msg.content}\n"
        
        # Build additional context
        additional_context = ""
        if context.additional_context:
            additional_context = "\nAdditional context:\n"
            for key, value in context.additional_context.items():
                additional_context += f"{key}: {value}\n"
        
        # Build the complete prompt
        prompt = f"""
{character_context}

{conversation_context}

{messages_context}

{additional_context}

Instructions:
- Respond naturally as {context.current_character.name}
- Keep your response conversational and engaging
- Stay in character based on your personality and background
- Respond to the conversation context appropriately
- Keep responses concise but meaningful
- Use your speaking style consistently

Respond now:
"""
        
        return prompt.strip()
    
    async def _process_response(self, llm_response, context: ConversationContext) -> AIResponse:
        """Process and enhance the LLM response"""
        
        # Clean up the response
        content = llm_response.content.strip()
        
        # Remove any unwanted prefixes or suffixes
        if content.startswith(f"{context.current_character.name}:"):
            content = content[len(f"{context.current_character.name}:"):].strip()
        
        # Ensure response is not too long
        if len(content) > settings.MAX_RESPONSE_LENGTH:
            content = content[:settings.MAX_RESPONSE_LENGTH] + "..."
        
        # Create AI response
        ai_response = AIResponse(
            content=content,
            message_type=MessageType.TEXT,
            confidence=0.8,  # Default confidence
            model_used=llm_response.model,
            response_time_ms=llm_response.response_time_ms,
            metadata={
                "provider": llm_response.metadata.get("provider", "unknown"),
                "usage": llm_response.usage,
                "finish_reason": llm_response.finish_reason
            }
        )
        
        # Add reasoning if available
        if llm_response.metadata.get("reasoning"):
            ai_response.reasoning = llm_response.metadata["reasoning"]
        
        return ai_response
    
    async def _store_conversation_context(self, context: ConversationContext, response: AIResponse):
        """Store conversation context for future reference"""
        try:
            # Create character memory
            memory = CharacterMemory(
                character_id=context.current_character.id,
                memory_type="conversation",
                content=response.content,
                importance_score=0.7,
                metadata={
                    "group_id": str(context.group.id),
                    "mood": context.mood.value if context.mood else "CASUAL",
                    "topic": context.current_topic or "general"
                }
            )
            
            # Generate embedding for the memory
            embedding = await self.vector_service.generate_embedding(response.content)
            
            # Store the memory
            await self.vector_service.store_character_memory(memory, embedding)
            
            # Update conversation summary if needed
            await self._update_conversation_summary(context, response)
            
        except Exception as e:
            logger.error("Failed to store conversation context", error=str(e))
    
    async def _update_conversation_summary(self, context: ConversationContext, response: AIResponse):
        """Update conversation summary"""
        try:
            # This is a simplified version - in production, you'd want more sophisticated summarization
            summary_text = f"Conversation in {context.group.name} with {len(context.active_characters)} participants. " \
                          f"Current mood: {context.mood.value if context.mood else 'CASUAL'}. " \
                          f"Latest message from {context.current_character.name}: {response.content[:100]}..."
            
            summary = ConversationSummary(
                group_id=context.group.id,
                summary=summary_text,
                key_topics=[context.current_topic] if context.current_topic else [],
                participants=[char.id for char in context.active_characters],
                mood=context.mood or ConversationMood.CASUAL
            )
            
            # Generate embedding for the summary
            embedding = await self.vector_service.generate_embedding(summary_text)
            
            # Store the summary
            await self.vector_service.store_conversation_summary(summary, embedding)
            
        except Exception as e:
            logger.error("Failed to update conversation summary", error=str(e))
    
    async def get_character_memories(self, character_id: UUID, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant memories for a character"""
        try:
            # Generate embedding for the query
            query_embedding = await self.vector_service.generate_embedding(query)
            
            # Search for similar memories
            memories = await self.vector_service.search_similar_memories(
                character_id=character_id,
                query_embedding=query_embedding,
                top_k=limit
            )
            
            return memories
            
        except Exception as e:
            logger.error("Failed to get character memories", error=str(e))
            return []
    
    async def get_conversation_context(self, group_id: UUID, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get relevant conversation context for a group"""
        try:
            # Generate embedding for the query
            query_embedding = await self.vector_service.generate_embedding(query)
            
            # Search for similar conversation context
            contexts = await self.vector_service.search_conversation_context(
                group_id=group_id,
                query_embedding=query_embedding,
                top_k=limit
            )
            
            return contexts
            
        except Exception as e:
            logger.error("Failed to get conversation context", error=str(e))
            return []
    
    def _create_fallback_response(self) -> AIResponse:
        """Create a fallback response when AI generation fails"""
        fallback_responses = [
            "Hmm, let me think about that...",
            "That's an interesting point!",
            "I'm not sure what to say about that.",
            "Can you tell me more about that?",
            "That's something to consider...",
            "I see what you mean.",
            "That's a good question!",
            "Let me process that for a moment..."
        ]
        
        import random
        content = random.choice(fallback_responses)
        
        return AIResponse(
            content=content,
            message_type=MessageType.TEXT,
            confidence=0.1,
            model_used="fallback",
            response_time_ms=0,
            metadata={"fallback": True}
        )
    
    async def is_healthy(self) -> bool:
        """Check if conversation service is healthy"""
        try:
            return (await self.llm_service.is_healthy() and 
                   await self.vector_service.is_healthy())
        except Exception as e:
            logger.error("Conversation service health check failed", error=str(e))
            return False



