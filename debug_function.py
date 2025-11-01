#!/usr/bin/env python3
"""
Debug script to test the register_tenant function directly
"""
import asyncio
from database import db
import uuid

async def test_register_function():
    """Test the register_tenant function directly"""
    try:
        client = db.supabase_manager.client
        
        # Test with minimal data first
        test_tenant_id = str(uuid.uuid4())
        
        print("Testing register_tenant function...")
        
        # Call the function directly
        result = client.rpc('register_tenant', {
            'p_tenant_id': test_tenant_id,
            'p_api_key': 'test-api-key',
            'p_site_url': 'http://test.example.com',
            'p_admin_email': 'test@example.com',
            'p_metadata': {},
            'p_domain': 'test.example.com',
            'p_hmac_secret_encrypted': 'test-encrypted-secret',
            'p_site_hash': 'test-site-hash'
        }).execute()
        
        print(f"Function result: {result.data}")
        
        # If successful, clean up
        if result.data and result.data.get('success'):
            print("Cleaning up test tenant...")
            client.table('tenants').delete().eq('id', test_tenant_id).execute()
            
    except Exception as e:
        print(f"Error testing function: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_register_function())