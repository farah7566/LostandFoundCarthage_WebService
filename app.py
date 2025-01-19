import os
from datetime import timedelta
from flask import Flask, jsonify, render_template
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename
from db import db
import uuid
from dotenv import load_dotenv
from resources.lost_item import blp as LostItemBlueprint
from resources.user import blp as UserBlueprint

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'secretlostandfoundkey')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'

# Add API title and version
app.config['API_TITLE'] = "Lost and Found API"
app.config['API_VERSION'] = "1.0"
app.config['OPENAPI_VERSION'] = "3.0.2"

# Initialize the Flask-JWT manager
jwt = JWTManager(app)

# Initialize the database
db.init_app(app)

# Initialize Flask-Smorest API
api = Api(app)

# Register Blueprints
api.register_blueprint(LostItemBlueprint)
api.register_blueprint(UserBlueprint)

# Swagger UI setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swagger_ui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Lost and Found API"})
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

@app.before_first_request
def create_tables():
    db.create_all()

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Route to serve index.html
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)