# Eagle Chat Server

A multi-tenant backend API for WordPress chatbot integration, built with FastAPI and Supabase. 
This server manages tenant registration, authentication, and provides a secure foundation for chatbot services across multiple WordPress sites.

## 🚀 Features

- **Multi-Tenant Architecture**: UUID-based tenant isolation ensures complete data separation
- **HMAC Request Signing**: Cryptographic authentication for secure API communication
- **Automatic Credential Generation**: Secure API keys and tenant IDs generated server-side
- **WordPress Callback Verification**: Validates registration requests by calling back to WordPress
- **AI Provider Management**: Secure storage and validation of Anthropic/OpenAI API keys
- **Rate Limiting**: Per-IP rate limiting with configurable limits
- **Daily Rolling Logs**: Automatic log rotation with configurable retention policies
- **Comprehensive Validation**: Email, URL, and API key validation with detailed error messages
- **RESTful API**: Clean, well-documented endpoints with OpenAPI specification
- **Production-Ready**: Error handling, logging, retry logic, and security best practices

## 📋 Prerequisites

- Python 3.8+
- Supabase account with a project
- PostgreSQL database (via Supabase)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd eaglechatserver
```

### 2. Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Database Setup

1. Log into your Supabase project dashboard
2. Navigate to the SQL Editor
3. Run the SQL scripts in order:
   - First, execute all SQL from `suprabase.md` (creates the documents table and vector search functions)
   - Then, execute all SQL from `suprabase_tenant.md` (creates the tenants table and management functions)

### 4. Configure the Application

1. Create `.env` file with your sensitive credentials:
   ```bash
   # Copy the example file and edit it
   cp .env.example .env
   # Then edit .env with your actual credentials
   ```
   
   **Required environment variables:**
   ```bash
   # EagleChat Master Key for encrypting tenant secrets
   EAGLECHAT_MASTER_KEY=your-64-character-base64-key-here
   
   # Supabase Database Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```

2. Create `config.json` with your application settings:
   ```json
   {
     "logging": {
       "level": "INFO",
       "retention_days": 30,
       "log_directory": "logs"
     },
     "api": {
       "title": "Eagle Chat Server",
       "description": "Multi-tenant chatbot backend for WordPress",
       "version": "1.0.0",
       "development_mode": false
     },
     "callback": {
       "retry_attempts": 3,
       "retry_delay_seconds": 3
     }
   }
   ```

   **Configuration sections:**
   - **`.env`**: All sensitive credentials (never commit to git)
   - **`config.json`**: Application settings (safe to version control)
   - `logging`: Log level, retention, and directory settings  
   - `api`: API metadata and development mode toggle
   - `callback`: WordPress callback verification retry settings

   **Finding your Supabase credentials:**
   - URL: Settings → API → Project URL
   - Service Role Key: Settings → API → Service Role Key (secret)

   **⚠️ Security Note**: Always add `.env` to your `.gitignore` file to prevent committing secrets!

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## 📡 API Documentation

### Interactive Documentation

Once running, access the interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### 🏥 Health Check
```http
GET /
```
Returns server status, version, and health information.

**Response:**
```json
{
  "status": "healthy",
  "service": "Eagle Chat Server",
  "version": "1.0.0",
  "development_mode": false
}
```

#### 🔐 Register Tenant
```http
POST /api/v1/register
Content-Type: application/json

{
  "site_url": "https://your-wordpress-site.com",
  "admin_email": "admin@your-site.com",
  "callback_token": "wordpress_generated_token_here"
}
```

**Registration Workflow:**
1. WordPress plugin generates a temporary callback token (expires in 60 seconds)
2. Plugin sends registration request with site URL, admin email, and callback token
3. FastAPI server immediately calls back to WordPress at `/wp-json/eaglechat-plugin/v1/verify`
4. WordPress verifies the token matches what it generated
5. On successful verification, FastAPI generates and returns tenant credentials

**Response:**
```json
{
  "success": true,
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
  "message": "Tenant registered successfully"
}
```

**Error Responses:**
- `400`: Site URL already registered, email already associated, or callback verification failed
- `500`: Server error

#### ✅ Validate Tenant
```http
POST /api/v1/validate
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Credentials are valid"
}
```

**Error Response:**
- `401`: Invalid credentials

#### 🔑 Configure HMAC Security
```http
POST /api/v1/configure-hmac
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
  "hmac_secret": "64-character-hex-string-secret"
}
```

**Response:**
```json
{
  "success": true,
  "message": "HMAC secret configured successfully"
}
```

#### 🤖 Chat with AI (HMAC Protected)
```http
POST /api/v1/chat
Content-Type: application/json
X-EagleChat-Signature: hmac-sha256=calculated_signature
X-EagleChat-Timestamp: 1642781234
X-EagleChat-Version: v1

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
  "session_id": "user_session_12345",
  "message": "Hello, how can you help me?",
  "ai_config": {
    "model": "claude-3-sonnet",
    "temperature": 0.7,
    "max_tokens": 2000,
    "conversation_memory": "full"
  }
}
```

**HMAC Signature Calculation:**
```
string_to_sign = timestamp + "\n" + request_body
signature = hmac_sha256(hmac_secret, string_to_sign)
header_value = "hmac-sha256=" + signature
```

**Response:**
```json
{
  "success": true,
  "response": "Hello! I'm here to help you with any questions...",
  "ai_model": "claude-3-sonnet",
  "input_tokens": 12,
  "output_tokens": 45,
  "total_tokens": 57
}
```

#### 🔧 Configure AI Provider Keys
```http
POST /api/v1/configure-keys
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
  "anthropic_api_key": "sk-ant-your-anthropic-key",
  "openai_api_key": "sk-your-openai-key"
}
```

#### 📊 Get API Key Status
```http
POST /api/v1/get-key-status
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
}
```

**Response:**
```json
{
  "success": true,
  "masked_keys": {
    "anthropic": "sk-ant-****...****",
    "openai": "sk-****...****"
  }
}
```

#### 🗑️ Remove API Key
```http
POST /api/v1/remove-key
Content-Type: application/json

{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "eck_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
  "provider": "anthropic"
}
```

## 🔒 HMAC Authentication

### Overview
HMAC (Hash-based Message Authentication Code) provides cryptographic verification that requests are authentic and unmodified. Required for production deployments.

### Protected Endpoints
- `/api/v1/chat` - AI chat functionality
- `/api/v1/conversation-history` - Chat history retrieval

### HMAC Headers
- `X-EagleChat-Signature`: `hmac-sha256=<signature>`
- `X-EagleChat-Timestamp`: Unix timestamp (within 5 minutes)
- `X-EagleChat-Version`: `v1` (optional)

### Signature Generation
1. Create string to sign: `timestamp + "\n" + request_body`
2. Calculate HMAC-SHA256: `hmac(secret, string_to_sign)`
3. Format header: `hmac-sha256=<hex_signature>`

### Example Implementation (Python)
```python
import hmac
import hashlib
import time
import json

def generate_hmac_signature(secret, body):
    timestamp = int(time.time())
    string_to_sign = f"{timestamp}\n{body}"
    signature = hmac.new(
        secret.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        'X-EagleChat-Signature': f'hmac-sha256={signature}',
        'X-EagleChat-Timestamp': str(timestamp),
        'X-EagleChat-Version': 'v1'
    }
```

### Security Features
- **Algorithm**: HMAC-SHA256
- **Timestamp Validation**: 5-minute tolerance prevents replay attacks
- **Constant-time Comparison**: Prevents timing attack vulnerabilities
- **Encrypted Storage**: Secrets stored encrypted in database

## 🧪 Testing

### Testing Tools

#### Option 1: HTTP Test Files (Recommended for Development)
The `test_api.http` file contains pre-configured test scenarios:

1. **VS Code**: Install the "REST Client" extension by Huachao Mao
2. **IntelliJ IDEA**: Use the built-in HTTP Client
3. **Command Line**: Use curl or httpie

#### Option 2: Postman (Recommended for Comprehensive Testing)
See detailed Postman instructions below.

#### Option 3: Interactive API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 📮 Postman Testing Guide

#### Setup Environment Variables
Create a Postman environment with these variables:
```
baseUrl = http://localhost:8000
tenant_id = (will be set from registration response)
api_key = (will be set from registration response)
hmac_secret = (will be set after HMAC configuration)
```

#### Pre-request Script for HMAC Signatures
Add this pre-request script to HMAC-protected endpoints:

```javascript
// Generate HMAC signature for EagleChat API
if (pm.request.headers.has('X-EagleChat-Signature')) {
    const timestamp = Math.floor(Date.now() / 1000);
    const body = pm.request.body.raw || '';
    const secret = pm.environment.get('hmac_secret');
    
    if (!secret) {
        throw new Error('hmac_secret environment variable is required');
    }
    
    // Create string to sign
    const stringToSign = timestamp + '\n' + body;
    
    // Generate HMAC-SHA256 signature
    const signature = CryptoJS.HmacSHA256(stringToSign, secret).toString();
    
    // Set headers
    pm.request.headers.upsert({
        key: 'X-EagleChat-Signature',
        value: `hmac-sha256=${signature}`
    });
    pm.request.headers.upsert({
        key: 'X-EagleChat-Timestamp',
        value: timestamp.toString()
    });
    pm.request.headers.upsert({
        key: 'X-EagleChat-Version',
        value: 'v1'
    });
}
```

#### Test Collection Structure

**1. Health Check**
```http
GET {{baseUrl}}/
```

**2. Register Tenant**
```http
POST {{baseUrl}}/api/v1/register
Content-Type: application/json

{
  "site_url": "https://test-site.com",
  "admin_email": "admin@test-site.com", 
  "callback_token": "test_token_1234567890abcdef"
}
```

**Test Script to Extract Credentials:**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set('tenant_id', response.tenant_id);
    pm.environment.set('api_key', response.api_key);
    console.log('Tenant credentials saved to environment');
}
```

**3. Validate Tenant**
```http
POST {{baseUrl}}/api/v1/validate
Content-Type: application/json

{
  "tenant_id": "{{tenant_id}}",
  "api_key": "{{api_key}}"
}
```

**4. Configure HMAC Secret**
```http
POST {{baseUrl}}/api/v1/configure-hmac
Content-Type: application/json

{
  "tenant_id": "{{tenant_id}}",
  "api_key": "{{api_key}}",
  "hmac_secret": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
}
```

**Test Script to Save HMAC Secret:**
```javascript
if (pm.response.code === 200) {
    // Save the secret used in the request for future HMAC calculations
    const requestBody = JSON.parse(pm.request.body.raw);
    pm.environment.set('hmac_secret', requestBody.hmac_secret);
    console.log('HMAC secret saved to environment');
}
```

**5. Configure AI API Keys**
```http
POST {{baseUrl}}/api/v1/configure-keys
Content-Type: application/json

{
  "tenant_id": "{{tenant_id}}",
  "api_key": "{{api_key}}",
  "anthropic_api_key": "sk-ant-your-test-key-here",
  "openai_api_key": "sk-your-openai-test-key-here"
}
```

**6. Chat with AI (HMAC Protected)**
```http
POST {{baseUrl}}/api/v1/chat
Content-Type: application/json
X-EagleChat-Signature: (auto-generated by pre-request script)
X-EagleChat-Timestamp: (auto-generated by pre-request script)  
X-EagleChat-Version: v1

{
  "tenant_id": "{{tenant_id}}",
  "api_key": "{{api_key}}",
  "session_id": "test_session_12345",
  "message": "Hello, this is a test message",
  "ai_config": {
    "model": "claude-3-sonnet",
    "temperature": 0.7,
    "max_tokens": 100,
    "conversation_memory": "full"
  }
}
```

**Important**: Add the pre-request script to this request for automatic HMAC signature generation.

### Manual Testing with cURL

#### Basic Endpoints
```bash
# Health check
curl http://localhost:8000/

# Register tenant
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "site_url": "https://test-site.com",
    "admin_email": "admin@test-site.com",
    "callback_token": "test_callback_token_1234567890"
  }'
```

#### HMAC-Protected Chat Request
```bash
#!/bin/bash
# Generate HMAC signature for chat request

TENANT_ID="your-tenant-id-here"
API_KEY="your-api-key-here"
HMAC_SECRET="your-hmac-secret-here"
TIMESTAMP=$(date +%s)

# Request body
BODY='{
  "tenant_id": "'$TENANT_ID'",
  "api_key": "'$API_KEY'",
  "session_id": "test_session_12345",
  "message": "Hello, this is a test message",
  "ai_config": {
    "model": "claude-3-sonnet",
    "temperature": 0.7,
    "max_tokens": 100,
    "conversation_memory": "full"
  }
}'

# Generate signature
STRING_TO_SIGN="$TIMESTAMP"$'\n'"$BODY"
SIGNATURE=$(echo -n "$STRING_TO_SIGN" | openssl dgst -sha256 -hmac "$HMAC_SECRET" -hex | cut -d' ' -f2)

# Make request
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-EagleChat-Signature: hmac-sha256=$SIGNATURE" \
  -H "X-EagleChat-Timestamp: $TIMESTAMP" \
  -H "X-EagleChat-Version: v1" \
  -d "$BODY"
```

### Testing Scenarios

#### Core Functionality Tests
1. **✅ Successful Registration**: Register with valid URL, email, and callback token
2. **❌ Duplicate Site URL**: Attempt to register same URL twice (should fail)
3. **❌ Duplicate Email**: Use already registered email (should fail)
4. **❌ Invalid Email Format**: Test email validation
5. **❌ Invalid URL Format**: Test URL validation
6. **❌ Invalid Callback Token**: Test with short or missing token
7. **✅ Valid Credentials**: Validate with correct tenant credentials
8. **❌ Invalid Credentials**: Test authentication failure

#### HMAC Security Tests
9. **✅ HMAC Configuration**: Successfully configure HMAC secret
10. **✅ Valid HMAC Request**: Chat with correct HMAC signature
11. **❌ Invalid HMAC Signature**: Chat with wrong signature (should fail)
12. **❌ Missing HMAC Headers**: Chat without HMAC headers (should fail)
13. **❌ Expired Timestamp**: Chat with old timestamp (should fail)
14. **❌ Future Timestamp**: Chat with future timestamp (should fail)

#### API Key Management Tests
15. **✅ Configure API Keys**: Add Anthropic/OpenAI keys
16. **✅ Get Key Status**: Retrieve masked key information
17. **✅ Remove API Key**: Delete specific provider key
18. **❌ Invalid API Key Format**: Test with malformed keys

#### Rate Limiting Tests
19. **✅ Normal Request Rate**: Stay within limits (20/minute)
20. **❌ Exceeded Rate Limit**: Send >20 requests in 60 seconds

### Expected Response Codes
- **200**: Success
- **400**: Bad Request (validation errors, duplicates)
- **401**: Unauthorized (invalid credentials, HMAC failure)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

### Callback Configuration

The callback verification includes configurable retry logic:
- **retry_attempts**: Number of times to retry the WordPress callback (default: 3)
- **retry_delay_seconds**: Delay between retries (default: 3 seconds)

## 📊 Monitoring & Logs

### Log Files

Logs are automatically created in the `logs/` directory with the format:
```
logs/
├── 20250124_LOG.log  # Today's log
├── 20250123_LOG.log  # Yesterday's log
└── ...
```

### Log Format
```
2025-01-24 10:30:45 - eaglechat - INFO - Registration request received for site: https://example.com
2025-01-24 10:30:46 - eaglechat - INFO - Successfully registered tenant: 123e4567... for site: https://example.com
```

### Log Retention

- Configured in `config.json` (default: 30 days)
- Old logs are automatically deleted
- Adjust `retention_days` as needed (1-365)

## 🔒 Security Considerations

1. **API Keys**: 
   - Generated using cryptographically secure random functions
   - 48+ characters with prefix "eck_"
   - Only alphanumeric, hyphens, and underscores allowed

2. **Tenant IDs**:
   - Standard UUID v4 format
   - Globally unique identifiers

3. **Configuration**:
   - Sensitive credentials stored in `config.json`
   - File excluded from version control via `.gitignore`
   - Use environment variables in production

4. **Validation**:
   - Strict email validation
   - URL format validation
   - Input sanitization

## 🚀 Production Deployment

1. Use environment variables for sensitive configuration
2. Set up a reverse proxy (nginx/Apache)
3. Enable HTTPS with SSL certificates
4. Configure CORS appropriately (not "*" in production)
5. Set up monitoring and alerting
6. Regular backup of Supabase database
7. Use a process manager (systemd, supervisor)

## 📝 Development Notes

- The server uses async/await for all database operations
- Logging is configured at both application and request levels
- All endpoints return appropriate HTTP status codes
- Comprehensive error messages aid in debugging

## 🤝 Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## 📄 License

[Add your license information here]

## 🆘 Troubleshooting

### Common Issues

1. **"config.json not found"**: Create it from `config.example.json`
2. **Database connection errors**: Verify Supabase credentials
3. **"Table does not exist"**: Run the SQL setup scripts
4. **Port already in use**: Change port with `--port 8001`

### Debug Mode

Set logging level to "DEBUG" in `config.json` for verbose output:
```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```