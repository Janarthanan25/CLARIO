from models import db
from models.models import Notification

def send_notification(user_id, title, message, category='system', link=None):
    """Create an in-app notification for a user"""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        return None

def get_user_notifications(user_id, limit=20, unread_only=False):
    """Retrieve user notifications"""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

def mark_notification_as_read(notification_id, user_id):
    """Mark a single notification as read"""
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_as_read(user_id):
    """Mark all user notifications as read"""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return True
