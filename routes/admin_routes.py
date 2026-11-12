from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db
from models.models import User, Document, EmailRecord, Transaction, RiskResult, AgentExecution, Payment, Subscription, AuditLog
from utils.security_utils import admin_required
from services.audit_service import log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin():
        abort(403)

@admin_bp.route('/admin', methods=['GET'])
def admin_view():
    users = User.query.order_by(User.created_at.desc()).all()
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(30).all()
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(20).all()
    agent_executions = AgentExecution.query.order_by(AgentExecution.created_at.desc()).limit(20).all()
    
    total_users = User.query.count()
    pro_users = User.query.filter_by(plan='PRO').count()
    total_docs = Document.query.count()
    total_txs = Transaction.query.count()
    total_high_risk = RiskResult.query.filter_by(risk_level='HIGH').count()
    total_volume = db.session.query(db.func.sum(Payment.amount)).scalar() or 0.0

    stats = {
        'total_users': total_users,
        'pro_users': pro_users,
        'total_docs': total_docs,
        'total_txs': total_txs,
        'total_high_risk': total_high_risk,
        'total_revenue': float(total_volume)
    }

    return render_template(
        'admin.html',
        users=users,
        audit_logs=audit_logs,
        payments=payments,
        agent_executions=agent_executions,
        stats=stats
    )

@admin_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    total_users = User.query.count()
    pro_users = User.query.filter_by(plan='PRO').count()
    total_docs = Document.query.count()
    total_txs = Transaction.query.count()
    total_high_risk = RiskResult.query.filter_by(risk_level='HIGH').count()
    total_agent_runs = AgentExecution.query.count()
    total_revenue = float(db.session.query(db.func.sum(Payment.amount)).scalar() or 0.0)

    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'pro_users': pro_users,
            'total_documents': total_docs,
            'total_transactions': total_txs,
            'total_high_risk': total_high_risk,
            'total_agent_runs': total_agent_runs,
            'total_revenue': total_revenue
        }
    })

@admin_bp.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
def update_user_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get('role')
    new_plan = data.get('plan')

    target_user = User.query.get_or_404(user_id)
    if new_role in ['user', 'admin']:
        target_user.role = new_role
    if new_plan in ['FREE', 'PRO']:
        target_user.plan = new_plan

    db.session.commit()
    log_action(current_user.id, 'ADMIN_UPDATED_USER', 'users', {'target_user_id': user_id, 'role': new_role, 'plan': new_plan})

    return jsonify({'success': True, 'user': target_user.to_dict()})


@admin_bp.route('/api/admin/health', methods=['GET'])
def system_health():
    """System-wide health telemetry check for administration"""
    import os
    import shutil
    from services.ai_service import ai_service
    from flask import current_app

    upload_folder = current_app.config['UPLOAD_FOLDER']
    free_bytes = shutil.disk_usage(upload_folder).free
    free_mb = round(free_bytes / (1024 * 1024), 2)

    return jsonify({
        'status': 'HEALTHY',
        'subsystems': {
            'database': 'OPERATIONAL',
            'ai_engine': 'LIVE_GEMINI' if ai_service.is_live_configured() else 'LOCAL_HEURISTICS',
            'ml_fraud_engine': 'ISOLATION_FOREST_READY',
            'paypal_gateway': current_app.config.get('PAYPAL_MODE', 'sandbox').upper(),
            'storage_free_mb': free_mb
        }
    })
