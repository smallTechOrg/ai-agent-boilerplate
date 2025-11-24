import os
import uuid
import psycopg
from langchain_postgres import PostgresChatMessageHistory
from config import DATABASE_URL, db_name, table_name

def ensure_database_exists(DATABASE_URL, db_name):
    """
    Connect to the 'postgres' system database. Create db_name if not exists.
    """
    # Parse from URL for creation
    base_url = DATABASE_URL.rsplit('/', 1)[0]
    postgres_url = f"{base_url}/postgres"
        
    # First, ensure the database exists

    with psycopg.connect(postgres_url) as temp_conn:
        temp_conn.autocommit = True
        with temp_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")


def create_sync_connection(DATABASE_URL):
    """
    Establish a connection to the specified database.
    """
    conn = psycopg.connect(DATABASE_URL)
    conn.autocommit = False
    return conn

def ensure_chat_table_exists(sync_connection, table_name):
    """
    Use LangChain's helper to make sure the chat history table exists.
    """
    PostgresChatMessageHistory.create_tables(sync_connection, table_name)
    print(f"Table '{table_name}' created or verified.")


def ensure_summaries_table_exists(sync_connection):
    """
    Create the chat_info table for storing lead information and summaries.
    """
    try:
        with sync_connection.cursor() as cur:
            # Create the chat_info table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS chat_info (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                contact_name TEXT,
                email TEXT,
                mobile TEXT,
                country TEXT,
                request_type TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                
                -- Add constraint to prevent duplicate summaries for same session
                UNIQUE(session_id)
            );
            
            -- Create indexes for efficient querying
            CREATE INDEX IF NOT EXISTS idx_chat_info_session_id 
            ON chat_info(session_id);
            
            
            CREATE INDEX IF NOT EXISTS idx_chat_info_created_at 
            ON chat_info(created_at);
            """
            
            cur.execute(create_table_query)

            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS contact_name TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS email TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS country TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS mobile TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS request_type TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;")

            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'OPEN';")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS remarks TEXT;")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS domain TEXT DEFAULT 'smalltech.in';")
            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS agent_type TEXT DEFAULT 'contact_us';")

            cur.execute("ALTER TABLE chat_info ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")

            sync_connection.commit()
            print("Table 'chat_info' created/verified successfully.")
            
    except Exception as e:
        print(f"Error creating chat_info table: {e}")
        sync_connection.rollback()

def ensure_prompts_table_exists(sync_connection):
    """
    Create or verify a 'prompts' table with columns:
      - domain : domain, under which prompt is, example as common, smalltech, client
      - agent_type -- Determines the type of agent, example as Sales, generic
      - type -- What the prompt use for, example as name_prompt, sales prompt, info_prompt, generic
      - text -- prompt itself
    """
    try:
        with sync_connection.cursor() as cur:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS prompts (
                id SERIAL PRIMARY KEY,
                domain Text DEFAULT 'common',
                agent_type TEXT NOT NULL,
                type TEXT NOT NULL,
                "text" TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            cur.execute(create_table_sql)
            sync_connection.commit()
            print("Table 'prompts' created/verified successfully.")
    except Exception as e:
        print(f"Error creating prompts table: {e}")
        sync_connection.rollback()

def ensure_domains_table_exists(sync_connection):
    """
    Create or verify a 'domains' table with columns:
      - key : unique identifier example common, smalltech, client
      - address : url for the example domain smalltech.in
      - parent key : parent key for domain key
    Note: column name 'key' will be created quoted to avoid ambiguity; it's still a valid column name.
    """
    try:
        with sync_connection.cursor() as cur:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS domains (
                id SERIAL PRIMARY KEY,
                "key" TEXT NOT NULL UNIQUE,
                address TEXT,
                parent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            """
            cur.execute(create_table_sql)
            sync_connection.commit()
            print("Table 'domains' created/verified successfully.")
    except Exception as e:
        print(f"Error creating domains table: {e}")
        sync_connection.rollback()

def setup_database_and_table(database_url, table_name):
    """
    Orchestrates DB and table setup, returns the live connection and table name.
    """
    try:
        ensure_database_exists(DATABASE_URL, db_name)
        sync_connection = create_sync_connection(DATABASE_URL)

        ensure_chat_table_exists(sync_connection, table_name)
        ensure_summaries_table_exists(sync_connection)
        ensure_prompts_table_exists(sync_connection)
        ensure_domains_table_exists(sync_connection)

        return sync_connection, table_name
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise
        

# Usage — get the ready connection and table name
sync_connection, table_name = setup_database_and_table(DATABASE_URL, table_name)
