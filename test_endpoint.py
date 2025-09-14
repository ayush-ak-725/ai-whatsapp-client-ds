#!/usr/bin/env python3
"""
Test script for the generate-response endpoint
"""

import requests
import json
from datetime import datetime

# Test data for the endpoint
test_data = {
    "group": {
        "id": "test-group-1",
        "name": "Test Group",
        "description": "Test group for AI responses",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": None
    },
    "current_character": {
        "id": "test-char-1",
        "name": "Test AI",
        "personality_traits": "Helpful and friendly",
        "system_prompt": "You are a helpful AI assistant",
        "avatar_url": None,
        "speaking_style": "casual",
        "background": "AI assistant",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": None
    },
    "recent_messages": [
        {
            "id": "msg-1",
            "group_id": "test-group-1",
            "character_id": "test-char-1",
            "content": "Hello! How are you today?",
            "message_type": "TEXT",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "is_ai_generated": False,
            "response_time_ms": None
        }
    ],
    "active_characters": [],
    "additional_context": {},
    "conversation_start_time": datetime.utcnow().isoformat() + "Z",
    "current_topic": "greeting",
    "mood": "CASUAL"
}

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_generate_response():
    """Test the generate-response endpoint"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ai/generate-response",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        print(f"Generate Response Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Generate response test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing AI WhatsApp Backend Endpoints...")
    print("=" * 50)
    
    # Test health first
    if test_health():
        print("\n✅ Health check passed")
        
        # Test generate response
        if test_generate_response():
            print("\n✅ Generate response test passed")
        else:
            print("\n❌ Generate response test failed")
    else:
        print("\n❌ Health check failed - service not running")
