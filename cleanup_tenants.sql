-- Clean up existing tenant records for localhost:10003
-- This will remove any duplicate or orphaned records

-- Show current records first
SELECT 
    tenant_id,
    site_url, 
    admin_email,
    domain,
    created_at
FROM tenants 
WHERE site_url LIKE '%localhost:10003%' 
   OR site_url LIKE '%localhost%'
ORDER BY created_at DESC;

-- Delete records for localhost:10003
DELETE FROM tenants 
WHERE site_url LIKE '%localhost:10003%' 
   OR site_url LIKE '%localhost%';

-- Verify cleanup
SELECT COUNT(*) as remaining_localhost_records 
FROM tenants 
WHERE site_url LIKE '%localhost%';