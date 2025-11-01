-- Migration: Add domain verification support to tenants table
-- Date: 2024-11-01
-- Purpose: Enable HMAC with domain verification for enhanced security

-- Add columns for domain verification and HMAC secrets
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS hmac_secret_encrypted TEXT,
ADD COLUMN IF NOT EXISTS domain VARCHAR(255),
ADD COLUMN IF NOT EXISTS site_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS hmac_secret_updated_at TIMESTAMP DEFAULT NOW();

-- Create index for domain lookups
CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain);

-- Create index for site_hash lookups
CREATE INDEX IF NOT EXISTS idx_tenants_site_hash ON tenants(site_hash);

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS register_tenant;
DROP FUNCTION IF EXISTS update_tenant_hmac_domain;
DROP FUNCTION IF EXISTS get_tenant_hmac_domain;

-- Update the register_tenant function to handle domain and HMAC data
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
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSONB;
BEGIN
    -- Check if tenant_id already exists
    IF EXISTS (SELECT 1 FROM tenants WHERE tenant_id = p_tenant_id::UUID) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Tenant ID already exists'
        );
    END IF;

    -- Check if site URL already registered
    IF EXISTS (SELECT 1 FROM tenants WHERE site_url = p_site_url) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Site URL already registered'
        );
    END IF;

    -- Check if admin email already used
    IF EXISTS (SELECT 1 FROM tenants WHERE admin_email = p_admin_email) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Admin email already associated with another tenant'
        );
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

    -- Return success with tenant info
    RETURN jsonb_build_object(
        'success', true,
        'tenant_id', p_tenant_id,
        'message', 'Tenant registered successfully',
        'hmac_configured', CASE WHEN p_hmac_secret_encrypted IS NOT NULL THEN true ELSE false END
    );

EXCEPTION
    WHEN unique_violation THEN
        -- Handle race conditions
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Tenant registration failed due to duplicate data'
        );
    WHEN OTHERS THEN
        -- Log the error and return generic message
        RAISE LOG 'register_tenant error: %', SQLERRM;
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Internal error during tenant registration'
        );
END;
$$;

-- Create function to update tenant HMAC secret and domain info
CREATE OR REPLACE FUNCTION update_tenant_hmac_domain(
    p_tenant_id TEXT,
    p_hmac_secret_encrypted TEXT,
    p_domain TEXT,
    p_site_hash TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSONB;
BEGIN
    -- Update tenant with new HMAC and domain data
    UPDATE tenants
    SET
        hmac_secret_encrypted = p_hmac_secret_encrypted,
        domain = p_domain,
        site_hash = p_site_hash,
        hmac_secret_updated_at = NOW()
    WHERE tenant_id = p_tenant_id::UUID;

    -- Check if update was successful
    IF FOUND THEN
        RETURN jsonb_build_object(
            'success', true,
            'message', 'HMAC and domain data updated successfully'
        );
    ELSE
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Tenant not found'
        );
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE LOG 'update_tenant_hmac_domain error: %', SQLERRM;
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Internal error during HMAC update'
        );
END;
$$;

-- Create function to get tenant HMAC and domain data
CREATE OR REPLACE FUNCTION get_tenant_hmac_domain(p_tenant_id TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    tenant_data RECORD;
BEGIN
    -- Get tenant HMAC and domain information
    SELECT
        hmac_secret_encrypted,
        domain,
        site_hash,
        hmac_secret_updated_at
    INTO tenant_data
    FROM tenants
    WHERE tenant_id = p_tenant_id::UUID;

    IF FOUND THEN
        RETURN jsonb_build_object(
            'success', true,
            'hmac_secret_encrypted', tenant_data.hmac_secret_encrypted,
            'domain', tenant_data.domain,
            'site_hash', tenant_data.site_hash,
            'hmac_secret_updated_at', tenant_data.hmac_secret_updated_at
        );
    ELSE
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Tenant not found'
        );
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        RAISE LOG 'get_tenant_hmac_domain error: %', SQLERRM;
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Internal error retrieving tenant data'
        );
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION register_tenant TO authenticated;
GRANT EXECUTE ON FUNCTION update_tenant_hmac_domain TO authenticated;
GRANT EXECUTE ON FUNCTION get_tenant_hmac_domain TO authenticated;

-- Add comments for documentation
COMMENT ON COLUMN tenants.hmac_secret_encrypted IS 'Encrypted HMAC secret for request signing';
COMMENT ON COLUMN tenants.domain IS 'Normalized domain name for origin verification';
COMMENT ON COLUMN tenants.site_hash IS 'SHA256 hash of domain + site identifier for verification';
COMMENT ON COLUMN tenants.hmac_secret_updated_at IS 'Timestamp when HMAC secret was last updated';

COMMENT ON FUNCTION register_tenant IS 'Register new tenant with optional HMAC and domain verification data';
COMMENT ON FUNCTION update_tenant_hmac_domain IS 'Update tenant HMAC secret and domain verification data';
COMMENT ON FUNCTION get_tenant_hmac_domain IS 'Retrieve tenant HMAC and domain verification data';