from flask import Flask
from flask_socketio import SocketIO
from app.config import Config
from app.utilities.db import init_db
from app.routes.main_routes import main_bp
from app.routes.api_routes import api_bp
from app.sockets.room_events import register_room_events
from app.sockets.timer_events import register_timer_events
from app.sockets.presence_events import register_presence_events

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize repository/DB
    init_db(config_class)

    # Register HTTP blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Initialize SocketIO app
    socketio.init_app(app)

    # Register SocketIO event handlers
    register_room_events(socketio)
    register_timer_events(socketio)
    register_presence_events(socketio)

    return app
