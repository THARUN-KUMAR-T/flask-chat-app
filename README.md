# Flask Chat App

A lightweight, real-time chat application built using Flask and Flask-SocketIO. This application allows users to join chat rooms, send messages, and see updates instantly without reloading the page.

## Features

* **Real-Time Messaging:** Instant message delivery powered by WebSockets.
* **Multiple Chat Rooms:** Users can join existing rooms or create new ones by name.
* **User Nicknames:** Choose a nickname upon joining for easy identification.
* **Responsive UI:** Clean and minimalistic interface that adapts to different screen sizes.

## Demo

![Chat App Screenshot](docs/images/chat_screenshot.png)

> Note: You can run the app locally and navigate to `http://localhost:5000` to try it out.

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/THARUN-KUMAR-T/flask-chat-app.git
   cd flask-chat-app
   ```

2. **Create a virtual environment** (optional but recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows, use `venv\\Scripts\\activate`
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

If you need to customize the server or SocketIO settings, you can modify the following files:

* **`main.py`**: Entry point of the application.
* **`chat_room.py`**: Contains the SocketIO event handlers and room logic.

No additional configuration is required for a local development environment.

## Usage

1. **Start the server**

   ```bash
   python main.py
   ```

2. **Open your browser** and go to:

   ```
   http://localhost:5000
   ```

3. **Enter a nickname and room name** to join or create a chat room.

4. **Start chatting!** Messages will appear in real time.

## Project Structure

```
flask-chat-app/
├── static/
│   ├── styles/        # CSS stylesheets
│   └── scripts/       # JavaScript client-side logic
├── templates/
│   └── index.html     # Main HTML template
├── chat_room.py       # SocketIO event handlers
├── main.py            # Flask application entry point
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Contributing

Contributions are welcome! Feel free to:

* Submit bug reports or feature requests via GitHub Issues.
* Fork the repository and submit pull requests.

Please follow the [Python PEP8 style guide](https://www.python.org/dev/peps/pep-0008/) when contributing.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

* [Flask](https://flask.palletsprojects.com/) for the web framework.
* [Flask-SocketIO](https://flask-socketio.readthedocs.io/) for real-time support.
* Inspired by various Flask tutorial projects.
