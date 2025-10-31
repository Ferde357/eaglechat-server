"""
AI Model Configurations
"""

# Model configurations - update these when new models are released
MODEL_CONFIGS = {
    'claude-sonnet': {
        'provider': 'anthropic',
        'model_name': 'claude-sonnet-4-5',  # Latest Sonnet
        'max_tokens_default': 4096
    },
    'claude-haiku': {
        'provider': 'anthropic', 
        'model_name': 'claude-haiku-4-5',  # Latest Haiku
        'max_tokens_default': 4096
    },
    'claude-opus': {
        'provider': 'anthropic',
        'model_name': 'claude-opus-4-1',  # Current Opus
        'max_tokens_default': 4096
    },
    'openai-gpt5': {
        'provider': 'openai',
        'model_name': 'gpt-5',  # Latest GPT-5 series
        'max_tokens_default': 4096
    },
    'openai-gpt5-mini': {
        'provider': 'openai',
        'model_name': 'gpt-5-mini',  # GPT-5 Mini
        'max_tokens_default': 4096
    },
    'openai-gpt5-nano': {
        'provider': 'openai',
        'model_name': 'gpt-5-nano',  # GPT-5 Nano
        'max_tokens_default': 4096
    },
    # Legacy GPT-4 models for compatibility
    'openai-gpt4': {
        'provider': 'openai',
        'model_name': 'gpt-4o',  # Latest GPT-4 Omni
        'max_tokens_default': 4096
    },
    'openai-gpt-mini': {
        'provider': 'openai',
        'model_name': 'gpt-4o-mini',  # Latest mini model
        'max_tokens_default': 4096
    },
    'openai-gpt-turbo': {
        'provider': 'openai',
        'model_name': 'gpt-4-turbo',  # Previous generation
        'max_tokens_default': 4096
    }
}