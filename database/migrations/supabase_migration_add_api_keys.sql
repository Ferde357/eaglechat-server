-- Migration: Add encrypted AI API key storage to tenants table
-- Date: 2024-10-29
-- Purpose: Store encrypted Anthropic and OpenAI API keys per tenant

-- Add encrypted API key columns to tenants table
ALTER TABLE tenants 
ADD COLUMN anthropic_api_key_encrypted TEXT,
ADD COLUMN openai_api_key_encrypted TEXT,
ADD COLUMN api_keys_updated_at TIMESTAMP WITH TIME ZONE;

-- Add index for efficient API key lookups
CREATE INDEX tenants_api_keys_updated_idx ON tenants(api_keys_updated_at);

-- Add comments for documentation
COMMENT ON COLUMN tenants.anthropic_api_key_encrypted IS 'Encrypted Anthropic Claude API key for this tenant';
COMMENT ON COLUMN tenants.openai_api_key_encrypted IS 'Encrypted OpenAI GPT API key for this tenant';
COMMENT ON COLUMN tenants.api_keys_updated_at IS 'Timestamp when API keys were last updated';

-- Function to update tenant API keys
CREATE OR REPLACE FUNCTION update_tenant_api_keys(
  p_tenant_id UUID,
  p_anthropic_key_encrypted TEXT DEFAULT NULL,
  p_openai_key_encrypted TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  result JSONB;
  tenant_exists BOOLEAN;
BEGIN
  -- Check if tenant exists
  SELECT EXISTS(
    SELECT 1 FROM tenants 
    WHERE tenant_id = p_tenant_id 
    AND is_active = true
  ) INTO tenant_exists;
  
  IF NOT tenant_exists THEN
    RETURN jsonb_build_object('success', false, 'error', 'tenant not found or inactive');
  END IF;
  
  -- Update API keys (only update non-NULL values)
  UPDATE tenants 
  SET 
    anthropic_api_key_encrypted = COALESCE(p_anthropic_key_encrypted, anthropic_api_key_encrypted),
    openai_api_key_encrypted = COALESCE(p_openai_key_encrypted, openai_api_key_encrypted),
    api_keys_updated_at = NOW()
  WHERE tenant_id = p_tenant_id;
  
  RETURN jsonb_build_object('success', true, 'tenant_id', p_tenant_id, 'updated_at', NOW());
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;

-- Function to get tenant API keys
CREATE OR REPLACE FUNCTION get_tenant_api_keys(
  p_tenant_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  result JSONB;
BEGIN
  SELECT jsonb_build_object(
    'tenant_id', tenant_id,
    'anthropic_api_key_encrypted', anthropic_api_key_encrypted,
    'openai_api_key_encrypted', openai_api_key_encrypted,
    'api_keys_updated_at', api_keys_updated_at
  )
  INTO result
  FROM tenants 
  WHERE tenant_id = p_tenant_id 
  AND is_active = true;
  
  IF result IS NULL THEN
    RETURN jsonb_build_object('success', false, 'error', 'tenant not found or inactive');
  END IF;
  
  RETURN jsonb_build_object('success', true, 'data', result);
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;

-- Function to delete tenant API keys (for security/cleanup)
CREATE OR REPLACE FUNCTION delete_tenant_api_keys(
  p_tenant_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE tenants 
  SET 
    anthropic_api_key_encrypted = NULL,
    openai_api_key_encrypted = NULL,
    api_keys_updated_at = NOW()
  WHERE tenant_id = p_tenant_id;
  
  IF FOUND THEN
    RETURN jsonb_build_object('success', true, 'tenant_id', p_tenant_id, 'deleted_at', NOW());
  ELSE
    RETURN jsonb_build_object('success', false, 'error', 'tenant not found');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;

-- Update existing register_tenant function to handle new columns
DROP FUNCTION IF EXISTS register_tenant(UUID, TEXT, TEXT, TEXT, JSONB);

CREATE OR REPLACE FUNCTION register_tenant(
  p_tenant_id UUID,
  p_api_key TEXT,
  p_site_url TEXT,
  p_admin_email TEXT,
  p_metadata JSONB DEFAULT '{}',
  p_anthropic_key_encrypted TEXT DEFAULT NULL,
  p_openai_key_encrypted TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  result JSONB;
BEGIN
  -- Check if tenant_id or api_key already exists
  IF EXISTS(SELECT 1 FROM tenants WHERE tenant_id = p_tenant_id) THEN
    RETURN jsonb_build_object('success', false, 'error', 'tenant_id already exists');
  END IF;
  
  IF EXISTS(SELECT 1 FROM tenants WHERE api_key = p_api_key) THEN
    RETURN jsonb_build_object('success', false, 'error', 'api_key already exists');
  END IF;
  
  -- Insert new tenant with optional encrypted API keys
  INSERT INTO tenants (
    tenant_id, 
    api_key, 
    site_url, 
    admin_email, 
    metadata,
    anthropic_api_key_encrypted,
    openai_api_key_encrypted,
    api_keys_updated_at
  )
  VALUES (
    p_tenant_id, 
    p_api_key, 
    p_site_url, 
    p_admin_email, 
    p_metadata,
    p_anthropic_key_encrypted,
    p_openai_key_encrypted,
    CASE WHEN (p_anthropic_key_encrypted IS NOT NULL OR p_openai_key_encrypted IS NOT NULL) 
         THEN NOW() 
         ELSE NULL 
    END
  );
  
  RETURN jsonb_build_object('success', true, 'tenant_id', p_tenant_id);
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT EXECUTE ON FUNCTION update_tenant_api_keys TO service_role;
-- GRANT EXECUTE ON FUNCTION get_tenant_api_keys TO service_role;
-- GRANT EXECUTE ON FUNCTION delete_tenant_api_keys TO service_role;