import json
from pathlib import Path
from functools import lru_cache
from db import sync_connection

def load_prompt_from_db(domain: str, agent_type: str, prompt_type: str):
    """
    Fetch a prompt's text from the DB (JSON or plain text), cache for fast access.
    """
    try:
        with sync_connection.cursor() as cur:
            cur.execute("""
                SELECT text 
                FROM prompts
                WHERE domain = %s AND agent_type = %s AND type = %s
                LIMIT 1;
            """, (domain, agent_type, prompt_type))

            row = cur.fetchone()

            if not row:
                raise ValueError(f"Prompt not found in DB: {domain}/{agent_type}/{prompt_type}")

            text = row[0]

            # Try to parse JSON if stored as JSON string
            try:
                parsed = json.loads(text)
                return parsed
            except json.JSONDecodeError:
                return text  # raw string

    except Exception as e:
        raise RuntimeError(f"Failed to load prompt from DB: {e}")
    
def get_generic_prompt():
    data = load_prompt_from_db("common", "test", "test")

    if isinstance(data, dict) and "system" in data:
        return "\n".join(data["system"])

    # If plain text:
    return data["system"]

def get_sales_prompt():
    data = load_prompt_from_db("common", "contact_us", "system")
    if isinstance(data, dict) and "system" in data:
        return "\n".join(data["system"])
    return data["system"]

def get_name_prompt():
    data = load_prompt_from_db("common", "info-extraction", "fetch-name")
    if isinstance(data, dict) and "system" in data:
        return "\n".join(data["system"])
    return data["system"]

def get_info_prompt():
    data = load_prompt_from_db("common", "info-extraction", "fetch-info")
    if isinstance(data, dict) and "system" in data:
        return "\n".join(data["system"])
    return data["system"]    
