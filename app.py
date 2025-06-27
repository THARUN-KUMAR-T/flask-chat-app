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
        <title>💬 Chat App</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                max-width: 900px; 
                margin: 0 auto; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container { 
                background: rgba(255,255,255,0.95); 
                padding: 40px; 
                border-radius: 15px; 
                text-align: center;
                color: #333;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .btn { 
                background: #007bff; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 8px; 
                margin: 10px; 
                display: inline-block;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn:hover { background: #0056b3; transform: translateY(-2px); }
            .btn.success { background: #28a745; }
            .btn.success:hover { background: #1e7e34; }
            h1 { color: #333; font-size: 2.5em; margin-bottom: 20px; }
            .features { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 30px 0; 
            }
            .feature { 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 4px solid #007bff; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💬 Welcome to ChatApp</h1>
            <p style="font-size: 1.2em; margin-bottom: 30px;">Connect with people in real-time chat rooms!</p>
            
            <div class="features">
                <div class="feature">
                    <h3>🎓 Students</h3>
                    <p>Join IIT communities</p>
                </div>
                <div class="feature">
                    <h3>👨‍👩‍👧‍👦 Parents</h3>
                    <p>Share parenting tips</p>
                </div>
                <div class="feature">
                    <h3>🏛️ Political</h3>
                    <p>Discuss current affairs</p>
                </div>
                <div class="feature">
                    <h3>🎭 Entertainment</h3>
                    <p>Share jokes & fun</p>
                </div>
            </div>
            
            <div style="margin-top: 40px;">
                <a href="/register" class="btn success">🚀 Get Started</a>
                <a href="/login" class="btn">🔐 Login</a>
            </div>
            
            <p style="margin-top: 30px; color: #666; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                <strong>Demo Account:</strong><br>
                Email: admin@chat.com<br>
                Password: admin123
            </p>
        </div>
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
            return '''
            <div style="font-family:Arial;max-width:500px;margin:50px auto;padding:30px;background:#fff3cd;border:1px solid #ffeaa7;border-radius:10px">
                <h2 style="color:#856404">⚠️ Email already exists!</h2>
                <a href="/register" style="background:#ffc107;color:#212529;padding:10px 20px;text-decoration:none;border-radius:5px">Try Again</a>
                <a href="/login" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;margin-left:10px">Login Instead</a>
            </div>
            '''
        
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
        
        return f'''
        <div style="font-family:Arial;max-width:500px;margin:50px auto;padding:30px;background:#d4edda;border:1px solid #c3e6cb;border-radius:10px">
            <h2 style="color:#155724">✅ Registration Successful!</h2>
            <p style="background:#fff;padding:15px;border-radius:8px;border-left:4px solid #28a745">
                <strong>Your verification code:</strong><br>
                <span style="font-size:1.5em;font-family:monospace;color:#007bff">{verification_code}</span>
            </p>
            <p>Save this code! You can click on usernames in chat to see their verification codes.</p>
            <a href="/login" style="background:#28a745;color:white;padding:12px 25px;text-decoration:none;border-radius:5px">Login Now</a>
        </div>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Chat App</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .form-container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 400px; width: 100%; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
            button { background: #28a745; color: white; padding: 15px; border: none; border-radius: 8px; width: 100%; font-size: 16px; font-weight: bold; cursor: pointer; }
            button:hover { background: #1e7e34; }
            h2 { text-align: center; color: #333; margin-bottom: 30px; }
            .link { text-align: center; margin-top: 20px; }
            .link a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="form-container">
            <h2>🚀 Create Account</h2>
            <form method="POST">
                <input type="text" name="name" placeholder="Full Name" required minlength="2">
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="password" name="password" placeholder="Password (min 6 chars)" required minlength="6">
                <button type="submit">Create Account</button>
            </form>
            <div class="link">
                <a href="/login">Already have an account? Login</a> | <a href="/">Home</a>
            </div>
        </div>
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
            return '''
            <div style="font-family:Arial;max-width:500px;margin:50px auto;padding:30px;background:#f8d7da;border:1px solid #f5c6cb;border-radius:10px">
                <h2 style="color:#721c24">❌ Invalid Credentials!</h2>
                <p>Please check your email and password.</p>
                <a href="/login" style="background:#dc3545;color:white;padding:10px 20px;text-decoration:none;border-radius:5px">Try Again</a>
                <a href="/register" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;margin-left:10px">Register</a>
            </div>
            '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Chat App</title>
        <style>
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .form-container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); max-width: 400px; width: 100%; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
            button { background: #007bff; color: white; padding: 15px; border: none; border-radius: 8px; width: 100%; font-size: 16px; font-weight: bold; cursor: pointer; }
            button:hover { background: #0056b3; }
            h2 { text-align: center; color: #333; margin-bottom: 30px; }
            .demo { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }
            .link { text-align: center; margin-top: 20px; }
            .link a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="form-container">
            <h2>🔐 Welcome Back</h2>
            <form method="POST">
                <input type="email" name="email" placeholder="Email Address" required autofocus>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="demo">
                <strong>🧪 Demo Account:</strong><br>
                Email: admin@chat.com<br>
                Password: admin123
            </div>
            <div class="link">
                <a href="/register">Don't have an account? Register</a> | <a href="/">Home</a>
            </div>
        </div>
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
    # Organize rooms by category
    students_rooms = ChatRoom.query.filter_by(category='students', is_public=True).all()
    parents_rooms = ChatRoom.query.filter_by(category='parents', is_public=True).all()
    political_rooms = ChatRoom.query.filter_by(category='political', is_public=True).all()
    entertainment_rooms = ChatRoom.query.filter_by(category='entertainment', is_public=True).all()
    
    def create_room_cards(rooms, emoji):
        html = ''
        for room in rooms:
            html += f'''
            <a href="/chat/{room.code}" style="display:block;padding:15px;margin:10px 0;background:white;text-decoration:none;border-radius:10px;border-left:5px solid #007bff;box-shadow:0 2px 5px rgba(0,0,0,0.1);transition:all 0.3s">
                <strong style="color:#333">{emoji} {room.name}</strong>
                <div style="color:#666;font-size:0.9em;margin-top:5px">Room Code: {room.code}</div>
            </a>
            '''
        return html
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lobby - Chat App</title>
        <style>
            body {{ font-family: Arial; background: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .category {{ background: #f8f9fa; padding: 20px; border-radius: 15px; border: 1px solid #e9ecef; }}
            .category h3 {{ margin-top: 0; color: #495057; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            .custom-section {{ background: white; padding: 30px; border-radius: 15px; margin-top: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .form-group {{ display: flex; gap: 10px; margin: 15px 0; }}
            .form-group input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; }}
            .btn {{ background: #007bff; color: white; padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }}
            .btn:hover {{ background: #0056b3; }}
            .btn.success {{ background: #28a745; }}
            .btn.success:hover {{ background: #1e7e34; }}
            .user-info {{ background: rgba(255,255,255,0.2); padding: 10px 15px; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1 style="margin:0">💬 Chat Lobby</h1>
                    <p style="margin:5px 0 0 0">Choose a room to start chatting!</p>
                </div>
                <div class="user-info">
                    <strong>Welcome, {current_user.name}!</strong><br>
                    <small>Your Code: {current_user.verification_code}</small><br>
                    <a href="/logout" style="color:#ffcccb;text-decoration:none;font-size:0.9em">Logout →</a>
                </div>
            </div>
            
            <div class="grid">
                <div class="category">
                    <h3>🎓 Students</h3>
                    {create_room_cards(students_rooms, '🎓')}
                </div>
                
                <div class="category">
                    <h3>👨‍👩‍👧‍👦 Parents</h3>
                    {create_room_cards(parents_rooms, '👨‍👩‍👧‍👦')}
                </div>
                
                <div class="category">
                    <h3>🏛️ Political</h3>
                    {create_room_cards(political_rooms, '🏛️')}
                </div>
                
                <div class="category">
                    <h3>🎭 Entertainment</h3>
                    {create_room_cards(entertainment_rooms, '🎭')}
                </div>
            </div>
            
            <div class="custom-section">
                <h2 style="margin-top:0">🚀 Custom Rooms</h2>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:30px">
                    <div>
                        <h4>Create New Room</h4>
                        <form method="POST" action="/create_room">
                            <div class="form-group">
                                <input type="text" name="room_name" placeholder="Enter room name" required maxlength="50">
                                <button type="submit" class="btn success">Create</button>
                            </div>
                        </form>
                    </div>
                    
                    <div>
                        <h4>Join Existing Room</h4>
                        <form method="POST" action="/join_room">
                            <div class="form-group">
                                <input type="text" name="room_code" placeholder="8-digit room code" required maxlength="8" style="text-transform:uppercase">
                                <button type="submit" class="btn">Join</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
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
        return '''
        <div style="font-family:Arial;max-width:500px;margin:50px auto;padding:30px;background:#f8d7da;border:1px solid #f5c6cb;border-radius:10px">
            <h2 style="color:#721c24">❌ Room Not Found!</h2>
            <p>The room code you entered doesn't exist.</p>
            <a href="/lobby" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px">← Back to Lobby</a>
        </div>
        '''

@app.route('/chat/<room_code>')
@login_required
def chat(room_code):
    room = ChatRoom.query.filter_by(code=room_code).first()
    if not room:
        return redirect(url_for('lobby'))
    
    messages = Message.query.filter_by(room_code=room_code).order_by(Message.timestamp.asc()).all()
    
    message_html = ''
    for msg in messages:
        message_html += f'''
        <div class="message">
            <small style="color:#666">{msg.timestamp.strftime("%H:%M")}</small>
            <strong class="username" onclick="toggleCode(this)" data-code="{msg.user.verification_code}">{msg.user.name}</strong>
            <span class="verification-code" style="display:none;color:#007bff;font-size:0.8em"> [{msg.user.verification_code}]</span>:
            <span>{msg.content}</span>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{room.name} - Chat</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body {{ font-family: Arial; margin: 0; background: #f8f9fa; }}
            .chat-container {{ max-width: 800px; margin: 20px auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .chat-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .messages {{ height: 400px; overflow-y: auto; padding: 20px; background: #fafafa; }}
            .message {{ margin: 10px 0; padding: 10px; background: white; border-radius: 8px; border-left: 4px solid #007bff; }}
            .username {{ cursor: pointer; color: #007bff; font-weight: bold; }}
            .username:hover {{ text-decoration: underline; }}
            .chat-input {{ padding: 20px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px; }}
            .chat-input input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
            .chat-input button {{ background: #007bff; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: bold; }}
            .chat-input button:hover {{ background: #0056b3; }}
            .status-message {{ font-style: italic; color: #666; background: #f8f9fa; border-left: 4px solid #6c757d; }}
            .badge {{ background: #6c757d; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.9em; margin: 0 5px; }}
            .badge.user {{ background: #17a2b8; }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <div>
                    <h2 style="margin:0">💬 {room.name}</h2>
                    <small>Click on usernames to see verification codes</small>
                </div>
                <div>
                    <span class="badge">{room_code}</span>
                    <span class="badge user">Your: {current_user.verification_code}</span>
                    <a href="/lobby" style="color:#ffcccb;text-decoration:none;margin-left:15px">← Lobby</a>
                </div>
            </div>
            
            <div class="messages" id="messages">
                {message_html}
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Type your message..." maxlength="500" autofocus>
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <script>
            const socket = io();
            const roomCode = '{room_code}';
            const messagesDiv = document.getElementById('messages');
            
            // Join room
            socket.emit('join', {{room: roomCode}});
            
            // Toggle verification code display
            function toggleCode(element) {{
                const codeSpan = element.nextElementSibling;
                codeSpan.style.display = codeSpan.style.display === 'none' ? 'inline' : 'none';
            }}
            
            // Send message
            function sendMessage() {{
                const input = document.getElementById('messageInput');
                if (input.value.trim()) {{
                    socket.emit('message', {{room: roomCode, message: input.value}});
                    input.value = '';
                }}
            }}
            
            // Enter key to send
            document.getElementById('messageInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') sendMessage();
            }});
            
            // Handle incoming messages
            socket.on('message', function(data) {{
                const div = document.createElement('div');
                div.className = 'message';
                div.innerHTML = `
                    <small style="color:#666">${{data.timestamp}}</small>
                    <strong class="username" onclick="toggleCode(this)" data-code="${{data.verification_code}}">${{data.username}}</strong>
                    <span class="verification-code" style="display:none;color:#007bff;font-size:0.8em"> [${{data.verification_code}}]</span>:
                    <span>${{data.message}}</span>
                `;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }});
            
            // Handle status messages
            socket.on('status', function(data) {{
                const div = document.createElement('div');
                div.className = 'message status-message';
                div.innerHTML = `<em>${{data.msg}}</em> <small>${{data.timestamp}}</small>`;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }});
            
            // Auto-scroll to bottom
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        </script>
    </body>
    </html>
    '''

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
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

@socketio.on('leave')
def on_leave(data):
    if current_user.is_authenticated:
        room_code = data['room']
        leave_room(room_code)
        emit('status', {
            'msg': f"{current_user.name} left the room",
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room_code)

@socketio.on('message')
def handle_message(data):
    if current_user.is_authenticated:
        room_code = data['room']
        content = data['message']
        
        # Save to database
        message = Message(
            content=content,
            user_id=current_user.id,
            room_code=room_code
        )
        db.session.add(message)
        db.session.commit()
        
        # Broadcast to room
        emit('message', {
            'message': content,
            'username': current_user.name,
            'verification_code': current_user.verification_code,
            'timestamp': datetime.now().strftime('%H:%M')
        }, room=room_code)

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist
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
