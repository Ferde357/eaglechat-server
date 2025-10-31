-- Function to remove a specific API key for a tenant
CREATE OR REPLACE FUNCTION remove_tenant_api_key(
  p_tenant_id UUID,
  p_provider TEXT  -- 'anthropic' or 'openai'
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
  
  -- Remove the specific API key
  IF p_provider = 'anthropic' THEN
    UPDATE tenants 
    SET 
      anthropic_api_key_encrypted = NULL,
      api_keys_updated_at = NOW()
    WHERE tenant_id = p_tenant_id;
  ELSIF p_provider = 'openai' THEN
    UPDATE tenants 
    SET 
      openai_api_key_encrypted = NULL,
      api_keys_updated_at = NOW()
    WHERE tenant_id = p_tenant_id;
  ELSE
    RETURN jsonb_build_object('success', false, 'error', 'invalid provider');
  END IF;
  
  RETURN jsonb_build_object('success', true, 'tenant_id', p_tenant_id, 'provider', p_provider, 'removed_at', NOW());
EXCEPTION
  WHEN OTHERS THEN
    RETURN jsonb_build_object('success', false, 'error', SQLERRM);
END;
$$;