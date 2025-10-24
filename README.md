# Eagle Chat Server

A multi-tenant backend API for WordPress chatbot integration, built with FastAPI and Supabase. 
This server manages tenant registration, authentication, and provides a secure foundation for chatbot services across multiple WordPress sites.

## 🚀 Features

- **Multi-Tenant Architecture**: UUID-based tenant isolation ensures complete data separation
- **Automatic Credential Generation**: Secure API keys and tenant IDs generated server-side
- **WordPress Callback Verification**: Validates registration requests by calling back to WordPress
- **Daily Rolling Logs**: Automatic log rotation with configurable retention policies
- **Comprehensive Validation**: Email, URL, and API key validation with detailed error messages
- **RESTful API**: Clean, well-documented endpoints for tenant management
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

1. Copy the example configuration:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your Supabase credentials:
   ```json
   {
     "supabase": {
       "url": "https://your-project.supabase.co",
       "service_role_key": "your-service-role-key"
     },
     "logging": {
       "level": "INFO",
       "retention_days": 30,
       "log_directory": "logs"
     },
     "api": {
       "title": "Eagle Chat Server",
       "description": "Multi-tenant chatbot backend for WordPress",
       "version": "1.0.0"
     },
     "callback": {
       "retry_attempts": 3,
       "retry_delay_seconds": 3
     }
   }
   ```

   **Finding your Supabase credentials:**
   - URL: Settings → API → Project URL
   - Service Role Key: Settings → API → Service Role Key (secret)

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

### Endpoints

#### Health Check
```http
GET /
```
Returns server status, version, and health information.

#### Register Tenant
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

#### Validate Tenant
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

## 🧪 Testing

### Using the HTTP Test File

The `test_api.http` file contains pre-configured test scenarios:

1. **VS Code**: Install the "REST Client" extension by Huachao Mao
2. **IntelliJ IDEA**: Use the built-in HTTP Client
3. **Command Line**: Use curl or httpie

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/

# Register a new tenant
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "site_url": "https://test-site.com",
    "admin_email": "admin@test-site.com",
    "callback_token": "test_callback_token_1234567890"
  }'

# Validate tenant (use actual values from registration)
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-tenant-id",
    "api_key": "your-api-key"
  }'
```

### Testing Scenarios

1. **Successful Registration**: Register a new site with valid URL, email, and callback token
2. **Duplicate Site URL**: Attempt to register the same URL twice (should fail)
3. **Duplicate Email**: Use an already registered email (should fail)
4. **Invalid Email Format**: Test email validation
5. **Invalid URL Format**: Test URL validation
6. **Invalid Callback Token**: Test with short or missing callback token
7. **WordPress Callback Failure**: Test when WordPress doesn't verify the token
8. **Valid Credentials**: Validate with correct tenant ID and API key
9. **Invalid Credentials**: Test authentication failure

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