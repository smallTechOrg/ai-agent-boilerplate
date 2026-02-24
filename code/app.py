from flask import Flask
from flask_cors import CORS 
from config import DEBUG
from api import register_blueprints

app = Flask(__name__)
register_blueprints(app)
CORS(app)

if __name__ == '__main__':
    app.run(debug=DEBUG,port=5001)