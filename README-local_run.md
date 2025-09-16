#Running using virtual env

## In the project directory, you can run:

## `py -3.11 -m venv venv`
## `python --version` (check that your python version inside the vm is 3.11)
## `venv\Scripts\Activate.ps1`
## `pip install -r requirements.txt`
## `python main.py`

## Add your own credentials for:- openai, gemini, pinecone in "app/api/core/config.py

## curl to test the generate-response api

curl --location 'http://localhost:8000/api/v1/ai/generate-response' \
--header 'accept: application/json' \
--header 'Content-Type: application/json' \
--data '{
  "group": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "MAB",
    "description": "string",
    "is_active": true,
    "created_at": "2025-09-15T14:13:20.806Z",
    "updated_at": "2025-09-15T14:13:20.806Z"
  },
  "current_character": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Ayush",
    "personality_traits": "Humorous & speaks a lot",
    "system_prompt": "string",
    "avatar_url": "string",
    "speaking_style": "casual",
    "background": "string",
    "is_active": true,
    "created_at": "2025-09-15T14:13:20.807Z",
    "updated_at": "2025-09-15T14:13:20.808Z"
  },
  "recent_messages": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "group_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "character_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "content": "string",
      "message_type": "TEXT",
      "timestamp": "2025-09-15T14:13:20.808Z",
      "is_ai_generated": false,
      "response_time_ms": 0
    }
  ],
  "active_characters": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "personality_traits": "string",
      "system_prompt": "string",
      "avatar_url": "string",
      "speaking_style": "string",
      "background": "string",
      "is_active": true,
      "created_at": "2025-09-15T14:13:20.808Z",
      "updated_at": "2025-09-15T14:13:20.808Z"
    }
  ],
  "additional_context": {},
  "conversation_start_time": "2025-09-15T14:13:20.808Z",
  "current_topic": "string",
  "mood": "CASUAL"
}'
`

