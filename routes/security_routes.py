import json
import pandas as pd
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.models import Transaction, RiskResult
from modules.security.analyzer import SecurityAnalyzer
from services.audit_service import log_action
from services.notification_service import send_notification
from utils.sample_data import get_sample_transactions

security_bp = Blueprint('security', __name__)
analyzer = SecurityAnalyzer()

@security_bp.route('/security', methods=['GET'])
@login_required
def security_view():
    recent_txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(25).all()
    high_risk_alerts = RiskResult.query.filter_by(user_id=current_user.id, risk_level='HIGH').order_by(RiskResult.created_at.desc()).limit(10).all()
    return render_template('security.html', transactions=recent_txs, alerts=high_risk_alerts)


@security_bp.route('/api/security/analyze', methods=['POST'])
@login_required
def analyze_transactions():
    tx_list = []
    batch_id = f"BATCH-{int(datetime.now().timestamp())}"

    # Check if CSV file uploaded
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            try:
                df = pd.read_csv(file)
                tx_list = df.fillna('').to_dict(orient='records')
            except Exception as e:
                return jsonify({'success': False, 'error': f"Failed to parse CSV file: {str(e)}"}), 400
    else:
        # Check if JSON payload passed
        data = request.get_json(silent=True) or {}
        tx_list = data.get('transactions', [])
        if data.get('batch_id'):
            batch_id = data.get('batch_id')

    if not tx_list:
        return jsonify({'success': False, 'error': 'No transaction data provided. Upload a CSV or provide records.'}), 400

    try:
        analysis_result = analyzer.analyze_transactions(tx_list)
        
        # Persist transactions & risk evaluations to database
        saved_items = []
        for item in analysis_result['transactions']:
            tx = Transaction(
                user_id=current_user.id,
                batch_id=batch_id,
                external_tx_id=item['external_tx_id'],
                amount=item['amount'],
                currency=item.get('currency', 'USD'),
                timestamp=pd_parse_date(item['timestamp']),
                sender=item['sender'],
                recipient=item['recipient'],
                category=item['category'],
                description=item.get('description', '')
            )
            db.session.add(tx)
            db.session.flush()

            risk = RiskResult(
                transaction_id=tx.id,
                user_id=current_user.id,
                risk_score=item['risk_score'],
                risk_level=item['risk_level'],
                is_anomaly=item['is_anomaly'],
                is_duplicate=item['is_duplicate'],
                detected_indicators=json.dumps(item['detected_indicators']),
                explanation=item['explanation'],
                recommended_action=item['recommended_action'],
                review_status='pending'
            )
            db.session.add(risk)
            saved_items.append(tx)

        db.session.commit()

        # Audit & Notification
        high_risk_count = analysis_result['metrics']['high_risk_count']
        if high_risk_count > 0:
            send_notification(
                user_id=current_user.id,
                title="Security Alert Flagged ⚠️",
                message=f"Isolation Forest & Rule Engine flagged {high_risk_count} high-risk transaction(s) requiring verification.",
                category="security",
                link="/security"
            )
        log_action(current_user.id, 'SECURITY_ANALYSIS_EXECUTED', 'security', {'batch_id': batch_id, 'count': len(tx_list)})

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'metrics': analysis_result['metrics'],
            'transactions': analysis_result['transactions']
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f"Security audit failed: {str(e)}"}), 500


@security_bp.route('/api/security/load-demo', methods=['POST'])
@login_required
def load_demo_transactions():
    """Loads realistic sample transactions clearly labeled as demonstration data"""
    sample_txs = get_sample_transactions()
    batch_id = f"DEMO-BATCH-{int(datetime.now().timestamp())}"

    analysis_result = analyzer.analyze_transactions(sample_txs)
    
    for item in analysis_result['transactions']:
        tx = Transaction(
            user_id=current_user.id,
            batch_id=batch_id,
            external_tx_id=item['external_tx_id'],
            amount=item['amount'],
            currency=item.get('currency', 'USD'),
            timestamp=pd_parse_date(item['timestamp']),
            sender=item['sender'],
            recipient=item['recipient'],
            category=item['category'],
            description=item.get('description', '') + ' (DEMO SAMPLE)'
        )
        db.session.add(tx)
        db.session.flush()

        risk = RiskResult(
            transaction_id=tx.id,
            user_id=current_user.id,
            risk_score=item['risk_score'],
            risk_level=item['risk_level'],
            is_anomaly=item['is_anomaly'],
            is_duplicate=item['is_duplicate'],
            detected_indicators=json.dumps(item['detected_indicators']),
            explanation=item['explanation'],
            recommended_action=item['recommended_action'],
            review_status='pending'
        )
        db.session.add(risk)

    db.session.commit()
    log_action(current_user.id, 'LOAD_DEMO_TRANSACTIONS', 'security', {'batch_id': batch_id})

    return jsonify({
        'success': True,
        'message': 'Demo sample transactions loaded and evaluated successfully!',
        'batch_id': batch_id,
        'metrics': analysis_result['metrics'],
        'transactions': analysis_result['transactions']
    })


@security_bp.route('/api/security/history', methods=['GET'])
@login_required
def get_security_history():
    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'transactions': [t.to_dict() for t in txs]
    })


@security_bp.route('/api/security/alerts', methods=['GET'])
@login_required
def get_security_alerts():
    high_risks = RiskResult.query.filter_by(user_id=current_user.id, risk_level='HIGH').order_by(RiskResult.created_at.desc()).all()
    return jsonify({
        'success': True,
        'alerts': [r.to_dict() for r in high_risks]
    })


@security_bp.route('/api/security/review', methods=['POST'])
@login_required
def review_transaction():
    data = request.get_json(silent=True) or {}
    tx_id = data.get('transaction_id')
    decision = data.get('decision')  # 'approved', 'flagged_fraud'

    if not tx_id or decision not in ['approved', 'flagged_fraud']:
        return jsonify({'success': False, 'error': 'Invalid transaction ID or decision value.'}), 400

    risk = RiskResult.query.filter_by(transaction_id=tx_id, user_id=current_user.id).first()
    if not risk:
        return jsonify({'success': False, 'error': 'Risk record not found.'}), 404

    risk.review_status = decision
    risk.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()

    log_action(current_user.id, 'MANUAL_TX_REVIEW', 'security', {'tx_id': tx_id, 'decision': decision})
    return jsonify({'success': True, 'message': f'Transaction review status updated to {decision}.', 'risk': risk.to_dict()})


def pd_parse_date(val):
    if isinstance(val, datetime):
        return val
    try:
        from dateutil import parser
        return parser.parse(str(val))
    except Exception:
        return datetime.now(timezone.utc)
