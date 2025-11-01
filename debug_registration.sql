-- Debug the registration function to understand the duplicate issue

-- Test the register_tenant function with debug info
DO $$
DECLARE
    test_tenant_id TEXT := 'test-' || gen_random_uuid()::TEXT;
    test_result JSONB;
BEGIN
    -- Check what's in the table before
    RAISE NOTICE 'Records before test: %', (SELECT COUNT(*) FROM tenants);
    
    -- Test with a unique site URL
    test_result := register_tenant(
        test_tenant_id,
        'test-api-key-' || extract(epoch from now()),
        'http://test-' || extract(epoch from now()) || '.example.com',
        'test-' || extract(epoch from now()) || '@example.com',
        '{}',
        'test.example.com',
        'test-encrypted-secret',
        'test-site-hash'
    );
    
    RAISE NOTICE 'Test result: %', test_result;
    
    -- Check what's in the table after
    RAISE NOTICE 'Records after test: %', (SELECT COUNT(*) FROM tenants);
    
    -- Clean up test record
    DELETE FROM tenants WHERE tenant_id = test_tenant_id::UUID;
    
END $$;