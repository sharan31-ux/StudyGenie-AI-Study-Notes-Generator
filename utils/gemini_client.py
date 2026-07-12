

import time
from typing import List, Optional

from google import genai
from google.genai import types

# Ordered from most-reliable/latest-alias to specific pinned fallbacks.
# "gemini-flash-latest" always points at Google's current default Flash model,
# so it's kept first as the most future-proof option; pinned versions follow
# as an explicit fallback in case the alias or a specific version is briefly
# unavailable.
#
# As of July 2026: gemini-2.0-flash / gemini-2.0-flash-lite were shut down on
# June 1, 2026 (always 404 now), and gemini-2.5-flash-lite has been
# restricted to existing users only (404s for new API keys/projects) -- both
# are intentionally excluded below. gemini-2.5-flash is still live but is
# slated for deprecation on Oct 16, 2026, so gemini-3.5-flash and
# gemini-3.1-flash-lite (the current GA replacement for the lite tier) are
# included as more future-proof options. Re-check
# https://ai.google.dev/gemini-api/docs/deprecations periodically, since
# Google has been retiring models on a roughly quarterly cadence.
DEFAULT_FALLBACK_MODELS = [
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
]


class GeminiGenerationError(RuntimeError):
    """Raised when every model in the fallback chain fails."""


class GeminiClient:
    def __init__(self, api_key: str, models: Optional[List[str]] = None):
        if not api_key or not api_key.strip():
            raise ValueError("A Gemini API key is required.")
        self._client = genai.Client(api_key=api_key.strip())
        self.models = models or DEFAULT_FALLBACK_MODELS
        self.last_used_model: Optional[str] = None

    def generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        max_retries_per_model: int = 2,
        retry_backoff_seconds: float = 1.2,
    ) -> str:
        """
        Try each model in order; within a model, retry a couple of times
        (handles transient 429/503 errors) before moving to the next model.
        This is the "model-fallback layer" that keeps generation reliable
        even when a specific model is overloaded, rate-limited, or retired.

        If every model fails, the raised error lists what each model in the
        chain reported, so a bad API key, a retired model, or a quota issue
        is easy to tell apart at a glance instead of only showing the last
        model's error.
        """
        attempts: List[str] = []

        for model_name in self.models:
            model_error: Optional[Exception] = None
            for attempt in range(max_retries_per_model):
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=temperature),
                    )
                    text = getattr(response, "text", None)
                    if text and text.strip():
                        self.last_used_model = model_name
                        return text.strip()
                    model_error = GeminiGenerationError("empty response")
                except Exception as e:  # noqa: BLE001 - intentionally broad for fallback
                    model_error = e
                    time.sleep(retry_backoff_seconds * (attempt + 1))
                    continue
            attempts.append(f"{model_name}: {model_error}")

        raise GeminiGenerationError(
            "All Gemini models in the fallback chain failed:\n- " + "\n- ".join(attempts)
        )
