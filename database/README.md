# Database Module

This module handles all database operations for EagleChat server using Supabase as the backend.

## Structure

- `supabase_manager.py` - Core Supabase client management
- `tenant_ops.py` - Tenant registration, validation, and management
- `api_key_ops.py` - API key storage, retrieval, and management
- `migrations/` - SQL migration files for database schema
  - `supabase_conversations.sql` - Conversation storage schema
  - `supabase_migration_add_api_keys.sql` - API key storage schema
  - `supabase_remove_key_function.sql` - API key removal functions

## Usage

```python
from database import db

# Register a new tenant
result = await db.register_tenant(
    tenant_id="tenant_123",
    api_key="api_key_abc",
    site_url="https://example.com",
    admin_email="admin@example.com"
)

# Validate tenant credentials
is_valid = await db.validate_tenant("tenant_123", "api_key_abc")

# Store API keys
await db.update_tenant_api_keys(
    tenant_id="tenant_123",
    anthropic_key_encrypted="encrypted_key",
    openai_key_encrypted="encrypted_key"
)
```

## Features

- **Tenant Management** - Registration, validation, and site checking
- **API Key Security** - Encrypted storage of AI provider API keys
- **Migration Support** - SQL scripts for database schema setup
- **Error Handling** - Comprehensive logging and error management
- **Singleton Pattern** - Single database instance for the application

## Database Schema

The module uses the following main tables:
- `tenants` - Tenant registration and configuration
- `tenant_api_keys` - Encrypted AI provider API keys
- `conversations` - Chat conversation storage

## Security

- All API keys are stored encrypted in the database
- Tenant isolation ensures data separation
- Service role key used for server-side operations
- No sensitive data in logs