from sqlalchemy import Column, String
from db import db

class TravelerLostItem(db.Model):
    __tablename__ = 'traveler_lost_items'

    lost_item_id = Column(String, primary_key=True, nullable=False)
    item_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location_lost = Column(String, nullable=False)  # Required for traveler
    contact_info = Column(String, nullable=False)   # Required for traveler
    traveler_name = Column(String, nullable=False) # Required for traveler
    claimed = db.Column(db.Boolean, default=False)
    claimed_by = db.Column(db.String(255), nullable=True)  # Who claimed it
    status = Column(String, nullable=False, default='Lost')  # Default status for traveler
    image_path = Column(String, nullable=True)  # New field for image path

class AgentLostItem(db.Model):
    __tablename__ = 'agent_lost_items'

    lost_item_id = Column(String, primary_key=True, nullable=False)
    item_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location_lost = Column(String, nullable=True)  # Optional for agent
    contact_info = Column(String, nullable=True)   # Optional for agent
    status = Column(String, nullable=False, default='Lost')  # Default status for agent
    image_path = Column(String, nullable=True)  # New field for image path


# User model for storing registered users
class User(db.Model):
    __tablename__ = 'users'

    username = Column(String, primary_key=True, nullable=False)
    password = Column(String, nullable=False)
    role = db.Column(db.String, nullable=False)  # 'traveler' or 'agent'


