"""
Vector Service for managing embeddings and vector database operations using Pinecone
"""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID

import structlog
import pinecone
from app.core.config import settings
from app.models.conversation import CharacterMemory, ConversationSummary

logger = structlog.get_logger(__name__)


class VectorService:
    """Service for managing vector operations with Pinecone"""

    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.environment = "us-east-1"
        self.index_name = "character-memories"
        self.dimension = 1536  # typical for OpenAI embeddings
        self._index = None

    async def initialize(self):
        """Initialize Pinecone client and index"""
        try:
            if not self.api_key:
                logger.warning("Pinecone API key not provided. Vector service disabled.")
                return

            from pinecone import Pinecone, ServerlessSpec
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=self.api_key)
            
            logger.info("Pinecone client initialized", index_name=self.index_name, environment=self.environment)

            # Get existing indexes
            existing_indexes = pc.list_indexes()
            logger.info(f"Existing indexes: {existing_indexes}")

            # Create index if missing
            if self.index_name not in existing_indexes.names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment
                    )
                )
                logger.info(f"Pinecone index '{self.index_name}' created")

            # Connect to the index
            self._index = pc.Index(self.index_name)
            logger.info("Vector service initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize vector service: {e}")
            self._index = None

    async def store_character_memory(self, memory: CharacterMemory, embedding: List[float]) -> str:
        """Store character memory with embedding"""
        if not self._index:
            logger.warning("Vector service not initialized. Skipping memory storage.")
            return ""

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
            lambda: self._index.upsert(vectors=[(vector_id, embedding, metadata)])
        )
        logger.debug("Stored character memory", character_id=memory.character_id, memory_type=memory.memory_type)
        return vector_id

    async def search_similar_memories(
        self,
        character_id: UUID,
        query_embedding: List[float],
        memory_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar memories for a character"""
        if not self._index:
            return []

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
        return [
            {"id": match.id, "score": match.score, "metadata": match.metadata}
            for match in results.matches
        ]

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's embeddings"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.embeddings.create(model="text-embedding-ada-002", input=text)
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if vector service is ready"""
        if not self._index:
            return False
        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.describe_index_stats()
            )
            return stats is not None
        except Exception as e:
            logger.error("Vector service health check failed", error=str(e))
            return False

    async def close(self):
        """Close vector service"""
        logger.info("Closing vector service")
        # Pinecone client does not require explicit shutdown
        self._index = None
