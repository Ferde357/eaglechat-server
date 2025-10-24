Change to registration process to include callback token. 

Workflow
1. User installs plugin on wordpress and clicks to Register in Wordpress admin area
2. Fast API Register_tenant is called sith site_url, admin_email, and callback_token (random token WordPress generates that expires in 60 seconds)
3. FastAPI immediately calls back to WordPress with the token:

POST https://site_url/wp-json/eaglechat-plugin/v1/verify
Sends the callback_token

4. WordPress plugin endpoint verifies:

Token matches what it just sent
Returns success (or fail if token doesn't match)

5. On success, FastAPI generates the uuid and api key which is stored in supabase and returned to wordpress.

Notes:
- Wordpress isn't handled in this code, details are provided for context and clarity. 
- Retry login with delays (number of retry and delay seconds configurable in config.json. Default is 3 and 3)

Also update config.example.json

Post Implementation
- Update readme and any testing for the new process




