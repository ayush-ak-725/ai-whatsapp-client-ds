"""
Character Service for managing AI character personalities and behaviors
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

import structlog
from app.models.conversation import Character, CharacterMemory
from app.services.vector_service import VectorService

logger = structlog.get_logger(__name__)


class CharacterService:
    """Service for managing AI character personalities and behaviors"""
    
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
        self._character_cache: Dict[UUID, Character] = {}
    
    async def create_character(self, character_data: Dict[str, Any]) -> Character:
        """Create a new character with personality traits"""
        try:
            character = Character(**character_data)
            
            # Store character in cache
            self._character_cache[character.id] = character
            
            # Create initial character memory
            await self._create_initial_memory(character)
            
            logger.info("Created character", character_id=character.id, name=character.name)
            return character
            
        except Exception as e:
            logger.error("Failed to create character", error=str(e))
            raise
    
    async def get_character(self, character_id: UUID) -> Optional[Character]:
        """Get character by ID"""
        # Check cache first
        if character_id in self._character_cache:
            return self._character_cache[character_id]
        
        # In a real implementation, you'd fetch from database
        # For now, return None
        return None
    
    async def update_character(self, character_id: UUID, updates: Dict[str, Any]) -> Optional[Character]:
        """Update character information"""
        try:
            character = await self.get_character(character_id)
            if not character:
                return None
            
            # Update character fields
            for key, value in updates.items():
                if hasattr(character, key):
                    setattr(character, key, value)
            
            # Update cache
            self._character_cache[character_id] = character
            
            # Update character memory if personality changed
            if "personality_traits" in updates or "system_prompt" in updates:
                await self._update_character_memory(character)
            
            logger.info("Updated character", character_id=character_id, name=character.name)
            return character
            
        except Exception as e:
            logger.error("Failed to update character", error=str(e))
            raise
    
    async def delete_character(self, character_id: UUID) -> bool:
        """Delete character and all associated memories"""
        try:
            # Remove from cache
            if character_id in self._character_cache:
                del self._character_cache[character_id]
            
            # Delete character memories
            await self.vector_service.delete_character_memories(character_id)
            
            logger.info("Deleted character", character_id=character_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete character", error=str(e))
            return False
    
    async def get_character_personality(self, character_id: UUID) -> Optional[Dict[str, Any]]:
        """Get character personality information"""
        character = await self.get_character(character_id)
        if not character:
            return None
        
        return {
            "name": character.name,
            "personality_traits": character.personality_traits,
            "system_prompt": character.system_prompt,
            "speaking_style": character.speaking_style,
            "background": character.background,
            "avatar_url": character.avatar_url
        }
    
    async def enhance_character_personality(self, character_id: UUID, context: str) -> Optional[Dict[str, Any]]:
        """Enhance character personality based on conversation context"""
        try:
            character = await self.get_character(character_id)
            if not character:
                return None
            
            # Get relevant memories
            memories = await self.vector_service.search_similar_memories(
                character_id=character_id,
                query_embedding=await self.vector_service.generate_embedding(context),
                memory_type="conversation",
                top_k=5
            )
            
            # Build enhanced personality context
            enhanced_context = {
                "base_personality": {
                    "traits": character.personality_traits,
                    "speaking_style": character.speaking_style,
                    "background": character.background
                },
                "recent_memories": memories,
                "context": context
            }
            
            return enhanced_context
            
        except Exception as e:
            logger.error("Failed to enhance character personality", error=str(e))
            return None
    
    async def _create_initial_memory(self, character: Character):
        """Create initial memory for a new character"""
        try:
            # Create personality memory
            personality_memory = CharacterMemory(
                character_id=character.id,
                memory_type="personality",
                content=f"Character: {character.name}. Traits: {character.personality_traits}. Background: {character.background}",
                importance_score=1.0,
                metadata={
                    "type": "initial_personality",
                    "created_at": character.created_at.isoformat()
                }
            )
            
            # Generate embedding and store
            embedding = await self.vector_service.generate_embedding(personality_memory.content)
            await self.vector_service.store_character_memory(personality_memory, embedding)
            
            logger.debug("Created initial memory for character", character_id=character.id)
            
        except Exception as e:
            logger.error("Failed to create initial character memory", error=str(e))
    
    async def _update_character_memory(self, character: Character):
        """Update character memory when personality changes"""
        try:
            # Create updated personality memory
            personality_memory = CharacterMemory(
                character_id=character.id,
                memory_type="personality",
                content=f"Updated character: {character.name}. Traits: {character.personality_traits}. Background: {character.background}",
                importance_score=1.0,
                metadata={
                    "type": "updated_personality",
                    "updated_at": character.updated_at.isoformat() if character.updated_at else None
                }
            )
            
            # Generate embedding and store
            embedding = await self.vector_service.generate_embedding(personality_memory.content)
            await self.vector_service.store_character_memory(personality_memory, embedding)
            
            logger.debug("Updated character memory", character_id=character.id)
            
        except Exception as e:
            logger.error("Failed to update character memory", error=str(e))
    
    async def get_character_memories(self, character_id: UUID, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all memories for a character"""
        try:
            # Generate a generic query embedding
            query_embedding = await self.vector_service.generate_embedding("character memories")
            
            # Search for memories
            memories = await self.vector_service.search_similar_memories(
                character_id=character_id,
                query_embedding=query_embedding,
                memory_type=memory_type,
                top_k=20
            )
            
            return memories
            
        except Exception as e:
            logger.error("Failed to get character memories", error=str(e))
            return []
    
    async def add_character_memory(self, character_id: UUID, content: str, memory_type: str = "conversation", importance_score: float = 0.5):
        """Add a new memory for a character"""
        try:
            memory = CharacterMemory(
                character_id=character_id,
                memory_type=memory_type,
                content=content,
                importance_score=importance_score
            )
            
            # Generate embedding and store
            embedding = await self.vector_service.generate_embedding(content)
            await self.vector_service.store_character_memory(memory, embedding)
            
            logger.debug("Added character memory", character_id=character_id, memory_type=memory_type)
            
        except Exception as e:
            logger.error("Failed to add character memory", error=str(e))
    
    async def is_healthy(self) -> bool:
        """Check if character service is healthy"""
        try:
            return await self.vector_service.is_healthy()
        except Exception as e:
            logger.error("Character service health check failed", error=str(e))
            return False






