# Overview
- Vector dimension: 1536 (OpenAI text-embedding-3-small or ada-002)
- Similarity metric: cosine (vector_cosine_ops)
- Index type: ivfflat (good balance of speed/accuracy)
- Lists parameter: 100 (adjust higher for >1M vectors)

# Multi-Tenancy
- Each WP site gets a unique UUID (tenant ID)

# Python API enforces tenant isolation
results = supabase.rpc('match_documents', {
    'query_embedding': embedding,
    'tenant_filter': 'a1b2c3d4-...'  # Only returns this tenant's docs
})

## Script 1: Create the documents table*
-- Create table for storing embeddings with multi-tenant support
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding VECTOR(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX documents_tenant_id_idx ON documents(tenant_id);
CREATE INDEX documents_created_at_idx ON documents(created_at);
CREATE INDEX documents_embedding_idx ON documents 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Enable Row Level Security (not enforced with service_role key)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

## Script 2: Create the search function
-- Function to search documents within a tenant
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.3,
  match_count INT DEFAULT 5,
  tenant_filter UUID DEFAULT NULL
)
RETURNS TABLE (
  id BIGINT,
  tenant_id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.tenant_id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE 
    (tenant_filter IS NULL OR documents.tenant_id = tenant_filter)
    AND 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

## Helper function to add documents
-- Function to insert a document
CREATE OR REPLACE FUNCTION add_document(
  p_tenant_id UUID,
  p_content TEXT,
  p_metadata JSONB,
  p_embedding VECTOR(1536)
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  new_id BIGINT;
BEGIN
  INSERT INTO documents (tenant_id, content, metadata, embedding)
  VALUES (p_tenant_id, p_content, p_metadata, p_embedding)
  RETURNING id INTO new_id;
  
  RETURN new_id;
END;
$$;

## Bulk operations functions
-- Function to delete all documents for a tenant
CREATE OR REPLACE FUNCTION delete_tenant_documents(
  p_tenant_id UUID
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM documents
  WHERE tenant_id = p_tenant_id;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

-- Function to count documents per tenant
CREATE OR REPLACE FUNCTION count_tenant_documents(
  p_tenant_id UUID
)
RETURNS INTEGER
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  doc_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO doc_count
  FROM documents
  WHERE tenant_id = p_tenant_id;
  
  RETURN doc_count;
END;
$$;

-- Function to update document content and embedding
CREATE OR REPLACE FUNCTION update_document(
  p_id BIGINT,
  p_content TEXT,
  p_metadata JSONB,
  p_embedding VECTOR(1536)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE documents
  SET 
    content = p_content,
    metadata = p_metadata,
    embedding = p_embedding,
    updated_at = NOW()
  WHERE id = p_id;
  
  RETURN FOUND;
END;
$$;