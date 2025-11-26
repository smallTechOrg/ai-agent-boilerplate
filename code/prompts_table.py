import psycopg
from db import sync_connection
import json
from pathlib import Path
from functools import lru_cache
from config import first_chat_message


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
                    ('common', 'info-extraction', 'fetch-name', Path("prompts/name_prompt.json")),
                    ('common', 'info-extraction', 'fetch-info',  Path("prompts/info_prompt.json")),
                    ('common', 'test', 'test', Path("prompts/generic_prompt.json")),
                    ('common', 'contact_us', 'system', Path("prompts/sales_prompt.json")),
                    ('smallTech.in', 'contact_us', 'company', Path("prompts/smallTech.json")),

                    ('smalltech.in', 'contact_us', 'intro', first_chat_message),
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


if __name__ == "__main__":
    check_and_insert_default_prompts(sync_connection)
