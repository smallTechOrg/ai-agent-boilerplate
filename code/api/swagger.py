
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = ''  # URL for exposing Swagger UI
API_URL = '/static/swagger.yaml'  # Path to your swagger file

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL
)