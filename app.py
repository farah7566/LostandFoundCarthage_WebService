import os
import sqlite3
import uuid
from datetime import timedelta  # Corrected import

import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename

from db import db
from models import AgentLostItem, TravelerLostItem, User

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'secretlostandfoundkey'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Token expires in 1 hour
SECRET_KEY = "secretlostandfoundkey"  # Make sure to keep this secret safe!

jwt = JWTManager(app)  # Initialize JWTManager with the app

# Your existing config setup
app.config.from_object('config.Config')

db.init_app(app)  # Initialize db with the app

# Swagger UI setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swagger_ui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Lost and Found API"})
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# File upload setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Route to serve index.html
@app.route('/')
def index():
    return render_template('index.html')



@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")  # Get the role from the request

    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "Username already exists"}), 400

    # Check if role is provided
    if role not in ['traveler', 'agent']:
        return jsonify({"message": "Invalid role. Must be 'traveler' or 'agent'."}), 400

    # Create new user
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201



# Login route to authenticate and generate a JWT token
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # Check if the user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Check if password matches
    if user.password != password:
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate the access token and refresh token
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    # Include the user's role in the response
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': user.role  # Return the role of the user
    }), 200

# Protected route example, requires a valid JWT token to access
@app.route('/api/protected', methods=['GET'])
def protected():
    current_user = get_jwt_identity()  # Get the identity of the current user from the JWT token
    return jsonify({"message": f"Hello, {current_user}! This is a protected route."})


@app.route('/api/lost-items/report-by-traveler', methods=['POST'])
@jwt_required()  # Protect this route with JWT authentication
def report_lost_item_by_traveller():
    data = request.get_json()

    item_name = data.get('item_name')
    description = data.get('description')
    location_lost = data.get('location_lost')
    contact_info = data.get('contact_info')
    traveler_name = data.get('traveler_name')

    # Ensure 'claimed' is treated as a boolean (True or False)
    claimed = data.get('claimed', False)  # Default to False if 'claimed' is not provided
    if isinstance(claimed, str):
        claimed = claimed.lower() == 'true'  # Convert string 'true' to boolean True

    claimed_by = data.get('claimed_by', 'no one')  # Default to 'no one' if not provided

    # Check if essential information is provided
    if not item_name or not description or not location_lost or not contact_info or not traveler_name:
        return jsonify(
            {"error": "Item name, description, location, contact info, and traveler name are required."}), 400

    # Handle the image upload
    image = request.files.get('image')
    image_path = None  # Default value if no image is uploaded
    if image and allowed_file(image.filename):  # Check if image is valid
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

    # Create a new TravelerLostItem
    new_item = TravelerLostItem(
        lost_item_id=str(uuid.uuid4()),
        item_name=item_name,
        description=description,
        location_lost=location_lost,
        contact_info=contact_info,
        traveler_name=traveler_name,
        claimed=claimed,
        claimed_by=claimed_by,
        status='Lost',  # Default status for traveler-reported items
        image_path=image_path  # Store the image path (or None if no image)
    )

    # Add the new item to the database and commit
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "Lost item reported by traveler", "lost_item_id": new_item.lost_item_id}), 201

# Existing route to report lost items by agents
@app.route('/api/lost-items/report-by-agent', methods=['POST'])
def report_lost_item_by_agent():
    data = request.get_json()  # Extract JSON data

    item_name = data.get('item_name')
    description = data.get('description')
    status = data.get('status')
    image_path = data.get('image_path')

    if not item_name or not description or not status:
        return jsonify({"error": "Item name, description, and status are required."}), 400

    # For agent, location_lost and contact_info are optional
    location_lost = data.get('location_lost', "Not Provided")
    contact_info = data.get('contact_info', "Not Provided")

    # Handle the image upload (file data handled separately)
    image = request.files.get('image')
    if image and allowed_file(image.filename):
        # Secure the filename and save it
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
    else:
        image_path = None  # If no image or invalid file type

    # Create a new AgentLostItem
    new_item = AgentLostItem(
        lost_item_id=str(uuid.uuid4()),
        item_name=item_name,
        description=description,
        location_lost=location_lost,  # Optional for agent
        contact_info=contact_info,  # Optional for agent
        status=status,  # Status provided by agent (e.g., "Found")
        image_path=image_path  # Store the image path (can be URL if hosted externally)
    )

    # Add the new item to the database and commit
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "Lost item reported by airport agent", "lost_item_id": new_item.lost_item_id}), 201


# Route to retrieve a lost item by its ID
@app.route('/api/lost-items/<string:lost_item_id>', methods=['GET'])
def get_lost_item(lost_item_id):
    # Check if it's a traveler-reported item
    item = TravelerLostItem.query.filter_by(lost_item_id=lost_item_id).first()
    if not item:
        # Check if it's an agent-reported item
        item = AgentLostItem.query.filter_by(lost_item_id=lost_item_id).first()

    if item:
        return jsonify({
            "lost_item_id": item.lost_item_id,
            "item_name": item.item_name,
            "description": item.description,
            "location_lost": item.location_lost,
            "contact_info": item.contact_info,
            "status": item.status,
            "image_url": item.image_path if item.image_path else None  # If an image exists, return its path

        })
    return jsonify({"message": "Item not found"}), 404

# Route to list all lost items
@app.route('/api/lost-items', methods=['GET'])
def list_lost_items():
    # Query both traveler-reported and agent-reported items
    traveler_items = TravelerLostItem.query.all()
    agent_items = AgentLostItem.query.all()

    items_list = []

    # Add traveler-reported items to the list
    for item in traveler_items:
        items_list.append({
            "lost_item_id": item.lost_item_id,
            "item_name": item.item_name,
            "description": item.description,
            "location_lost": item.location_lost,
            "status": item.status,
            "reporter_type": "Traveler",
            "image_url": item.image_path
        })

    # Add agent-reported items to the list
    for item in agent_items:
        items_list.append({
            "lost_item_id": item.lost_item_id,
            "item_name": item.item_name,
            "description": item.description,
            "location_lost": item.location_lost,
            "status": item.status,
            "reporter_type": "Agent",
            "image_url": item.image_path
        })

    return jsonify(items_list)

# Route to update a lost item's status
@app.route('/api/lost-items/<lost_item_id>', methods=['PUT', 'PATCH'])
@jwt_required()

def update_lost_item_status(lost_item_id):
    item = TravelerLostItem.query.get(lost_item_id) or AgentLostItem.query.get(lost_item_id)

    if not item:
        return jsonify({"error": "Lost item not found"}), 404

    # Get status from the request body
    status = request.json.get('status')
    if not status:
        return jsonify({"error": "Status is required"}), 400

    item.status = status
    db.session.commit()

    return jsonify({"message": f"The status of the lost item has been updated to '{status}'."}), 200


@app.route('/api/lost-items/claim/<lost_item_id>', methods=['POST'])
@jwt_required()  # Protect the route with JWT
def claim_lost_item(lost_item_id):
    # Get the current user (the traveler making the claim)
    current_user = get_jwt_identity()

    # Find the lost item by ID
    lost_item = TravelerLostItem.query.filter_by(lost_item_id=lost_item_id).first()

    if not lost_item:
        return jsonify({"error": "Lost item not found."}), 404

    if lost_item.claimed:
        return jsonify({"error": "This item has already been claimed."}), 400

    # Mark the item as claimed and record who claimed it
    lost_item.claimed = True
    lost_item.claimed_by = current_user  # You could store the user's ID instead of traveler name

    db.session.commit()

    return jsonify({"message": f"The item '{lost_item.item_name}' has been claimed by {current_user}."}), 200

# Route to delete a lost item
@app.route('/api/lost-items/<lost_item_id>', methods=['DELETE'])
@jwt_required()

def delete_lost_item(lost_item_id):
    item = TravelerLostItem.query.get(lost_item_id) or AgentLostItem.query.get(lost_item_id)

    if not item:
        return jsonify({"error": "Lost item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Lost item has been deleted."}), 200

@app.route('/get_flights', methods=['GET'])
def get_flights():
    airport = request.args.get('airport')
    begin = request.args.get('begin')
    end = request.args.get('end')

    # Replace with actual credentials and API URL
    api_url = f"https://opensky-network.org/api/flights/arrival?airport={airport}&begin={begin}&end={end}"
    auth = ('farah7566', 'Ffaarraahh222004*')  # Use environment variables for security

    response = requests.get(api_url, auth=auth)
    if response.status_code == 200:
        return jsonify(response.json())
    elif response.status_code == 404:
        return jsonify({'error': 'No flights found for the given interval'}), 404
    else:
        return jsonify({'error': 'Failed to fetch flight data'}), response.status_code

@app.route('/get_flightsrep', methods=['GET'])
def get_flightsrep():
    # Retrieve the 'airport' query parameter from the request
    airport = request.args.get('airport')

    # Ensure the 'airport' parameter is provided
    if not airport:
        return jsonify({'error': 'Missing required parameter: airport'}), 400

    # Replace with your flightapi.io API key
    api_key = '6769eea4be731744e7d4c74b'  # This is your public API key (replace with actual key)

    # Construct the URL for the API request (departure mode and IATA airport code)
    api_url = f"https://api.flightapi.io/compschedule/{api_key}?mode=departures&iata={airport}"

    # Make the GET request to the flightapi.io API
    response = requests.get(api_url)

    # Check if the response was successful (status code 200)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch flight data'}), response.status_code


DATABASE = os.path.join(os.getcwd(), 'instance', 'lost_and_found.db')


def query_database(query, args=(), one=False):
    """Query the SQLite database and return results."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows


@app.route('/search', methods=['GET'])
def search_items():
    """Search endpoint to find items by description."""
    description_query = request.args.get('description', '')
    if not description_query:
        return jsonify({"error": "Description query parameter is required"}), 400

    description_query = f"%{description_query}%"

    # Query both tables
    traveler_items = query_database(
        "SELECT item_name, description FROM traveler_lost_items WHERE description LIKE ?",
        [description_query]
    )
    agent_items = query_database(
        "SELECT item_name, description FROM agent_lost_items WHERE description LIKE ?",
        [description_query]
    )

    # Combine results
    results = {
        "traveler_items": [dict(row) for row in traveler_items],
        "agent_items": [dict(row) for row in agent_items]
    }

    return jsonify(results), 200


if __name__ == '__main__':
    # Ensure the application context is pushed before calling db.create_all()
    with app.app_context():
        db.create_all()  # Create both tables for traveler and agent lost items
    app.run(debug=True)
