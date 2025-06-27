from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import string
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions - THREADING MODE ONLY
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True)

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
    room_code = db.Column(db.String(8), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='messages')

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

# Public rooms
PUBLIC_ROOMS = {
    'students': ['IIT Bombay', 'IIT KGP', 'IIT Madras', 'IIT Hyderabad'],
    'parents': ['Parenting Tips', 'Child Education'],
    'political': ['BJP', 'Congress', 'All India Trinamool Congress'],
    'entertainment': ['Funny Jokes']
}

def create_public_rooms():
    try:
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
    except Exception as e:
        db.session.rollback()
        print(f"Error creating rooms: {e}")

# Routes
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🚀 Chat App is Live!</h1>
        <p>Welcome to the real-time chat application!</p>
        <a href="/register" class="btn">Register</a>
        <a href="/login" class="btn">Login</a>
        <p><strong>Demo credentials:</strong><br>Email: admin@chat.com<br>Password: admin123</p>
    </body>
    </html>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            return f'<h2>Error: Email already exists!</h2><a href="/register">Try again</a>'
        
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
        
        return f'<h2>Registration successful!</h2><p>Your verification code: <strong>{verification_code}</strong></p><a href="/login">Login now</a>'
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Register</title>
    <style>body{font-family:Arial;max-width:400px;margin:50px auto;padding:20px}
    input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
    button{background:#28a745;color:white;padding:12px 20px;border:none;border-radius:5px;width:100%}</style>
    </head>
    <body>
        <h2>Register</h2>
        <form method="POST">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <p><a href="/login">Already have an account? Login</a></p>
    </body>
    </html>
    '''

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
            return '<h2>Invalid credentials!</h2><a href="/login">Try again</a>'
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Login</title>
    <style>body{font-family:Arial;max-width:400px;margin:50px auto;padding:20px}
    input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
    button{background:#007bff;color:white;padding:12px 20px;border:none;border-radius:5px;width:100%}</style>
    </head>
    <body>
        <h2>Login</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p><strong>Demo:</strong> admin@chat.com / admin123</p>
        <p><a href="/register">Don't have an account? Register</a></p>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/lobby')
@login_required
def lobby():
    rooms = ChatRoom.query.filter_by(is_public=True).all()
    room_html = ''
    for room in rooms:
        room_html += f'<a href="/chat/{room.code}" style="display:block;padding:10px;margin:5px;background:#f8f9fa;text-decoration:none;border-radius:5px">{room.name} ({room.code})</a>'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Lobby</title>
    <style>body{{font-family:Arial;max-width:800px;margin:20px auto;padding:20px}}</style>
    </head>
    <body>
        <h2>Welcome, {current_user.name}! (Code: {current_user.verification_code})</h2>
        <a href="/logout" style="float:right;color:red">Logout</a>
        <h3>Public Rooms:</h3>
        {room_html}
        <h3>Create Custom Room:</h3>
        <form method="POST" action="/create_room" style="margin:20px 0">
            <input type="text" name="room_name" placeholder="Room name" required style="padding:10px;margin-right:10px">
            <button type="submit" style="padding:10px 20px;background:#28a745;color:white;border:none;border-radius:5px">Create</button>
        </form>
        <h3>Join Custom Room:</h3>
        <form method="POST" action="/join_room">
            <input type="text" name="room_code" placeholder="8-digit room code" maxlength="8" required style="padding:10px;margin-right:10px">
            <button type="submit" style="padding:10px 20px;background:#007bff;color:white;border:none;border-radius:5px">Join</button>
        </form>
    </body>
    </html>
    '''

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
        return '<h2>Room not found!</h2><a href="/lobby">Back to Lobby</a>'

@app.route('/chat/<room_code>')
@login_required
def chat(room_code):
    room = ChatRoom.query.filter_by(code=room_code).first()
    if not room:
        return '<h2>Room not found!</h2><a href="/lobby">Back to Lobby</a>'
    
    messages = Message.query.filter_by(room_code=room_code).order_by(Message.timestamp.asc()).all()
    
    message_html = ''
    for msg in messages:
        message_html += f'<div style="margin:5px 0;padding:5px;background:#f8f9fa;border-radius:3px"><small>{msg.timestamp.strftime("%H:%M")}</small> <strong onclick="this.nextSibling.style.display=this.nextSibling.style.display==\'none\'?\'inline\':\'none\'" style="cursor:pointer">{msg.user.name}</strong><span style="display:none;color:gray"> [{msg.user.verification_code}]</span>: {msg.content}</div>'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{room.name}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body style="font-family:Arial;max-width:800px;margin:20px auto;padding:20px">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <h2>{room.name}</h2>
            <div>
                <span style="background:#6c757d;color:white;padding:5px 10px;border-radius:15px">{room.code}</span>
                <span style="background:#17a2b8;color:white;padding:5px 10px;border-radius:15px;margin-left:10px">Your: {current_user.verification_code}</span>
                <a href="/lobby" style="margin-left:15px;color:#dc3545">← Lobby</a>
            </div>
        </div>
        
        <div id="messages" style="height:400px;overflow-y:auto;border:1px solid #ddd;padding:15px;background:white;margin:20px 0">
            {message_html}
        </div>
        
        <form id="messageForm" style="display:flex">
            <input type="text" id="messageInput" placeholder="Type your message..." required style="flex:1;padding:10px;border:1px solid #ddd;border-radius:5px 0 0 5px">
            <button type="submit" style="padding:10px 20px;background:#007bff;color:white;border:none;border-radius:0 5px 5px 0">Send</button>
        </form>
        
        <script>
            const socket = io();
            const roomCode = '{room_code}';
            const messagesDiv = document.getElementById('messages');
            
            socket.emit('join', {{room: roomCode}});
            
            document.getElementById('messageForm').onsubmit = function(e) {{
                e.preventDefault();
                const input = document.getElementById('messageInput');
                if (input.value.trim()) {{
                    socket.emit('message', {{room: roomCode, message: input.value}});
                    input.value = '';
                }}
            }};
            
            socket.on('message', function(data) {{
                const div = document.createElement('div');
                div.style.cssText = 'margin:5px 0;padding:5px;background:#f8f9fa;border-radius:3px';
                div.innerHTML = `<small>${{data.timestamp}}</small> <strong onclick="this.nextSibling.style.display=this.nextSibling.style.display=='none'?'inline':'none'" style="cursor:pointer">${{data.username}}</strong><span style="display:none;color:gray"> [${{data.verification_code}}]</span>: ${{data.message}}`;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }});
            
            socket.on('status', function(data) {{
                const div = document.createElement('div');
                div.style.cssText = 'color:gray;font-style:italic;margin:5px 0';
                div.innerHTML = `<em>${{data.msg}}</em> <small>${{data.timestamp}}</small>`;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }});
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        </script>
    </body>
    </html>
    '''

# Socket.IO Events
@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        print(f'User {current_user.name} connected')
        return True
    return False

@socketio.on('join')
def on_join(data):
    if current_user.is_authenticated:
        room_code = data['room']
        join_room(room_code)
        emit('status', {
            'msg': f"{current_user.name} joined the room",
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room_code)

@socketio.on('message')
def handle_message(data):
    if current_user.is_authenticated:
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

# Initialize database
with app.app_context():
    db.create_all()
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
