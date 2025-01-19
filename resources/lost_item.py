import sqlite3

from flask import request, jsonify
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from flask.views import MethodView
from models import TravelerLostItem, AgentLostItem
from db import db
import uuid
import os

blp = Blueprint('LostItem', __name__, description="Operations related to lost items")

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blp.route('/api/lost-items/report-by-traveler', methods=['POST'])
class ReportLostItemByTraveler(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        item_name = data.get('item_name')
        description = data.get('description')
        location_lost = data.get('location_lost')
        contact_info = data.get('contact_info')
        traveler_name = data.get('traveler_name')
        claimed = data.get('claimed', False)
        claimed_by = data.get('claimed_by', 'no one')

        if not item_name or not description or not location_lost or not contact_info or not traveler_name:
            return jsonify({"error": "Item name, description, location, contact info, and traveler name are required."}), 400

        image = request.files.get('image')
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)

        new_item = TravelerLostItem(
            lost_item_id=str(uuid.uuid4()),
            item_name=item_name,
            description=description,
            location_lost=location_lost,
            contact_info=contact_info,
            traveler_name=traveler_name,
            claimed=claimed,
            claimed_by=claimed_by,
            status='Lost',
            image_path=image_path
        )

        db.session.add(new_item)
        db.session.commit()

        return jsonify({"message": "Lost item reported by traveler", "lost_item_id": new_item.lost_item_id}), 201

@blp.route('/api/lost-items/report-by-agent', methods=['POST'])
class ReportLostItemByAgent(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        item_name = data.get('item_name')
        description = data.get('description')
        status = data.get('status')
        image_path = data.get('image_path')

        if not item_name or not description or not status:
            return jsonify({"error": "Item name, description, and status are required."}), 400

        location_lost = data.get('location_lost', "Not Provided")
        contact_info = data.get('contact_info', "Not Provided")

        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
        else:
            image_path = None

        new_item = AgentLostItem(
            lost_item_id=str(uuid.uuid4()),
            item_name=item_name,
            description=description,
            location_lost=location_lost,
            contact_info=contact_info,
            status=status,
            image_path=image_path
        )

        db.session.add(new_item)
        db.session.commit()

        return jsonify({"message": "Lost item reported by airport agent", "lost_item_id": new_item.lost_item_id}), 201

@blp.route('/api/lost-items/<string:lost_item_id>', methods=['GET'])
class GetLostItem(MethodView):
    def get(self, lost_item_id):
        item = TravelerLostItem.query.filter_by(lost_item_id=lost_item_id).first()
        if not item:
            item = AgentLostItem.query.filter_by(lost_item_id=lost_item_id).first()

        if item:
            return jsonify({
                "lost_item_id": item.lost_item_id,
                "item_name": item.item_name,
                "description": item.description,
                "location_lost": item.location_lost,
                "contact_info": item.contact_info,
                "status": item.status,
                "image_url": item.image_path if item.image_path else None
            })
        return jsonify({"message": "Item not found"}), 404

@blp.route('/api/lost-items', methods=['GET'])
class ListLostItems(MethodView):
    def get(self):
        traveler_items = TravelerLostItem.query.all()
        agent_items = AgentLostItem.query.all()

        items_list = []

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

@blp.route('/api/lost-items/<lost_item_id>', methods=['PUT', 'PATCH'])
class UpdateLostItemStatus(MethodView):
    @jwt_required()
    def put(self, lost_item_id):
        item = TravelerLostItem.query.get(lost_item_id) or AgentLostItem.query.get(lost_item_id)

        if not item:
            return jsonify({"error": "Lost item not found"}), 404

        status = request.json.get('status')
        if not status:
            return jsonify({"error": "Status is required"}), 400

        item.status = status
        db.session.commit()

        return jsonify({"message": f"The status of the lost item has been updated to '{status}'."}), 200

    @jwt_required()
    def patch(self, lost_item_id):
        return self.put(lost_item_id)

@blp.route('/api/lost-items/claim/<lost_item_id>', methods=['POST'])
class ClaimLostItem(MethodView):
    @jwt_required()
    def post(self, lost_item_id):
        current_user = get_jwt_identity()
        lost_item = TravelerLostItem.query.filter_by(lost_item_id=lost_item_id).first()

        if not lost_item:
            return jsonify({"error": "Lost item not found."}), 404

        if lost_item.claimed:
            return jsonify({"error": "This item has already been claimed."}), 400

        lost_item.claimed = True
        lost_item.claimed_by = current_user

        db.session.commit()

        return jsonify({"message": f"The item '{lost_item.item_name}' has been claimed by {current_user}."}), 200

@blp.route('/api/lost-items/<lost_item_id>', methods=['DELETE'])
class DeleteLostItem(MethodView):
    @jwt_required()
    def delete(self, lost_item_id):
        item = TravelerLostItem.query.get(lost_item_id) or AgentLostItem.query.get(lost_item_id)

        if not item:
            return jsonify({"error": "Lost item not found"}), 404

        db.session.delete(item)
        db.session.commit()

        return jsonify({"message": "Lost item has been deleted."}), 200

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


@blp.route('/search', methods=['GET'])
class SearchItems(MethodView):
    def get(self):
        description_query = request.args.get('description', '')
        if not description_query:
            return jsonify({"error": "Description query parameter is required"}), 400

        description_query = f"%{description_query}%"

        traveler_items = query_database(
            "SELECT item_name, description FROM traveler_lost_items WHERE description LIKE ?",
            [description_query]
        )
        agent_items = query_database(
            "SELECT item_name, description FROM agent_lost_items WHERE description LIKE ?",
            [description_query]
        )

        results = {
            "traveler_items": [dict(row) for row in traveler_items],
            "agent_items": [dict(row) for row in agent_items]
        }

        return jsonify(results), 200

