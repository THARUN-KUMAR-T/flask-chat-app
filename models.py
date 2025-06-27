from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import string
import random

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    verification_code = db.Column(db.String(10), unique=True, nullable=False)  # New field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_code = db.Column(db.String(8), db.ForeignKey('chat_room.code'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='messages')
    room = db.relationship('ChatRoom', backref='messages')

def generate_room_code():
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=8))
    while ChatRoom.query.filter_by(code=code).first():
        code = ''.join(random.choices(chars, k=8))
    return code

def generate_verification_code():
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=10))
    # Check for uniqueness
    while User.query.filter_by(verification_code=code).first():
        code = ''.join(random.choices(chars, k=10))
    return code
