from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import string
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chat_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    verification_code = db.Column(db.String(10), unique=True, nullable=False)
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_room_code():
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=8))
    while ChatRoom.query.filter_by(code=code).first():
        code = ''.join(random.choices(chars, k=8))
    return code

def generate_verification_code():
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=10))
    while User.query.filter_by(verification_code=code).first():
        code = ''.join(random.choices(chars, k=10))
    return code

# Public room categories
PUBLIC_ROOMS = {
    'students': ['IIT Bombay', 'IIT KGP', 'IIT Madras', 'IIT Hyderabad'],
    'parents': ['Parenting Tips', 'Child Education'],
    'political': ['BJP', 'Congress', 'All India Trinamool Congress'],
    'entertainment': ['Funny Jokes']
}

def create_public_rooms():
    for category, rooms in PUBLIC_ROOMS.items():
        for room_name in rooms:
            existing_room = ChatRoom.query.filter_by(name=room_name, category=category).first()
            if not existing_room:
                room = ChatRoom(
                    code=generate_room_code(),
                    name=room_name,
                    category=category,
                    is_public=True,
                    created_by=1
                )
                db.session.add(room)
    db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
            return redirect(url_for('register'))
        
        verification_code = generate_verification_code()
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            name=name, 
            email=email, 
            password=hashed_password,
            verification_code=verification_code
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Registration successful! Your verification code is: {verification_code}')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('lobby'))
        else:
            flash('Invalid credentials!')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/lobby')
@login_required
def lobby():
    organized_rooms = {
        category: ChatRoom.query.filter_by(category=category, is_public=True).all()
        for category in PUBLIC_ROOMS.keys()
    }
    return render_template('lobby.html', rooms=organized_rooms)

@app.route('/create_room', methods=['POST'])
@login_required
def create_room():
    room_name = request.form['room_name']
    room_code = generate_room_code()
    
    new_room = ChatRoom(
        code=room_code,
        name=room_name,
        category='custom',
        is_public=False,
        created_by=current_user.id
    )
    db.session.add(new_room)
    db.session.commit()
    
    return redirect(url_for('chat', room_code=room_code))

@app.route('/join_room', methods=['POST'])
@login_required
def join_room_route():
    room_code = request.form['room_code'].upper()
    room = ChatRoom.query.filter_by(code=room_code).first()
    
    if room:
        return redirect(url_for('chat', room_code=room_code))
    else:
        flash('Room not found!')
        return redirect(url_for('lobby'))

@app.route('/chat/<room_code>')
@login_required
def chat(room_code):
    room = ChatRoom.query.filter_by(code=room_code).first()
    if not room:
        flash('Room not found!')
        return redirect(url_for('lobby'))
    
    messages = Message.query.filter_by(room_code=room_code)\
                          .order_by(Message.timestamp.asc()).all()
    
    return render_template('chat.html', room=room, messages=messages)

# Socket.IO Events
@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        print(f'User {current_user.name} connected')
    else:
        return False

@socketio.on('join')
def on_join(data):
    room_code = data['room']
    join_room(room_code)
    emit('status', {
        'msg': f"{current_user.name} has joined the room.",
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room_code)

@socketio.on('leave')
def on_leave(data):
    room_code = data['room']
    leave_room(room_code)
    emit('status', {
        'msg': f"{current_user.name} has left the room.",
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room_code)

@socketio.on('message')
def handle_message(data):
    room_code = data['room']
    content = data['message']
    
    message = Message(
        content=content,
        user_id=current_user.id,
        room_code=room_code
    )
    db.session.add(message)
    db.session.commit()
    
    emit('message', {
        'message': content,
        'username': current_user.name,
        'verification_code': current_user.verification_code,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room_code)

# Initialize database and create tables
with app.app_context():
    db.create_all()
    # Create admin user
    admin = User.query.filter_by(id=1).first()
    if not admin:
        admin_user = User(
            name='Admin',
            email='admin@chat.com',
            password=generate_password_hash('admin123'),
            verification_code='ADMIN12345'
        )
        db.session.add(admin_user)
        db.session.commit()
    
    create_public_rooms()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
