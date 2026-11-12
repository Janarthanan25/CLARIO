from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db
from models.models import User
from services.audit_service import log_action
from services.ai_service import ai_service

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
@login_required
def settings_view():
    gemini_key = current_app.config.get('GEMINI_API_KEY', '')
    masked_key = f"{gemini_key[:4]}...{gemini_key[-4:]}" if (gemini_key and len(gemini_key) > 8) else ('Configured' if gemini_key else 'Not Configured')
    return render_template('settings.html', masked_key=masked_key, is_live=ai_service.is_live_configured())

@settings_bp.route('/api/settings/profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    full_name = data.get('full_name', '').strip()
    username = data.get('username', '').strip()

    if username and username != current_user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already taken.'}), 400
        current_user.username = username

    if full_name:
        current_user.full_name = full_name

    db.session.commit()
    log_action(current_user.id, 'PROFILE_UPDATED', 'settings')
    return jsonify({'success': True, 'message': 'Profile updated successfully!', 'user': current_user.to_dict()})

@settings_bp.route('/api/settings/password', methods=['POST'])
@login_required
def update_password():
    data = request.get_json(silent=True) or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if not current_user.check_password(current_pw):
        return jsonify({'success': False, 'error': 'Current password is incorrect.'}), 400

    if len(new_pw) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters.'}), 400

    current_user.set_password(new_pw)
    db.session.commit()
    log_action(current_user.id, 'PASSWORD_CHANGED', 'settings')
    return jsonify({'success': True, 'message': 'Password updated successfully!'})

@settings_bp.route('/api/settings/api-key', methods=['POST'])
@login_required
def update_api_key():
    data = request.get_json(silent=True) or {}
    api_key = data.get('gemini_api_key', '').strip()

    # Update in application config for the session
    current_app.config['GEMINI_API_KEY'] = api_key
    ai_service.api_key = api_key

    log_action(current_user.id, 'GEMINI_API_KEY_CONFIGURED', 'settings')
    return jsonify({
        'success': True,
        'message': 'Gemini API key configured successfully! Live AI orchestration enabled.',
        'is_live': bool(api_key and len(api_key) > 10)
    })
