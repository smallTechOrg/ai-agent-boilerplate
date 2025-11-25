import psycopg
from config import DATABASE_URL

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
                    ('common', 'contact_us', 'name_prompt', 'May I know your name?'),
                    ('common', 'contact_us', 'email_prompt', 'Could you share your email address?'),
                    ('common', 'contact_us', 'mobile_prompt', 'May I get your phone number?'),
                    ('common', 'contact_us', 'request_prompt', 'How may we assist you today?'),

                    ('smalltech.in', 'contact_us', 'intro', 'Welcome to SmallTech! How can we help you?'),
                ]

                for domain, agent_type, prompt_type, text in default_prompts:
                    cur.execute("""
                        INSERT INTO prompts (domain, agent_type, type, text)
                        VALUES (%s, %s, %s, %s);
                    """, (domain, agent_type, prompt_type, text))

                sync_connection.commit()
                print("Default prompts inserted successfully.")
            else:
                print("Prompts table already contains data. No insertion needed.")

    except Exception as e:
        print(f"Error inserting prompts: {e}")
        sync_connection.rollback()


def populate_prompts():
    """
    Standalone runner for prompt population.
    """
    try:
        conn = psycopg.connect(DATABASE_URL)
        conn.autocommit = False

        check_and_insert_default_prompts(conn)

        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")


if __name__ == "__main__":
    populate_prompts()
