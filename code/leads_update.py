from db import sync_connection

def update_chat_info(session_id: str, status: str = None, remarks: str = None, is_active: bool = None):
    """
    Insert or update a row in chat_info and return the updated row.
    """
    try:
        sync_connection.rollback()
        
        with sync_connection.cursor() as cur:
            insert_query = """
            INSERT INTO chat_info (
                session_id,
                status, 
                remarks,
                is_active
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (session_id) 
            DO UPDATE SET 
                status = CASE 
                    WHEN EXCLUDED.status IS NOT NULL THEN EXCLUDED.status 
                    ELSE chat_info.status 
                END,
                remarks = CASE 
                    WHEN EXCLUDED.remarks IS NOT NULL THEN EXCLUDED.remarks 
                    ELSE chat_info.remarks 
                END,
                is_active = CASE 
                    WHEN EXCLUDED.is_active IS NOT NULL THEN EXCLUDED.is_active 
                    ELSE chat_info.is_active 
                END
            """
            
            cur.execute(insert_query, (
                session_id,
                status,
                remarks,
                is_active
            ))

            sync_connection.commit()            
            
            # Log what was updated
            updates = []
            if status: updates.append(f"status='{status}'")
            if remarks: updates.append(f"remarks='{remarks}'")
            if is_active is not None: updates.append(f"is_active={1 if is_active else 0}")
            
            print(f"[DATABASE] Info updated for session {session_id}: {', '.join(updates) if updates else 'no new info'}")
    
    except Exception as e:
        sync_connection.rollback()
        print(f"[DATABASE ERROR] Failed to update lead for {session_id}: {str(e)}")
        raise