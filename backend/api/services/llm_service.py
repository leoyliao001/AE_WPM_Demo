"""OpenAI-compatible LLM client.

Config (project root .env):
    LLM_API_URL     — base URL of the chat completions endpoint
    LLM_API_KEY     — API key
    LLM_MODEL_NAME  — model identifier
    LLM_SSL_VERIFY  — true|false (default true). Set false behind corporate SSL proxy.
    LLM_CA_BUNDLE   — optional path to a custom CA PEM (also accepts project-root combined-ca.pem)
"""

from __future__ import annotations

from pathlib import Path

import requests
import urllib3

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_PATH = _PROJECT_ROOT / ".env"
_DEFAULT_CA_BUNDLE = _PROJECT_ROOT / "combined-ca.pem"


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not _ENV_PATH.exists():
        return env
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("'\"")
    return env


def _load_config() -> tuple[str, str, str]:
    env = _load_env()

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


def _resolve_ssl_verify(env: dict[str, str]):
    """Return requests `verify` value: False | CA path | True."""
    verify_raw = (env.get("LLM_SSL_VERIFY") or "true").strip().lower()
    if verify_raw in {"0", "false", "no", "off"}:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False

    ca_override = (env.get("LLM_CA_BUNDLE") or "").strip()
    if ca_override:
        ca_path = Path(ca_override)
        if not ca_path.is_absolute():
            ca_path = _PROJECT_ROOT / ca_path
        if ca_path.exists():
            return str(ca_path)
        raise ValueError(f"LLM_CA_BUNDLE not found: {ca_path}")

    if _DEFAULT_CA_BUNDLE.exists():
        return str(_DEFAULT_CA_BUNDLE)

    return True


def chat_completion(messages: list[dict], *, json_mode: bool = False) -> str:
    """Send messages to the LLM and return the assistant reply text.

    Args:
        messages: Standard OpenAI messages list [{"role": ..., "content": ...}].
        json_mode: When True, adds response_format=json_object for guaranteed JSON output.
    """
    env = _load_env()
    api_url, api_key, model = _load_config()

    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    verify = _resolve_ssl_verify(env)

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
