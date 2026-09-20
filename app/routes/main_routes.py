from flask import Blueprint, render_template, redirect, url_for, request, session
from app.utilities.db import get_repository
from app.services.session_service import SessionService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/history')
def history():
    return render_template('history.html')

@main_bp.route('/session/<session_code>')
def session_page(session_code):
    repo = get_repository()
    session_service = SessionService(repo)
    state = session_service.get_session_state(session_code.upper())
    
    if not state:
        # Redirect to landing page with error flag
        return redirect(url_for('main.index', error='session_not_found', code=session_code))

    return render_template('session.html', session_code=session_code.upper())

