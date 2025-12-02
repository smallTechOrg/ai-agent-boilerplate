
from http import HTTPStatus
import traceback
from urllib.parse import urlparse
from flask import Blueprint, jsonify, request
from history import get_history
from leads import get_all_chat_info
from leads_update import update_chat_info
from llm_api import get_groq_response
from api.validators import ValidationResponse, validate_address, validate_session_id, validate_update_data, chat_api_validate
from config import max_input_length, agent_type , status_type

chat_bp = Blueprint("chat", __name__)

#Rendering response
# chat_api is a Flask route function defined that acts as the backend API endpoint for chat exchanges. It is the API endpoint your frontend calls to send user messages and receive chatbot responses.
# It receives a JSON request containing the user's chat input from the frontend, validates the input, sends the validated input to the LLM, and returns a JSON response.

class APIResponse:
    def __init__(self, validation_response=None, data=None):
        self.validation_response = validation_response 
        self.data = data
    
    def response(self, http_status=None):
        if http_status == HTTPStatus.BAD_REQUEST:
            return jsonify({
                'success': self.validation_response.is_valid,
                'error': self.validation_response.message}), http_status
        elif http_status == HTTPStatus.OK:
            return jsonify({
                'success': True, 
                'response': self.data
                }), http_status
        else:
            return jsonify({
            'success': False,
            'error': "Sorry, something went wrong while processing your message. Please try again later."}), http_status



@chat_bp.route('/chat', methods=['POST'])
def chat_api():
    # Validate Request
    chat_validation_response = chat_api_validate(request)
    if not chat_validation_response.is_valid:
        return APIResponse(chat_validation_response).response(HTTPStatus.BAD_REQUEST)
    
     # Get response from LLM
    data = request.get_json()
    input = data.get('input', '')
    session_id = data.get('session_id')
    request_type = chat_validation_response.data["request_type"]
    domain = chat_validation_response.data["domain"]
    try:
        bot_response = get_groq_response(input.strip(), session_id, request_type, domain)
        return APIResponse(None,bot_response).response(HTTPStatus.OK)
    except Exception as e:
        print(f"Error during LLM call: {e}")
        err = traceback.format_exc()
        print(err)
        return APIResponse().response(HTTPStatus.INTERNAL_SERVER_ERROR)


@chat_bp.route('/chat-info', methods=['PATCH'])
def patch_updates():
    try:
        update_data = request.get_json()
        session_id = update_data.get("session_id")
        status = update_data.get("status")
        remarks = update_data.get("remarks")
        is_active = update_data.get("is_active")

        #validate update data
        result = validate_update_data(update_data, session_id, status,is_active)
        if not result["is_valid"]:
            return jsonify({"error": result["message"]}), result["status"]
        updated = update_chat_info(session_id, status, remarks, is_active)
        if updated:
            return jsonify({"success":True, "message":"chat-info updated"}), HTTPStatus.OK
        else:
            return jsonify({"success":False, "message":"Invalid Input"}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unable to update chat-info. Please try again later. ({str(e)})"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@chat_bp.route('/chat-info', methods=['GET'])
def get_chat_info():
    try:
        leads_data, status = get_all_chat_info()
        return jsonify({"leads":leads_data}), status
    except Exception as e:
        print(f"Error in get_leads endpoint: {e}")
        return jsonify({
            "error": "Unable to fetch chat info. Please try again later."
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# History API to load previous messages while loading the page
@chat_bp.route("/history", methods=["GET"])
def history_endpoint():
    session_id = request.args.get("session_id")
    address = get_request_address()

    # Validate
    result = validate_session_id(session_id)
    if not result["is_valid"]:
        return jsonify({"error": result["message"]}), result["status"]
    
    valid_address, domain  = validate_address(address)
    if not valid_address:
        return jsonify({"error": "Incorrect Address"}), HTTPStatus.BAD_REQUEST
    
    # Continue if valid
    history_data, status = get_history(session_id, domain)
    return jsonify(history_data), status

def get_request_address():
    origin = request.headers.get("Origin")
    if origin:
        return urlparse(origin).netloc
    return None

