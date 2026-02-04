from flask import Blueprint, jsonify
import psycopg
from config import DATABASE_URL

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint that verifies application and database connectivity.
    """
    status = {
        "message": "Hello World",
        "database": "disconnected"
    }
    
    try:
        # Check database connectivity
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        status["database"] = "connected"
        return jsonify(status), 200
    except Exception as e:
        status["database_error"] = str(e)
        return jsonify(status), 503