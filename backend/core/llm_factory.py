"""
LLM factory — returns the correct LangChain chat model instance
based on the model name prefix.

Supported providers (detected automatically from model name):
  claude-*          → Anthropic  (langchain-anthropic)
  gpt-* | o1-* | o3-* | o4-*  → OpenAI     (langchain-openai)
  gemini-*          → Google     (langchain-google-genai)
"""
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel

from backend.config import get_settings


def get_llm(model: str, **kwargs: Any) -> BaseChatModel:
    """
    Return a LangChain chat model instance for the given model name.

    Provider is inferred from the model name prefix:
      - 'claude-'         → ChatAnthropic
      - 'gpt-', 'o1-', 'o3-', 'o4-'  → ChatOpenAI
      - 'gemini-'         → ChatGoogleGenerativeAI

    Extra kwargs (e.g. temperature, max_tokens) are forwarded to the
    provider constructor.

    Usage:
        llm = get_llm("claude-sonnet-4-6", temperature=0, max_tokens=256)
        llm = get_llm("gpt-4o", temperature=0.2, max_tokens=512)
    """
    settings = get_settings()
    name = model.lower()

    if name.startswith("claude-"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            api_key=settings.anthropic_api_key,
            **kwargs,
        )

    if name.startswith(("gpt-", "o1-", "o3-", "o4-")):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            **kwargs,
        )

    if name.startswith("gemini-"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ImportError(
                "Google Generative AI support requires 'langchain-google-genai'. "
                "Install it: pip install langchain-google-genai"
            ) from exc
        google_api_key = getattr(settings, "google_api_key", None)
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=google_api_key,
            **kwargs,
        )

    raise ValueError(
        f"Cannot determine LLM provider for model '{model}'. "
        "Expected prefix: 'claude-', 'gpt-', 'o1-', 'o3-', 'o4-', or 'gemini-'."
    )
