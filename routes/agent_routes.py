from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.models import AgentExecution
from agents.master_agent import MasterAgent
from services.audit_service import log_action

agent_bp = Blueprint('agents', __name__)

@agent_bp.route('/agents', methods=['GET'])
@login_required
def agents_view():
    history = AgentExecution.query.filter_by(user_id=current_user.id).order_by(AgentExecution.created_at.desc()).limit(20).all()
    return render_template('agents.html', history=history)


@agent_bp.route('/api/agents/run', methods=['POST'])
@login_required
def run_agent():
    if not current_user.can_make_ai_request():
        return jsonify({
            'success': False,
            'error': 'AI request limit reached for Free plan. Upgrade to Clario Pro for unlimited multi-agent runs.'
        }), 429

    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    context = data.get('context', {})

    if not prompt:
        return jsonify({'success': False, 'error': 'Prompt cannot be empty.'}), 400

    master = MasterAgent(user_id=current_user.id)
    result = master.process_command(prompt, context=context)

    current_user.ai_requests_count += 1
    db.session.commit()

    log_action(current_user.id, 'AGENT_ORCHESTRATION_RUN', 'agents', {'prompt': prompt[:100]})

    return jsonify({
        'success': result.get('status') == 'success',
        'result': result
    })


@agent_bp.route('/api/agents/status', methods=['GET'])
@login_required
def get_agents_status():
    from services.ai_service import ai_service
    is_live = ai_service.is_live_configured()
    
    agent_catalog = [
        {
            'name': 'Master Orchestrator Agent',
            'key': 'master_agent',
            'status': 'OPERATIONAL',
            'description': 'Directs intent routing, calls approved tools, and integrates specialist findings.',
            'engine': f"Google Gemini ({ai_service._get_model()})" if is_live else 'Clario Local Dispatch Matrix'
        },
        {
            'name': 'Document Intelligence Agent',
            'key': 'document_agent',
            'status': 'OPERATIONAL',
            'description': 'Multi-format PDF/DOCX/TXT/CSV text extraction, summarization, and grounded Q&A.',
            'engine': 'PyMuPDF + Docx + AI Summarizer'
        },
        {
            'name': 'Smart Email Agent',
            'key': 'email_agent',
            'status': 'OPERATIONAL',
            'description': 'Sentiment analysis, urgency scoring, task extraction, and multi-tone drafts.',
            'engine': 'NLP Heuristics + Generative Drafter'
        },
        {
            'name': 'Security & Fraud Agent',
            'key': 'security_agent',
            'status': 'OPERATIONAL',
            'description': 'Hybrid rule-based duplicate/velocity scan and Scikit-Learn IsolationForest anomaly detection.',
            'engine': 'Scikit-Learn IsolationForest'
        },
        {
            'name': 'Research Synthesis Agent',
            'key': 'research_agent',
            'status': 'OPERATIONAL',
            'description': 'Cross-references workspace files, emails, and transaction notes for deep insights.',
            'engine': 'Context Correlator + Gemini'
        },
        {
            'name': 'Executive Report Agent',
            'key': 'report_agent',
            'status': 'OPERATIONAL',
            'description': 'Compiles cross-module telemetry into downloadable executive briefings.',
            'engine': 'Telemetry Aggregator'
        }
    ]
    return jsonify({'success': True, 'agents': agent_catalog})


@agent_bp.route('/api/agents/history', methods=['GET'])
@login_required
def get_agents_history():
    history = AgentExecution.query.filter_by(user_id=current_user.id).order_by(AgentExecution.created_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'executions': [e.to_dict() for e in history]
    })
