from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.models import Document, EmailRecord, Transaction, RiskResult, AgentExecution, AuditLog
from services.ai_service import ai_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def landing_page():
    return render_template('index.html')

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    doc_count = Document.query.filter_by(user_id=current_user.id).count()
    email_count = EmailRecord.query.filter_by(user_id=current_user.id).count()
    tx_count = Transaction.query.filter_by(user_id=current_user.id).count()
    high_risk_tx_count = RiskResult.query.filter_by(user_id=current_user.id, risk_level='HIGH').count()
    medium_risk_tx_count = RiskResult.query.filter_by(user_id=current_user.id, risk_level='MEDIUM').count()
    agent_runs_count = AgentExecution.query.filter_by(user_id=current_user.id).count()

    # Calculate risk distribution
    low_risk_tx_count = max(0, tx_count - (high_risk_tx_count + medium_risk_tx_count))

    # Real user stats
    return jsonify({
        'success': True,
        'stats': {
            'documents_analyzed': doc_count,
            'emails_processed': email_count,
            'transactions_monitored': tx_count,
            'suspicious_transactions': high_risk_tx_count,
            'medium_risk_transactions': medium_risk_tx_count,
            'low_risk_transactions': low_risk_tx_count,
            'ai_agent_activity': agent_runs_count,
            'ai_requests_count': current_user.ai_requests_count,
            'plan': current_user.plan,
            'subscription_status': current_user.subscription_status
        },
        'chart_data': {
            'risk_distribution': {
                'labels': ['Low Risk', 'Medium Risk', 'High Risk'],
                'data': [low_risk_tx_count, medium_risk_tx_count, high_risk_tx_count]
            },
            'module_usage': {
                'labels': ['Documents', 'Emails', 'Security Audits', 'Agent Runs'],
                'data': [doc_count, email_count, tx_count, agent_runs_count]
            }
        },
        'ai_status': {
            'is_live': ai_service.is_live_configured(),
            'model': ai_service.model
        }
    })

@dashboard_bp.route('/api/dashboard/activity', methods=['GET'])
@login_required
def dashboard_activity():
    activities = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.created_at.desc()).limit(15).all()
    return jsonify({
        'success': True,
        'activities': [a.to_dict() for a in activities]
    })
