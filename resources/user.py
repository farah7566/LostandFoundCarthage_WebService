from flask import request, jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import create_access_token, create_refresh_token
from flask.views import MethodView  # Import MethodView
from models import User
from db import db

blp = Blueprint('User', __name__, description="User operations such as registration and login")

@blp.route('/api/register', methods=['POST'])
class Register(MethodView):  # Inherit from MethodView
    def post(self):
        data = request.json
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"message": "Username already exists"}), 400

        # Check if role is valid
        if role not in ['traveler', 'agent']:
            return jsonify({"message": "Invalid role. Must be 'traveler' or 'agent'."}), 400

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

@blp.route('/api/login', methods=['POST'])
class Login(MethodView):  # Inherit from MethodView
    def post(self):
        data = request.json
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        if user.password != password:
            return jsonify({"message": "Invalid credentials"}), 401

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': user.role
        }), 200