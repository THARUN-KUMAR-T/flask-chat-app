Flask Chat App
A real-time chat application built with Flask, Flask-SocketIO and Bootstrap.
It lets multiple users join named rooms and exchange messages instantly through WebSockets.

Features
Real-time messaging with Flask-SocketIO (WebSocket fallback to long-polling)

Create or join chat rooms by name

Display online users in each room

Typing indicator

Responsive interface styled with Bootstrap 5

Docker-ready & easily deployable to Heroku, Render, Fly.io, etc.

Demo
bash
# Clone and run locally
git clone https://github.com/THARUN-KUMAR-T/flask-chat-app.git
cd flask-chat-app
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000 in two browser tabs and start chatting
Project Structure
Path	Purpose
app.py	Flask application factory & SocketIO events
templates/	Jinja2 HTML templates (index.html, chat.html)
static/js/	Front-end SocketIO logic (chat.js)
static/css/	Custom styles
requirements.txt	Python dependencies
Dockerfile	Container build instructions
Procfile	Heroku/Render launch command
Installation
Prerequisites
Python 3.9+

Node.js (only if you plan to bundle front-end assets yourself)

(Optional) Docker

Steps
bash
# 1. Clone repository
git clone https://github.com/THARUN-KUMAR-T/flask-chat-app.git
cd flask-chat-app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python app.py
The server starts at http://127.0.0.1:5000.

Environment Variables
Variable	Default	Description
FLASK_ENV	development	Set to production in prod
SECRET_KEY	supersecretkey	Flask session encryption
PORT	5000	Port to bind (useful for Heroku)
Create a .env file or export variables before running:

bash
export SECRET_KEY="change_this_value"
export FLASK_ENV=production
Running with Docker
bash
docker build -t flask-chat .
docker run -d -p 5000:5000 --name chatapp flask-chat
Deployment Guide
Heroku / Render / Fly.io
Set buildpacks: heroku/python, optionally heroku/nodejs

Add environment variables (SECRET_KEY, PORT)

Deploy; the Procfile (web: gunicorn app:app) will start Gunicorn with eventlet.

Nginx + Gunicorn
bash
pip install gunicorn eventlet
gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:8000
Then proxy location /socket.io and / through Nginx.

Contributing
Fork the repo & create your branch (git checkout -b feature/foo)

Commit your changes (git commit -am 'Add foo')

Push to the branch (git push origin feature/foo)

Open a Pull Request

License
This project is released under the MIT License — feel free to use and modify it.
