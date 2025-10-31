-- Conversations and Messages Tables for Eagle Chat
-- Run this in your Supabase SQL editor

-- Create conversations table
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
  session_id VARCHAR(255) NOT NULL,
  user_ip VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  -- Ensure unique session per tenant
  UNIQUE(tenant_id, session_id)
);

-- Create messages table
CREATE TABLE conversation_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL,
  message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}', -- Store token count, model used, response time, etc.
  
  -- Foreign key constraint
  FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX conversations_tenant_id_idx ON conversations(tenant_id);
CREATE INDEX conversations_session_id_idx ON conversations(session_id);
CREATE INDEX conversations_created_at_idx ON conversations(created_at DESC);
CREATE INDEX conversations_tenant_session_idx ON conversations(tenant_id, session_id);

CREATE INDEX messages_conversation_id_idx ON conversation_messages(conversation_id);
CREATE INDEX messages_tenant_id_idx ON conversation_messages(tenant_id);
CREATE INDEX messages_timestamp_idx ON conversation_messages(timestamp DESC);
CREATE INDEX messages_tenant_timestamp_idx ON conversation_messages(tenant_id, timestamp DESC);

-- Function to create or get conversation
CREATE OR REPLACE FUNCTION get_or_create_conversation(
  p_tenant_id UUID,
  p_session_id VARCHAR(255),
  p_user_ip VARCHAR(45) DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  conversation_uuid UUID;
BEGIN
  -- Try to get existing conversation
  SELECT id INTO conversation_uuid
  FROM conversations
  WHERE tenant_id = p_tenant_id AND session_id = p_session_id;
  
  -- Create new conversation if doesn't exist
  IF conversation_uuid IS NULL THEN
    INSERT INTO conversations (tenant_id, session_id, user_ip, user_agent)
    VALUES (p_tenant_id, p_session_id, p_user_ip, p_user_agent)
    RETURNING id INTO conversation_uuid;
  END IF;
  
  RETURN conversation_uuid;
END;
$$;

-- Function to add message to conversation
CREATE OR REPLACE FUNCTION add_conversation_message(
  p_tenant_id UUID,
  p_session_id VARCHAR(255),
  p_message_type VARCHAR(20),
  p_content TEXT,
  p_metadata JSONB DEFAULT '{}',
  p_user_ip VARCHAR(45) DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  conversation_uuid UUID;
  message_uuid UUID;
BEGIN
  -- Get or create conversation
  conversation_uuid := get_or_create_conversation(p_tenant_id, p_session_id, p_user_ip, p_user_agent);
  
  -- Add message
  INSERT INTO conversation_messages (conversation_id, tenant_id, message_type, content, metadata)
  VALUES (conversation_uuid, p_tenant_id, p_message_type, p_content, p_metadata)
  RETURNING id INTO message_uuid;
  
  -- Update conversation timestamp
  UPDATE conversations 
  SET updated_at = NOW()
  WHERE id = conversation_uuid;
  
  RETURN message_uuid;
END;
$$;

-- Function to get conversation history for tenant
CREATE OR REPLACE FUNCTION get_conversation_history(
  p_tenant_id UUID,
  p_limit INTEGER DEFAULT 100,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  conversation_id UUID,
  session_id VARCHAR(255),
  message_id UUID,
  message_type VARCHAR(20),
  content TEXT,
  timestamp TIMESTAMP WITH TIME ZONE,
  metadata JSONB
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    c.id as conversation_id,
    c.session_id,
    m.id as message_id,
    m.message_type,
    m.content,
    m.timestamp,
    m.metadata
  FROM conversations c
  JOIN conversation_messages m ON c.id = m.conversation_id
  WHERE c.tenant_id = p_tenant_id
  ORDER BY m.timestamp DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$;

-- Function to get single conversation messages
CREATE OR REPLACE FUNCTION get_conversation_messages(
  p_tenant_id UUID,
  p_session_id VARCHAR(255)
)
RETURNS TABLE (
  message_id UUID,
  message_type VARCHAR(20),
  content TEXT,
  timestamp TIMESTAMP WITH TIME ZONE,
  metadata JSONB
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    m.id as message_id,
    m.message_type,
    m.content,
    m.timestamp,
    m.metadata
  FROM conversations c
  JOIN conversation_messages m ON c.id = m.conversation_id
  WHERE c.tenant_id = p_tenant_id AND c.session_id = p_session_id
  ORDER BY m.timestamp ASC;
END;
$$;

-- Function to count conversations for tenant
CREATE OR REPLACE FUNCTION count_tenant_conversations(
  p_tenant_id UUID
)
RETURNS INTEGER
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  conversation_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO conversation_count
  FROM conversations
  WHERE tenant_id = p_tenant_id;
  
  RETURN conversation_count;
END;
$$;