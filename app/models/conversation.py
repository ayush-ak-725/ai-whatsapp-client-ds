"""
Conversation models for the AI Backend service
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Message types"""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    EMOJI = "EMOJI"
    SYSTEM = "SYSTEM"


class ConversationMood(str, Enum):
    """Conversation moods"""
    CASUAL = "CASUAL"
    FORMAL = "FORMAL"
    HUMOROUS = "HUMOROUS"
    SERIOUS = "SERIOUS"
    EXCITED = "EXCITED"
    CALM = "CALM"
    DEBATE = "DEBATE"
    GOSSIP = "GOSSIP"
    PLANNING = "PLANNING"


class Character(BaseModel):
    """Character model"""
    id: UUID
    name: str
    personality_traits: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar_url: Optional[str] = None
    speaking_style: Optional[str] = None
    background: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class Group(BaseModel):
    """Group model"""
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class Message(BaseModel):
    """Message model"""
    id: UUID
    group_id: UUID
    character_id: UUID
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime
    is_ai_generated: bool = False
    response_time_ms: Optional[int] = None


class ConversationContext(BaseModel):
    """Conversation context for AI response generation"""
    group: Group
    current_character: Character
    recent_messages: List[Message] = Field(default_factory=list)
    active_characters: List[Character] = Field(default_factory=list)
    additional_context: Dict[str, Any] = Field(default_factory=dict)
    conversation_start_time: Optional[datetime] = None
    current_topic: Optional[str] = None
    mood: Optional[ConversationMood] = ConversationMood.CASUAL


class AIResponse(BaseModel):
    """AI response model"""
    content: str
    message_type: MessageType = MessageType.TEXT
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_interruption: bool = False
    reasoning: Optional[str] = None


class CharacterMemory(BaseModel):
    """Character memory model for vector storage"""
    character_id: UUID
    memory_type: str  # "conversation", "relationship", "preference", "fact"
    content: str
    importance_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSummary(BaseModel):
    """Conversation summary for context management"""
    group_id: UUID
    summary: str
    key_topics: List[str] = Field(default_factory=list)
    participants: List[UUID] = Field(default_factory=list)
    mood: ConversationMood = ConversationMood.CASUAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LLMRequest(BaseModel):
    """LLM request model"""
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """LLM response model"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    response_time_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)



