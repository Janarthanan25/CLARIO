from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from services.notification_service import get_user_notifications, mark_notification_as_read, mark_all_notifications_as_read
from models.models import Notification

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/api/notifications', methods=['GET'])
@login_required
def list_notifications():
    notifications = get_user_notifications(current_user.id, limit=30)
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    })

@notification_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    success = mark_notification_as_read(notif_id, current_user.id)
    return jsonify({'success': success})

@notification_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    success = mark_all_notifications_as_read(current_user.id)
    return jsonify({'success': success})
