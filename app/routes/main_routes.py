from flask import Blueprint, render_template, redirect, url_for, request
from app.utilities.db import get_repository
from app.services.room_service import RoomService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/room/<room_code>')
def room_page(room_code):
    repo = get_repository()
    room_service = RoomService(repo)
    state = room_service.get_room_state(room_code.upper())
    
    if not state:
        # Redirect to landing page with error flag
        return redirect(url_for('main.index', error='room_not_found', code=room_code))

    return render_template('room.html', room_code=room_code.upper())
