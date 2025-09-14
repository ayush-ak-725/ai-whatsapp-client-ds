"""
LLM Service for handling multiple AI providers
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Optional

import structlog
from app.core.config import settings
from app.models.conversation import LLMRequest, LLMResponse

logger = structlog.get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from the LLM provider"""
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if the provider is healthy"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider"""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-pro"
        self._client = None

    async def initialize(self):
        """Initialize the Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Gemini provider", error=str(e))
            raise

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini"""
        start_time = time.time()
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.generate_content(
                    contents=request.prompt,  # ✅ must use contents
                    generation_config={
                        "max_output_tokens": request.max_tokens or 500,
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                    },
                ),
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.text,
                model=self.model,
                response_time_ms=response_time_ms,
                metadata={"provider": "gemini", "finish_reason": "stop"},
            )
        except Exception as e:
            logger.error("Gemini generation failed", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if Gemini is healthy"""
        try:
            # Just check if client is initialized, don't make actual API calls
            return self._client is not None
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "gemini"


class OpenAIProvider(LLMProvider):
    """OpenAI provider"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4"
        self._client = None

    async def initialize(self):
        """Initialize the OpenAI client"""
        try:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize OpenAI provider", error=str(e))
            raise

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI"""
        start_time = time.time()
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=request.max_tokens or 500,
                temperature=request.temperature,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                finish_reason=response.choices[0].finish_reason,
                response_time_ms=response_time_ms,
                metadata={"provider": "openai"},
            )
        except Exception as e:
            logger.error("OpenAI generation failed", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if OpenAI is healthy"""
        try:
            # Just check if client is initialized, don't make actual API calls
            return self._client is not None
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "openai"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-sonnet-20240229"
        self._client = None

    async def initialize(self):
        """Initialize the Anthropic client"""
        try:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            logger.info("Anthropic provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Anthropic provider", error=str(e))
            raise

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic Claude"""
        start_time = time.time()
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens or 500,
                temperature=request.temperature,
                messages=[{"role": "user", "content": request.prompt}],
            )

            response_time_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                response_time_ms=response_time_ms,
                metadata={"provider": "anthropic"},
            )
        except Exception as e:
            logger.error("Anthropic generation failed", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if Anthropic is healthy"""
        try:
            # Just check if client is initialized, don't make actual API calls
            return self._client is not None
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "anthropic"


class HuggingFaceProvider(LLMProvider):
    """Hugging Face provider for local models"""

    def __init__(self):
        self.model_name = "microsoft/DialoGPT-medium"
        self._pipeline = None

    async def initialize(self):
        """Initialize the Hugging Face pipeline"""
        try:
            from transformers import pipeline

            self._pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                return_full_text=False,
                max_length=100,
                do_sample=True,
                temperature=0.7,
            )
            logger.info("Hugging Face provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Hugging Face provider", error=str(e))
            raise

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Hugging Face model"""
        start_time = time.time()
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._pipeline(
                    request.prompt,
                    max_length=request.max_tokens or 100,
                    temperature=request.temperature,
                    do_sample=True,
                    pad_token_id=50256,
                ),
            )

            response_time_ms = int((time.time() - start_time) * 1000)
            content = (
                response[0]["generated_text"]
                if response
                else "I'm not sure how to respond."
            )

            return LLMResponse(
                content=content,
                model=self.model_name,
                response_time_ms=response_time_ms,
                metadata={"provider": "huggingface"},
            )
        except Exception as e:
            logger.error("Hugging Face generation failed", error=str(e))
            raise

    async def is_healthy(self) -> bool:
        """Check if Hugging Face is healthy"""
        try:
            # Just check if pipeline is initialized, don't make actual API calls
            return self._pipeline is not None
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "huggingface"


class LLMService:
    """Service for managing multiple LLM providers"""

    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.current_provider: Optional[LLMProvider] = None

    async def initialize(self):
        """Initialize all available LLM providers"""
        logger.info("Initializing LLM service")

        # Preferred order: Gemini → OpenAI → Anthropic → HuggingFace
        if settings.GEMINI_API_KEY:
            try:
                provider = GeminiProvider()
                await provider.initialize()
                self.providers.append(provider)
                logger.info("Gemini provider added")
            except Exception as e:
                logger.warning("Failed to initialize Gemini provider", error=str(e))

        if settings.OPENAI_API_KEY:
            try:
                provider = OpenAIProvider()
                await provider.initialize()
                self.providers.append(provider)
                logger.info("OpenAI provider added")
            except Exception as e:
                logger.warning("Failed to initialize OpenAI provider", error=str(e))

        if settings.ANTHROPIC_API_KEY:
            try:
                provider = AnthropicProvider()
                await provider.initialize()
                self.providers.append(provider)
                logger.info("Anthropic provider added")
            except Exception as e:
                logger.warning("Failed to initialize Anthropic provider", error=str(e))

        try:
            provider = HuggingFaceProvider()
            await provider.initialize()
            self.providers.append(provider)
            logger.info("Hugging Face provider added")
        except Exception as e:
            logger.warning("Failed to initialize Hugging Face provider", error=str(e))

        if not self.providers:
            raise RuntimeError("No LLM providers could be initialized")

        await self._select_healthy_provider()
        logger.info(f"LLM service initialized with {len(self.providers)} providers")

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using the best available provider"""
        if not self.current_provider:
            await self._select_healthy_provider()

        if not self.current_provider:
            raise RuntimeError("No healthy LLM providers available")

        try:
            return await self.current_provider.generate_response(request)
        except Exception as e:
            logger.error("Current provider failed, trying others", error=str(e))
            # Try other providers in order
            for provider in self.providers:
                if provider != self.current_provider:
                    try:
                        if await provider.is_healthy():
                            self.current_provider = provider
                            logger.info(
                                f"Switched to backup provider: {provider.get_provider_name()}"
                            )
                            return await provider.generate_response(request)
                    except Exception:
                        continue

            raise RuntimeError("All LLM providers failed")

    async def is_healthy(self) -> bool:
        """Check if any provider is healthy"""
        for provider in self.providers:
            try:
                if await provider.is_healthy():
                    return True
            except Exception:
                continue
        return False

    async def _select_healthy_provider(self):
        """Select the first healthy provider in preferred order"""
        for provider in self.providers:
            try:
                if await provider.is_healthy():
                    self.current_provider = provider
                    logger.info(
                        f"Selected provider: {provider.get_provider_name()}"
                    )
                    return
            except Exception:
                continue
        self.current_provider = None

    async def close(self):
        """Close all providers"""
        logger.info("Closing LLM service")
        # Most providers don't need explicit closing
        pass
