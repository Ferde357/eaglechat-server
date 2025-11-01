-- Fix HMAC functions to work properly with PostgREST
-- Replace JSONB returns with table returns for better compatibility

-- Drop and recreate get_tenant_hmac_domain function
DROP FUNCTION IF EXISTS get_tenant_hmac_domain;

CREATE OR REPLACE FUNCTION get_tenant_hmac_domain(p_tenant_id TEXT)
RETURNS TABLE(
    hmac_secret_encrypted TEXT,
    domain VARCHAR(255),
    site_hash VARCHAR(64),
    hmac_secret_updated_at TIMESTAMP
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Return tenant HMAC and domain information
    RETURN QUERY
    SELECT 
        t.hmac_secret_encrypted,
        t.domain,
        t.site_hash,
        t.hmac_secret_updated_at
    FROM tenants t
    WHERE t.tenant_id = p_tenant_id::UUID;
    
    -- If no rows found, function will return empty result set
    -- Caller can check if any rows were returned
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION get_tenant_hmac_domain TO authenticated;