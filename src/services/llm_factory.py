"""
LLM Factory
Factory functions for creating LLM and embeddings instances.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config.settings import settings


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Factory function to get the appropriate LLM instance.

    Args:
        provider: LLM provider ("openai", "anthropic", or "google")
        model: Model name to use
        temperature: Temperature for generation
        max_tokens: Maximum tokens for generation

    Returns:
        Configured LLM instance
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set the OPENAI_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.OPENAI_MODEL
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. "
                "Please set the ANTHROPIC_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.ANTHROPIC_MODEL
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    elif provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Please set the GOOGLE_API_KEY environment variable or use a different LLM provider."
            )
        model = model or settings.GOOGLE_MODEL
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_embeddings(provider: Optional[str] = None) -> Embeddings:
    """
    Factory function to get the appropriate embeddings instance.

    Args:
        provider: Embeddings provider ("openai" or "google")
                  Note: Anthropic doesn't provide embeddings, falls back to OpenAI

    Returns:
        Configured embeddings instance

    Raises:
        ValueError: If the required API key is not configured
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER

    # Anthropic doesn't have embeddings, fall back to OpenAI or Google
    if provider == "anthropic":
        if settings.OPENAI_API_KEY:
            provider = "openai"
        elif settings.GOOGLE_API_KEY:
            provider = "google"
        else:
            raise ValueError(
                "Embeddings require either OPENAI_API_KEY or GOOGLE_API_KEY. "
                "Anthropic does not provide an embeddings API."
            )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set the OPENAI_API_KEY environment variable for embeddings."
            )
        return OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small",
        )
    elif provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. "
                "Please set the GOOGLE_API_KEY environment variable for embeddings."
            )
        return GoogleGenerativeAIEmbeddings(
            google_api_key=settings.GOOGLE_API_KEY,
            model="models/embedding-001",
        )
    else:
        raise ValueError(f"Unsupported embeddings provider: {provider}")
