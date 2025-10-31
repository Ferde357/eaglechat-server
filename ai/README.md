# AI Service Module

This module handles AI integrations for EagleChat server, supporting multiple AI providers including Anthropic Claude and OpenAI GPT models.

## Structure

- `base.py` - Main AIService class that coordinates different providers
- `models/` - AI provider implementations
  - `types.py` - Common data types and exceptions
  - `anthropic.py` - Anthropic Claude API integration
  - `openai.py` - OpenAI GPT API integration
- `services/` - AI-related services
  - `conversation.py` - Conversation context building and management
- `utils/` - Utility functions
  - `retry.py` - Retry decorator for API calls
  - `config.py` - Model configurations

## Usage

```python
from ai import ai_service, AIServiceError

try:
    response = await ai_service.generate_response(
        message="Hello, how are you?",
        ai_config=ai_config,
        conversation_history=history,
        tenant_id=tenant_id
    )
    print(response.response)
except AIServiceError as e:
    print(f"AI service error: {e.message}")
```

## Adding New Providers

1. Create a new provider class in `models/`
2. Implement the `generate_response` method
3. Add model configurations to `utils/config.py`
4. Update the routing logic in `base.py`

## Features

- **Multi-provider support** - Anthropic and OpenAI with easy extensibility
- **Automatic retries** - Exponential backoff for transient failures
- **Token tracking** - Detailed usage statistics
- **Conversation context** - Smart history management
- **Tenant isolation** - Per-tenant API key management
- **Error handling** - Comprehensive error categorization