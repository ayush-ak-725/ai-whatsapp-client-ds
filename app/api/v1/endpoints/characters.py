"""
Character management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID
from app.models.conversation import Character
from app.services.character_service import CharacterService
from main import get_character_service

router = APIRouter()


@router.post("/", response_model=Character)
async def create_character(
    character_data: dict,
    character_service: CharacterService = Depends(get_character_service)
) -> Character:
    """
    Create a new character
    """
    try:
        character = await character_service.create_character(character_data)
        return character
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create character: {str(e)}")


@router.get("/{character_id}", response_model=Character)
async def get_character(
    character_id: UUID,
    character_service: CharacterService = Depends(get_character_service)
) -> Character:
    """
    Get character by ID
    """
    character = await character_service.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=Character)
async def update_character(
    character_id: UUID,
    updates: dict,
    character_service: CharacterService = Depends(get_character_service)
) -> Character:
    """
    Update character information
    """
    character = await character_service.update_character(character_id, updates)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.delete("/{character_id}")
async def delete_character(
    character_id: UUID,
    character_service: CharacterService = Depends(get_character_service)
):
    """
    Delete character
    """
    success = await character_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}


@router.get("/{character_id}/personality")
async def get_character_personality(
    character_id: UUID,
    character_service: CharacterService = Depends(get_character_service)
):
    """
    Get character personality information
    """
    personality = await character_service.get_character_personality(character_id)
    if not personality:
        raise HTTPException(status_code=404, detail="Character not found")
    return personality


@router.post("/{character_id}/enhance-personality")
async def enhance_character_personality(
    character_id: UUID,
    context: str,
    character_service: CharacterService = Depends(get_character_service)
):
    """
    Enhance character personality based on context
    """
    enhanced = await character_service.enhance_character_personality(character_id, context)
    if not enhanced:
        raise HTTPException(status_code=404, detail="Character not found")
    return enhanced


@router.get("/{character_id}/memories")
async def get_character_memories(
    character_id: UUID,
    memory_type: Optional[str] = None,
    character_service: CharacterService = Depends(get_character_service)
):
    """
    Get character memories
    """
    memories = await character_service.get_character_memories(character_id, memory_type)
    return {"memories": memories}


@router.post("/{character_id}/memories")
async def add_character_memory(
    character_id: UUID,
    content: str,
    memory_type: str = "conversation",
    importance_score: float = 0.5,
    character_service: CharacterService = Depends(get_character_service)
):
    """
    Add a new memory for a character
    """
    await character_service.add_character_memory(character_id, content, memory_type, importance_score)
    return {"message": "Memory added successfully"}



