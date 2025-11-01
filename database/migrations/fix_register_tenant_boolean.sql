-- Fix register_tenant function to return BOOLEAN instead of JSONB
-- This resolves the PostgREST issue with complex return types

-- Drop and recreate the register_tenant function with simple BOOLEAN return
DROP FUNCTION IF EXISTS register_tenant;

CREATE OR REPLACE FUNCTION register_tenant(
    p_tenant_id TEXT,
    p_api_key TEXT,
    p_site_url TEXT,
    p_admin_email TEXT,
    p_metadata JSONB DEFAULT '{}',
    p_domain TEXT DEFAULT NULL,
    p_hmac_secret_encrypted TEXT DEFAULT NULL,
    p_site_hash TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_tenant_count INTEGER;
    v_site_count INTEGER;
    v_email_count INTEGER;
BEGIN
    -- Validate tenant_id is a valid UUID
    BEGIN
        PERFORM p_tenant_id::UUID;
    EXCEPTION
        WHEN invalid_text_representation THEN
            RAISE EXCEPTION 'Invalid tenant ID format';
    END;
    
    -- Check if tenant_id already exists
    SELECT COUNT(*) INTO v_tenant_count 
    FROM tenants 
    WHERE tenant_id = p_tenant_id::UUID;
    
    IF v_tenant_count > 0 THEN
        RAISE EXCEPTION 'Tenant ID already exists';
    END IF;
    
    -- Check if site URL already registered
    SELECT COUNT(*) INTO v_site_count
    FROM tenants 
    WHERE site_url = p_site_url;
    
    IF v_site_count > 0 THEN
        RAISE EXCEPTION 'Site URL already registered';
    END IF;
    
    -- Check if admin email already used
    SELECT COUNT(*) INTO v_email_count
    FROM tenants 
    WHERE admin_email = p_admin_email;
    
    IF v_email_count > 0 THEN
        RAISE EXCEPTION 'Admin email already associated with another tenant';
    END IF;
    
    -- Insert new tenant with domain verification data
    INSERT INTO tenants (
        tenant_id,
        api_key,
        site_url,
        admin_email,
        metadata,
        domain,
        hmac_secret_encrypted,
        site_hash,
        hmac_secret_updated_at,
        created_at
    ) VALUES (
        p_tenant_id::UUID,
        p_api_key,
        p_site_url,
        p_admin_email,
        p_metadata,
        p_domain,
        p_hmac_secret_encrypted,
        p_site_hash,
        CASE WHEN p_hmac_secret_encrypted IS NOT NULL THEN NOW() ELSE NULL END,
        NOW()
    );
    
    -- Return success
    RETURN TRUE;
    
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'Tenant registration failed due to duplicate data';
    WHEN OTHERS THEN
        -- Log the actual error and re-raise with context
        RAISE LOG 'register_tenant error for tenant_id %, site_url %: % %', 
                  p_tenant_id, p_site_url, SQLSTATE, SQLERRM;
        RAISE EXCEPTION 'Internal error during tenant registration: %', SQLERRM;
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION register_tenant TO authenticated;