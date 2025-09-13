"""
Vector Service for managing embeddings and vector database operations
"""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID

import structlog
from app.core.config import settings
from app.models.conversation import CharacterMemory, ConversationSummary

logger = structlog.get_logger(__name__)


class VectorService:
    """Service for managing vector operations with Pinecone"""
    
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.CHARACTER_EMBEDDING_DIMENSION
        self._index = None
        self._pinecone = None
    
    async def initialize(self):
        """Initialize Pinecone client and index"""
        try:
            import pinecone
            from pinecone import Pinecone
            
            # Initialize Pinecone
            pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            if self.index_name not in pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec={
                        "serverless": {
                            "cloud": "aws",
                            "region": self.environment
                        }
                    }
                )
            
            # Connect to index
            self._index = pc.Index(self.index_name)
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize vector service", error=str(e))
            raise
    
    async def store_character_memory(self, memory: CharacterMemory, embedding: List[float]) -> str:
        """Store character memory with embedding"""
        try:
            vector_id = f"memory_{memory.character_id}_{memory.memory_type}_{memory.created_at.timestamp()}"
            
            metadata = {
                "character_id": str(memory.character_id),
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance_score": memory.importance_score,
                "created_at": memory.created_at.isoformat(),
                **memory.metadata
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.upsert(
                    vectors=[(vector_id, embedding, metadata)]
                )
            )
            
            logger.debug("Stored character memory", character_id=memory.character_id, memory_type=memory.memory_type)
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store character memory", error=str(e))
            raise
    
    async def search_similar_memories(self, 
                                    character_id: UUID, 
                                    query_embedding: List[float], 
                                    memory_type: Optional[str] = None,
                                    top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memories for a character"""
        try:
            filter_dict = {"character_id": str(character_id)}
            if memory_type:
                filter_dict["memory_type"] = memory_type
            
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.query(
                    vector=query_embedding,
                    filter=filter_dict,
                    top_k=top_k,
                    include_metadata=True
                )
            )
            
            memories = []
            for match in results.matches:
                memories.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.debug("Found similar memories", character_id=character_id, count=len(memories))
            return memories
            
        except Exception as e:
            logger.error("Failed to search similar memories", error=str(e))
            raise
    
    async def store_conversation_summary(self, summary: ConversationSummary, embedding: List[float]) -> str:
        """Store conversation summary with embedding"""
        try:
            vector_id = f"summary_{summary.group_id}_{summary.created_at.timestamp()}"
            
            metadata = {
                "group_id": str(summary.group_id),
                "summary": summary.summary,
                "key_topics": summary.key_topics,
                "participants": [str(p) for p in summary.participants],
                "mood": summary.mood.value,
                "created_at": summary.created_at.isoformat(),
                "updated_at": summary.updated_at.isoformat()
            }
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.upsert(
                    vectors=[(vector_id, embedding, metadata)]
                )
            )
            
            logger.debug("Stored conversation summary", group_id=summary.group_id)
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store conversation summary", error=str(e))
            raise
    
    async def search_conversation_context(self, 
                                        group_id: UUID, 
                                        query_embedding: List[float], 
                                        top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant conversation context"""
        try:
            filter_dict = {"group_id": str(group_id)}
            
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.query(
                    vector=query_embedding,
                    filter=filter_dict,
                    top_k=top_k,
                    include_metadata=True
                )
            )
            
            contexts = []
            for match in results.matches:
                contexts.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.debug("Found conversation context", group_id=group_id, count=len(contexts))
            return contexts
            
        except Exception as e:
            logger.error("Failed to search conversation context", error=str(e))
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using a simple method"""
        try:
            # For production, use a proper embedding model like OpenAI's text-embedding-ada-002
            # or sentence-transformers
            import hashlib
            import struct
            
            # Simple hash-based embedding (not recommended for production)
            # This is just for demonstration - use a proper embedding model
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to float vector
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                if len(embedding) >= self.dimension:
                    break
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    value = struct.unpack('>f', chunk)[0]
                    embedding.append(value)
            
            # Pad or truncate to required dimension
            while len(embedding) < self.dimension:
                embedding.append(0.0)
            
            embedding = embedding[:self.dimension]
            
            # Normalize
            import math
            norm = math.sqrt(sum(x*x for x in embedding))
            if norm > 0:
                embedding = [x/norm for x in embedding]
            
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise
    
    async def delete_character_memories(self, character_id: UUID) -> int:
        """Delete all memories for a character"""
        try:
            # Note: Pinecone doesn't support bulk delete by metadata filter
            # This would require querying first, then deleting individual vectors
            # For now, we'll just log the request
            logger.info("Delete character memories requested", character_id=character_id)
            return 0
            
        except Exception as e:
            logger.error("Failed to delete character memories", error=str(e))
            raise
    
    async def is_healthy(self) -> bool:
        """Check if vector service is healthy"""
        try:
            if not self._index:
                return False
            
            # Simple health check
            stats = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.describe_index_stats()
            )
            
            return stats is not None
            
        except Exception as e:
            logger.error("Vector service health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close vector service connections"""
        logger.info("Closing vector service")
        # Pinecone doesn't require explicit closing
        pass



