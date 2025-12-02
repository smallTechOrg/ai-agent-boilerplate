from http import HTTPStatus
from urllib.parse import urlparse
from config import max_input_length, agent_type , status_type
import uuid
from db import sync_connection

class ValidationResponse:
    def __init__(self, is_valid, message, data=None):
        self.is_valid = is_valid 
        self.message = message
        self.data = data

    def is_valid(self):
        return self.is_valid

def chat_api_validate(request) -> ValidationResponse:
    data = request.get_json()
    input = data.get('input', '')
    request_type = data.get('request_type')
    address = get_request_address2(request)

    """Validates the chat user input. Returns (is_valid, message, address)."""
    result = None
    result = validate_chat_user_input(input)
    if not result.is_valid:
        return result
    
    try:
        request_type = agent_type(request_type.strip().lower()).value
    except (ValueError, AttributeError):
        request_type = agent_type.GENERIC.value  # <-- fallback string

    address_validation_response = validate_address2(address)
    if not address_validation_response.is_valid:
        return address_validation_response 
    
    return ValidationResponse(True, "", {"request_type":request_type, "domain":address_validation_response.data})

def validate_chat_user_input(input) -> ValidationResponse:
    input = input.strip()
    if not input:
        return ValidationResponse(False,"Please enter a message before sending.")
    if len(input) > max_input_length:
        return ValidationResponse(False, "Your message is too long. Please limit to {max_input_length} characters.")
    return ValidationResponse(True, "")


def validate_input(input, request_type, address):
    """Validates the chat user input. Returns (is_valid, message, address)."""
    input = input.strip()
    if not input:
        return {"is_valid":False, "message":"Please enter a message before sending."}

    if len(input) > max_input_length:
        return {"is_valid":False, "message":f"Your message is too long. Please limit to {max_input_length} characters."}
        
    # Normalize and validate request_type
    try:
        request_type = agent_type(request_type.strip().lower()).value  # <-- return string value
    except (ValueError, AttributeError):
        request_type = agent_type.GENERIC.value  # <-- fallback string
    valid_address, domain  = validate_address(address)
    if not valid_address:
        return {"is_valid":False, "message":"Incorrect Address"}        
    
    return {"is_valid":True, "message":"Input is valid", "data":{"request_type":request_type, "domain":domain}}


    
def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def validate_session_id(session_id):
    """Validate session_id and return chat history or create new session."""
    try:
        if session_id is None:
            return {"is_valid":False, "message":"session_id is required", "status":HTTPStatus.BAD_REQUEST}
        # Validate UUID format
        if not is_valid_uuid(session_id):
            return {"is_valid":False, "message":"Invalid session_id format", "status":HTTPStatus.BAD_REQUEST}
        return {"is_valid":True, "message":"Valid session_id", "status":HTTPStatus.OK}

    except Exception as e:
        print(f"[Error] {e}")
        return {"is_valid":False, "message":"Internal Server Error", "status":HTTPStatus.INTERNAL_SERVER_ERROR}
    
def validate_update_data(update_data, session_id, status, is_active):
    """Validate status and remarks """
    try:
        if not update_data or not session_id:
            return {"is_valid":False, "message":"session_id/data is required", "status":HTTPStatus.BAD_REQUEST}
        if status and status not in status_type.__members__ and status not in [s.value for s in status_type]:
            return {"is_valid":False, "message":"Status not allowed", "status":HTTPStatus.BAD_REQUEST}
        if is_active and not isinstance(is_active, bool):
            return {"is_valid":False, "message":"Invalid input", "status":HTTPStatus.BAD_REQUEST}
        return {"is_valid":True, "message":"Valid session_id", "status":HTTPStatus.OK}

    except Exception as e:
        print(f"[Error] {e}")
        return {"is_valid":False, "message":"Internal Server Error", "status":HTTPStatus.INTERNAL_SERVER_ERROR}
    
def validate_address(address):
    """Checks whether the given address exists. Returns (is_valid, domain or message)."""
    sync_connection.rollback()
    
    with sync_connection.cursor() as cur:
        cur.execute("SELECT key FROM domains WHERE address = %s;", (address,))
        row = cur.fetchone()

        if not row:
            return False, "Incorrect Address"
        
        return True, row[0]
    
def validate_address2(address):
    """Checks whether the given address exists. Returns (is_valid, domain or message)."""
    sync_connection.rollback()
    
    with sync_connection.cursor() as cur:
        cur.execute("SELECT key FROM domains WHERE address = %s;", (address,))
        row = cur.fetchone()

        if not row:
            return ValidationResponse(False, "Incorrect Address")
        
        return ValidationResponse(True, "",row[0])
    

def get_request_address2(request):
    origin = request.headers.get("Origin")
    if origin:
        return urlparse(origin).netloc
    return None