"""OpenAI-compatible LLM client.

Config (project root .env):
    LLM_API_URL   — base URL of the chat completions endpoint
    LLM_API_KEY   — API key
    LLM_MODEL_NAME — model identifier
"""

from __future__ import annotations

from pathlib import Path

import requests

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_CA_BUNDLE = Path(__file__).resolve().parents[3] / "combined-ca.pem"


def _load_config() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip("'\"")

    api_url = (env.get("LLM_API_URL") or "").rstrip("/")
    api_key = env.get("LLM_API_KEY") or ""
    model = env.get("LLM_MODEL_NAME") or ""

    if not api_url:
        raise ValueError(f"LLM_API_URL not set in {_ENV_PATH}")
    if not api_key:
        raise ValueError(f"LLM_API_KEY not set in {_ENV_PATH}")
    if not model:
        raise ValueError(f"LLM_MODEL_NAME not set in {_ENV_PATH}")

    return api_url, api_key, model


def chat_completion(messages: list[dict], *, json_mode: bool = False) -> str:
    """Send messages to the LLM and return the assistant reply text.

    Args:
        messages: Standard OpenAI messages list [{"role": ..., "content": ...}].
        json_mode: When True, adds response_format=json_object for guaranteed JSON output.
    """
    api_url, api_key, model = _load_config()

    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    verify = str(_CA_BUNDLE) if _CA_BUNDLE.exists() else True

    response = requests.post(
        f"{api_url}/chat/completions",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        verify=verify,
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(
            f"LLM API error {response.status_code}: {response.text[:500]}"
        )

    return response.json()["choices"][0]["message"]["content"]
