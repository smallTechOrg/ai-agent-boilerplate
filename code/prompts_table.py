import psycopg
import json
from pathlib import Path
from functools import lru_cache
from config import first_chat_message, agent_type, DEFAULT_DOMAIN


def load_json(path: Path):
    """
    Load and return JSON content as a string.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data)  # ensure DB stores valid JSON text
    except Exception as e:
        print(f"Failed to load JSON file {path}: {e}")
        return None

def check_and_insert_default_prompts(sync_connection):
    """
    Check if the prompts table is empty, and insert default rows only if empty.
    """
    try:
        with sync_connection.cursor() as cur:
            # Check if the table is empty
            cur.execute("SELECT COUNT(*) FROM prompts;")
            count = cur.fetchone()[0]
            if count == 0:
                print("Prompts table is empty. Inserting default prompts...")

                default_prompts = [
                    (DEFAULT_DOMAIN, 'generic', 'fetch-name', Path("prompts/name_prompt.json")),
                    (DEFAULT_DOMAIN, 'sales', 'fetch-contact-info',  Path("prompts/info_prompt.json")),
                    (DEFAULT_DOMAIN, 'sales', 'base-prompt', Path("prompts/sales_prompt.json")),
                    (DEFAULT_DOMAIN, 'sales', 'company', Path("prompts/company.json")),
                    (DEFAULT_DOMAIN, 'sales', 'intro-message', first_chat_message),
                    (DEFAULT_DOMAIN, 'generic', 'system', Path("prompts/generic_prompt.json")),
                ]

                for domain, agent_type, prompt_type, text in default_prompts:

                    # If text is a file path → load JSON
                    if isinstance(text, Path):
                        text_json = load_json(text)
                        if text_json is None:
                            print(f"Skipping insertion for {text}")
                            continue
                        text_to_insert = text_json
                    else:
                        # Normal string (like `first_chat_message`)
                        text_to_insert = text


                    cur.execute("""
                        INSERT INTO prompts (domain, agent_type, type, text)
                        VALUES (%s, %s, %s, %s);
                    """, (domain, agent_type, prompt_type, text_to_insert))

                sync_connection.commit()
                print("Default prompts inserted successfully.")
            else:
                print("Prompts table already contains data. No insertion needed.")

    except Exception as e:
        print(f"Error inserting prompts: {e}")
        sync_connection.rollback()


def check_and_insert_default_domains(sync_connection):
    with sync_connection.cursor() as cur:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS domains (
            id SERIAL PRIMARY KEY,
            key TEXT NOT NULL,
            address TEXT,
            parent INTEGER REFERENCES domains(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (key, address)
        );
        
        -- Insert a default row if it doesn't exist
        INSERT INTO domains (key, address, parent)
        VALUES ('COMMON', 'example.com', NULL)
        ON CONFLICT (key, address) DO NOTHING;
        """
        cur.execute(create_table_sql)
        sync_connection.commit()

