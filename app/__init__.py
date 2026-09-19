from flask import Flask
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
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

    # Wrap WSGI app with ProxyFix for production reverse proxies (HTTPS headers)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize repository/DB
    init_db(config_class)

    # Register HTTP blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Initialize SocketIO app with configurable CORS origins
    origins = app.config.get('SOCKETIO_CORS_ORIGINS', '*')
    if isinstance(origins, str) and ',' in origins:
        origins = [o.strip() for o in origins.split(',')]

    socketio.init_app(app, cors_allowed_origins=origins)

    # Register SocketIO event handlers
    register_room_events(socketio)
    register_timer_events(socketio)
    register_presence_events(socketio)

    return app
