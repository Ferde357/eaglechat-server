-- Create tenants table for API key management
CREATE TABLE tenants (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID UNIQUE NOT NULL,
  api_key TEXT UNIQUE NOT NULL,
  site_url TEXT,
  admin_email TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_seen_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB DEFAULT '{}'
);

-- Indexes for fast lookups
CREATE INDEX tenants_tenant_id_idx ON tenants(tenant_id);
CREATE INDEX tenants_api_key_idx ON tenants(api_key);
CREATE INDEX tenants_email_idx ON tenants(admin_email);

-- Function to validate tenant credentials
CREATE OR REPLACE FUNCTION validate_tenant(
  p_tenant_id UUID,
  p_api_key TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
  is_valid BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM tenants
    WHERE tenant_id = p_tenant_id
    AND api_key = p_api_key
    AND is_active = true
  ) INTO is_valid;
  
  -- Update last_seen_at if valid
  IF is_valid THEN
    UPDATE tenants
    SET last_seen_at = NOW()
    WHERE tenant_id = p_tenant_id;
  END IF;
  
  RETURN is_valid;
END;
$$;

-- Function to register new tenant
CREATE OR REPLACE FUNCTION register_tenant(
  p_tenant_id UUID,
  p_api_key TEXT,
  p_site_url TEXT,
  p_admin_email TEXT,
  p_metadata JSONB DEFAULT '{}'
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
  
  -- Insert new tenant
  INSERT INTO tenants (tenant_id, api_key, site_url, admin_email, metadata)
  VALUES (p_tenant_id, p_api_key, p_site_url, p_admin_email, p_metadata);
  
  RETURN jsonb_build_object('success', true, 'tenant_id', p_tenant_id);
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;