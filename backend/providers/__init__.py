from . import groq, mistral, gemini, grok_xai

PROVIDER_MAP = {
    "groq":     groq,
    "mistral":  mistral,
    "gemini":   gemini,
    "grok":     grok_xai,
}


def call_provider(provider: str, model: str, system_prompt: str, user_message: str) -> str:
    """
    Route a model call to the correct provider module.

    Args:
        provider:      One of 'groq','mistral','gemini','grok'
        model:         The model string to pass to the provider
        system_prompt: Instruction prompt
        user_message:  Content to respond to

    Returns:
        The model's response as a plain string.

    Raises:
        ValueError:   If the provider name is not recognised.
        RuntimeError: Propagated from the provider on API failure.
    """
    if provider not in PROVIDER_MAP:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Must be one of: {list(PROVIDER_MAP.keys())}"
        )
    return PROVIDER_MAP[provider].call(model, system_prompt, user_message)