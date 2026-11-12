import json
from flask import request
from models import db
from models.models import AuditLog

def log_action(user_id, action, resource=None, details=None):
    """Safely log audit trail actions"""
    try:
        ip_addr = request.remote_addr if request else '127.0.0.1'
    except Exception:
        ip_addr = '127.0.0.1'
        
    try:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_addr,
            details_json=details_str
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit trail: {e}")
        return None
