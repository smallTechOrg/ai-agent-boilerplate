from db import sync_connection

def update_chat_info(session_id: str, status: str = None, remarks: str = None, is_active: bool = None):
    """
    Insert or update a row in chat_info and return the updated row.
    """
    try:
        sync_connection.rollback()
        
        with sync_connection.cursor() as cur:
            update_query = """
                UPDATE chat_info 
                SET
                    status = COALESCE(%s, status),
                    remarks = COALESCE(%s, remarks),
                    is_active = COALESCE(%s, is_active)
                WHERE session_id = %s
                RETURNING *;
            """
            
            cur.execute(update_query, (
                status,
                remarks,
                is_active,
                session_id
            ))

            updated_row = cur.fetchone() 
            sync_connection.commit()            
            
            # Log what was updated
            updates = []
            if status: updates.append(f"status='{status}'")
            if remarks: updates.append(f"remarks='{remarks}'")
            if is_active is not None: updates.append(f"is_active={1 if is_active else 0}")
            
            print(f"[DATABASE] Info updated for session {session_id}: {', '.join(updates) if updates else 'no new info'}")
            return bool(updated_row)

    
    except Exception as e:
        sync_connection.rollback()
        print(f"[DATABASE ERROR] Failed to update lead for {session_id}: {str(e)}")
        raise