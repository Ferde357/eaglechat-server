#!/usr/bin/env python3
"""
Debug script to check existing tenants in database
"""
import asyncio
from database import db

async def check_tenants():
    """Check for existing tenants that might conflict"""
    try:
        # Check if we can access the database
        client = db.supabase_manager.client
        
        # Get all tenants
        result = client.table('tenants').select('*').execute()
        
        print(f"Found {len(result.data)} existing tenants:")
        for tenant in result.data:
            print(f"- ID: {tenant.get('id')}")
            print(f"  Site URL: {tenant.get('site_url')}")
            print(f"  Admin Email: {tenant.get('admin_email')}")
            print(f"  Domain: {tenant.get('domain')}")
            print(f"  HMAC Configured: {bool(tenant.get('hmac_secret_encrypted'))}")
            print(f"  Created: {tenant.get('created_at')}")
            print()
        
        # Check specifically for localhost:10003
        localhost_result = client.table('tenants').select('*').eq('site_url', 'http://localhost:10003').execute()
        if localhost_result.data:
            print("Found existing registration for http://localhost:10003:")
            for tenant in localhost_result.data:
                print(f"- Tenant ID: {tenant.get('id')}")
                print(f"- Admin Email: {tenant.get('admin_email')}")
                print(f"- Created: {tenant.get('created_at')}")
        else:
            print("No existing registration found for http://localhost:10003")
            
    except Exception as e:
        print(f"Error checking tenants: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_tenants())