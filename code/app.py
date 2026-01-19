from http import HTTPStatus
import os
from flask import Flask, render_template, request, jsonify
from llm_api import get_groq_response
from validators import validate_input, validate_session_id, validate_update_data, validate_address
from config import DEBUG
from flask_cors import CORS 
from flask_swagger_ui import get_swaggerui_blueprint
from prompts_table import get_all_prompts, upsert_prompt
from history import get_history
from leads import get_all_chat_info
from leads_update import update_chat_info
from urllib.parse import urlparse
import traceback

app = Flask(__name__)
CORS(app)


# Swagger UI setup
SWAGGER_URL = '/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.yaml'  # Path to your swagger file

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Chat API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

#render HTML frontend
@app.route('/')
def chat():
    return render_template('chat.html')

@app.route("/health", methods=["GET"])
def hello():
    return jsonify({"message": "Hello World"})

# History API to load previous messages while loading the page
@app.route("/history", methods=["GET"])
def history_endpoint():
    session_id = request.args.get("session_id")
    address = get_request_address(request)

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

@app.route('/chat-info', methods=['GET'])
def get_chat_info():
    try:
        leads_data, status = get_all_chat_info()
        return jsonify({"leads":leads_data}), status
    except Exception as e:
        print(f"Error in get_leads endpoint: {e}")
        return jsonify({
            "error": "Unable to fetch chat info. Please try again later."
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/chat-info', methods=['PATCH'])
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


#Rendering response
# chat_api is a Flask route function defined that acts as the backend API endpoint for chat exchanges. It is the API endpoint your frontend calls to send user messages and receive chatbot responses.
# It receives a JSON request containing the user's chat input from the frontend, validates the input, sends the validated input to the LLM, and returns a JSON response.

@app.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    input = data.get('input', '')
    session_id = data.get('session_id')
    request_type = data.get('request_type')
    address = get_request_address(request)
    # Input Validation

    result = validate_input(input, request_type, address)

    if not result["is_valid"]:
        return jsonify({'success': False, 'error': result["message"]}), HTTPStatus.BAD_REQUEST
    request_type = result["data"]["request_type"]
    domain = result["data"]["domain"]

    # Get response from LLM
    try:
        bot_response = get_groq_response(input.strip(), session_id, request_type, domain)
        return jsonify({'success': True, 'response': bot_response})
    except Exception as e:
        print(f"Error during LLM call: {e}")
        err = traceback.format_exc()
        print(err)
        return jsonify({
            'success': False,
            'error': "Sorry, something went wrong while processing your message. Please try again later."}), HTTPStatus.INTERNAL_SERVER_ERROR


# --- New Prompt APIs ---
@app.route('/prompts', methods=['GET'])
def get_prompts():
    from db import sync_connection
    prompts = get_all_prompts(sync_connection)
    return jsonify({"prompts": prompts}), 200

@app.route('/prompt', methods=['POST'])
def create_or_update_prompt():
    from db import sync_connection
    data = request.get_json()
    domain = data.get('domain')
    agent_type = data.get('agent_type')
    prompt_type = data.get('type')
    text = data.get('text')
    if not all([domain, agent_type, prompt_type, text]):
        return jsonify({"success": False, "error": "Missing required fields: domain, agent_type, type, text"}), 400
    success = upsert_prompt(sync_connection, domain, agent_type, prompt_type, text)
    if success:
        return jsonify({"success": True, "message": "Prompt created/updated."}), 200
    else:
        return jsonify({"success": False, "error": "Failed to create/update prompt."}), 500




def get_request_address(request):
    origin = request.args.get("origin")
    if not origin or not str(origin).strip():
        origin = request.headers.get("Origin")
    if origin:
        return urlparse(origin).netloc
    return None

if __name__ == '__main__':
    app.run(debug=DEBUG,port=5000)


