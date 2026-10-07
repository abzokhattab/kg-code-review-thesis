"""LLM provider abstraction."""

import os
import time
from typing import Optional


# Token-usage tracking. Non-breaking side channel: each successful API call
# appends a {model, prompt_tokens, completion_tokens} dict here. Consumers
# (cost-reporting scripts) read and reset via _USAGE_LOG.clear(). Default
# behaviour of generate_completion() is unchanged.
_USAGE_LOG: list[dict] = []


def _record_usage(model: str, usage) -> None:
    if usage is None:
        return
    try:
        _USAGE_LOG.append({
            "model": model,
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        })
    except Exception:
        pass


def generate_completion(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0
) -> str:
    """
    Generate completion from LLM.
    
    Args:
        prompt: User prompt
        system: System prompt
        model: Model identifier (e.g., "openai:gpt-4o", "anthropic:claude-3-7-sonnet-20250219")
        temperature: Sampling temperature
    
    Returns:
        Generated text
    """
    # Parse model string
    if not model:
        model = os.environ.get('MODEL_NAME', 'openai:gpt-4o')
    
    if ':' in model:
        provider, model_name = model.split(':', 1)
    else:
        provider = os.environ.get('MODEL_PROVIDER', 'openai')
        model_name = model
    
    provider = provider.lower()
    
    if provider == 'openai':
        return _generate_openai(prompt, system, model_name, temperature)
    elif provider == 'anthropic':
        return _generate_anthropic(prompt, system, model_name, temperature)
    elif provider == 'deepseek':
        return _generate_openai_compat(prompt, system, model_name, temperature,
                                        base_url="https://api.deepseek.com/v1",
                                        api_key_env="DEEPSEEK_API_KEY",
                                        provider_tag="deepseek")
    elif provider == 'gemini':
        return _generate_openai_compat(prompt, system, model_name, temperature,
                                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                                        api_key_env="GOOGLE_API_KEY",
                                        provider_tag="gemini")
    elif provider in ('xai', 'grok'):
        return _generate_openai_compat(prompt, system, model_name, temperature,
                                        base_url="https://api.x.ai/v1",
                                        api_key_env="XAI_API_KEY",
                                        provider_tag="xai")
    elif provider == 'local':
        return _generate_local(prompt, system, model_name, temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _generate_openai(
    prompt: str,
    system: Optional[str],
    model_name: str,
    temperature: float
) -> str:
    """Generate using OpenAI API with automatic TPM rate-limit retry."""
    try:
        import openai

        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY or API_KEY environment variable required")

        client = openai.OpenAI(api_key=api_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        token_param = "max_completion_tokens" if "gpt-5" in model_name or "o3" in model_name or "o4" in model_name else "max_tokens"

        for attempt in range(8):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    **{token_param: 4096}
                )
                _record_usage(f"openai:{model_name}", getattr(response, "usage", None))
                return response.choices[0].message.content or ""
            except openai.RateLimitError as e:
                # Parse retry-after from message if present, else exponential backoff
                import re
                m = re.search(r'try again in ([0-9.]+)s', str(e))
                wait = float(m.group(1)) + 2 if m else min(30 * (2 ** attempt), 120)
                print(f"    [rate-limit] waiting {wait:.0f}s before retry {attempt+1}/8...")
                time.sleep(wait)
        raise RuntimeError("OpenAI rate limit: max retries exceeded")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"OpenAI generation failed: {e}")


def _generate_openai_compat(
    prompt: str,
    system: Optional[str],
    model_name: str,
    temperature: float,
    base_url: str,
    api_key_env: str,
    provider_tag: str
) -> str:
    """Generate using an OpenAI-compatible provider."""
    try:
        import openai

        api_key = os.environ.get(api_key_env) or os.environ.get('API_KEY')
        if not api_key:
            raise ValueError(f"{api_key_env} environment variable required")

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=8192
        )

        _record_usage(f"{provider_tag}:{model_name}", getattr(response, "usage", None))
        return response.choices[0].message.content or ""
    except Exception as e:
        raise RuntimeError(f"API generation failed ({base_url}): {e}")


def _generate_anthropic(
    prompt: str,
    system: Optional[str],
    model_name: str,
    temperature: float
) -> str:
    """Generate using Anthropic API."""
    try:
        import anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY or API_KEY environment variable required")
        
        # Explicitly bypass ANTHROPIC_BASE_URL (set by Claude Code's local proxy)
        # so generation scripts hit api.anthropic.com directly.
        client = anthropic.Anthropic(api_key=api_key, base_url="https://api.anthropic.com")
        
        response = client.messages.create(
            model=model_name,
            max_tokens=2000,
            temperature=temperature,
            system=system or "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Anthropic usage shape: input_tokens / output_tokens (not prompt/completion)
        anth_usage = getattr(response, "usage", None)
        if anth_usage is not None:
            _USAGE_LOG.append({
                "model": f"anthropic:{model_name}",
                "prompt_tokens": getattr(anth_usage, "input_tokens", 0) or 0,
                "completion_tokens": getattr(anth_usage, "output_tokens", 0) or 0,
            })
        return response.content[0].text
    except Exception as e:
        raise RuntimeError(f"Anthropic generation failed: {e}")


def _generate_local(
    prompt: str,
    system: Optional[str],
    model_name: str,
    temperature: float
) -> str:
    """Generate using local model (placeholder)."""
    # For POC, return a mock response
    return """# Review Note — Evidence-Anchored

**Scope:** Local model placeholder

## Problem
1) This is a placeholder response from local model
2) Real implementation would use transformers or other local inference

## Evidence
• placeholder.py:1-10: Mock evidence line
• placeholder.py:15-20: Another mock line

## Impact
• This is placeholder impact text for testing

## Recommendation (Fix / Tests / Risks)
1) Implement actual local model inference
2) Add test coverage for local generation
3) Monitor inference performance

## Traceability
• CODEOWNERS: @team
"""










