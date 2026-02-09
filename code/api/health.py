from flask import Blueprint, jsonify
from db import sync_connection

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint that verifies the shared database connection is still alive.
    This tests the same connection that other APIs use.
    """
    status = {
        "message": "Hello World",
        "database": "disconnected"
    }
    
    try:
        # Check if the shared connection is still active
        with sync_connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        status["database"] = "connected"
        return jsonify(status), 200
    except Exception as e:
        status["database"] = "disconnected"
        status["database_error"] = str(e)
        return jsonify(status), 503