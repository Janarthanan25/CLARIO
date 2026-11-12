from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from agents.report_agent import ReportAgent
from models.models import Document, EmailRecord, Transaction, RiskResult

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports', methods=['GET'])
@login_required
def reports_view():
    doc_count = Document.query.filter_by(user_id=current_user.id).count()
    email_count = EmailRecord.query.filter_by(user_id=current_user.id).count()
    tx_count = Transaction.query.filter_by(user_id=current_user.id).count()
    high_risk_count = RiskResult.query.filter_by(user_id=current_user.id, risk_level='HIGH').count()

    metrics = {
        'documents_count': doc_count,
        'emails_count': email_count,
        'transactions_count': tx_count,
        'high_risk_count': high_risk_count
    }
    return render_template('reports.html', metrics=metrics)

@report_bp.route('/api/reports/generate', methods=['POST'])
@login_required
def generate_report():
    data = request.get_json(silent=True) or {}
    report_type = data.get('report_type', 'executive_summary')

    agent = ReportAgent(user_id=current_user.id)
    exec_res = agent.execute({'report_type': report_type})

    if exec_res.get('status') == 'completed':
        return jsonify({
            'success': True,
            'report': exec_res['data'],
            'tools_called': exec_res['tools_called']
        })
    return jsonify({'success': False, 'error': exec_res.get('error', 'Report generation failed.')}), 500

@report_bp.route('/api/reports/download', methods=['GET'])
@login_required
def download_full_report():
    agent = ReportAgent(user_id=current_user.id)
    exec_res = agent.execute({'report_type': 'comprehensive_audit'})
    content = exec_res.get('data', {}).get('report_content', 'No report content.')

    report_text = f"""# CLARIO EXECUTIVE PLATFORM REPORT
Client ID: {current_user.id} ({current_user.email})
Generated: {exec_res.get('data', {}).get('generated_at', '')}
Plan: {current_user.plan}

==================================================

{content}

==================================================
Report generated automatically by CLARIO Multi-Agent Intelligence System.
"""
    return Response(
        report_text,
        mimetype="text/markdown",
        headers={"Content-disposition": "attachment; filename=CLARIO_Executive_Intelligence_Report.md"}
    )
