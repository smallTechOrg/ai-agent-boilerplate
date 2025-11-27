import json
from pathlib import Path
from functools import lru_cache
from db import sync_connection
from config import DEFAULT_DOMAIN, agent_type

def get_generic_prompt():
    data = load_prompt_from_db(DEFAULT_DOMAIN, "generic", "test")

    if isinstance(data, dict) and "system" in data:
        return "\n".join(data["system"])

    # If plain text:
    return data["system"]

def get_prompt(domain, agent_type, prompt_type):
    # Load both prompts from DB
    if prompt_type == "system":

        if agent_type == "sales":
            common_data = load_prompt_from_db(domain, agent_type, "base-prompt")
            # if common_data is None:
            #     # Use default or find parent.
            #     common_data = load_prompt_from_db(DEFAULT_DOMAIN, agent_type, "base-prompt")
            company_data = load_prompt_from_db(domain, agent_type, "company")    
            # if company_data is None:
            #     company_data = load_prompt_from_db(DEFAULT_DOMAIN, agent_type, "company") 
                
            # Extract "system" arrays safely
            common_parts = common_data["system"] if isinstance(common_data, dict) and "system" in common_data else [common_data]
            company_parts = company_data["system"] if isinstance(company_data, dict) and "system" in company_data else [company_data]

            # Merge arrays
            merged_parts = common_parts + company_parts

            # Join them into one prompt string
            return "\n".join(merged_parts)
        else:
            data =  load_prompt_from_db(domain, agent_type, prompt_type)
            if isinstance(data, dict) and "system" in data:
                return "\n".join(data["system"])
            return data["system"]
    else:
        data =  load_prompt_from_db(domain, agent_type, prompt_type)
        if isinstance(data, dict) and "system" in data:
            return "\n".join(data["system"])
        return data["system"]



def load_prompt_from_db(domain: str, agent_type: str, prompt_type: str):
    """
    Fetch a prompt's text from the DB (JSON or plain text), cache for fast access.
    """
    try:
        row = find_prompt(domain, agent_type, prompt_type)

        if row is None:
            print(f"Prompt not found in DB: {domain}/{agent_type}/{prompt_type}, looking for parent prompt")
            parent_domain = find_parent_key(domain) 
            row = find_prompt(parent_domain, agent_type, prompt_type)
            if row is None:
                print(f"Prompt not found in DB for parent Domain: {domain}/{agent_type}/{prompt_type}")
                return None

        text = row[0]

        # Try to parse JSON if stored as JSON string
        try:
            parsed = json.loads(text)
            return parsed
        except json.JSONDecodeError:
            return text  # raw string

    except Exception as e:
        raise RuntimeError(f"Failed to load prompt from DB: {e}")

def find_parent_key(key):
    with sync_connection.cursor() as cur:
        cur.execute("""
            SELECT parent.key
            FROM domains child
            LEFT JOIN domains parent ON child.parent = parent.id
            WHERE child.key = %s;
        """, (key,))
        row = cur.fetchone()
        return row[0] if row else None

def find_prompt(domain, agent_type, prompt_type):
    try:
        with sync_connection.cursor() as cur:
            cur.execute("""
                SELECT text 
                FROM prompts
                WHERE domain = %s AND agent_type = %s AND type = %s
                LIMIT 1;
            """, (domain, agent_type, prompt_type))

            row = cur.fetchone()
            return row
        
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt from DB: {e}")