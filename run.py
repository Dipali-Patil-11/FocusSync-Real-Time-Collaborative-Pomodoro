import os
from app import create_app, socketio
from app.utilities.logger import logger

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    logger.info(f"Starting FocusSync Realtime Server on http://0.0.0.0:{port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
