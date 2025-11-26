import json
from pathlib import Path
from functools import lru_cache
from db import sync_connection
from prompts_table import check_and_insert_default_prompts

check_and_insert_default_prompts(sync_connection)
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
    # Load both prompts from DB
    common_data = load_prompt_from_db("common", "contact_us", "system")
    company_data = load_prompt_from_db("smallTech.in", "contact_us", "company")

    # Extract "system" arrays safely
    common_parts = common_data["system"] if isinstance(common_data, dict) and "system" in common_data else [common_data]
    company_parts = company_data["system"] if isinstance(company_data, dict) and "system" in company_data else [company_data]

    # Merge arrays
    merged_parts = common_parts + company_parts

    # Join them into one prompt string
    return "\n".join(merged_parts)

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