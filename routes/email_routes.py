import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.models import EmailRecord
from modules.email.assistant import EmailAssistant
from services.audit_service import log_action
from services.notification_service import send_notification
from utils.sample_data import get_sample_emails

email_bp = Blueprint('email', __name__)

@email_bp.route('/email', methods=['GET'])
@login_required
def email_view():
    recent_emails = EmailRecord.query.filter_by(user_id=current_user.id).order_by(EmailRecord.created_at.desc()).limit(15).all()
    sample_list = get_sample_emails()
    return render_template('email.html', recent_emails=recent_emails, sample_emails=sample_list)


@email_bp.route('/api/emails/analyze', methods=['POST'])
@login_required
def analyze_email():
    if not current_user.can_make_ai_request():
        return jsonify({
            'success': False,
            'error': 'AI request limit reached for Free plan (25 requests/day). Please upgrade to Clario Pro for unlimited AI requests.'
        }), 429

    data = request.get_json(silent=True) or {}
    body = data.get('body', '').strip()
    subject = data.get('subject', '').strip() or 'Inbound Correspondence'
    sender = data.get('sender', '').strip() or 'Unknown Sender'
    tone = data.get('tone', 'Professional')

    if not body:
        return jsonify({'success': False, 'error': 'Email body cannot be empty.'}), 400

    try:
        processed = EmailAssistant.process_email(
            body=body,
            subject=subject,
            sender=sender,
            desired_tone=tone
        )

        record = EmailRecord(
            user_id=current_user.id,
            subject=subject,
            sender=sender,
            body=body,
            category=processed['category'],
            sentiment=processed['sentiment'],
            urgency_score=processed['urgency_score'],
            summary=processed['summary'],
            extracted_tasks=json.dumps(processed['tasks']),
            deadlines=json.dumps(processed['deadlines']),
            generated_reply=processed['generated_reply'],
            reply_tone=tone
        )
        db.session.add(record)
        current_user.ai_requests_count += 1
        db.session.commit()

        log_action(current_user.id, 'EMAIL_ANALYSIS', 'emails', {'email_id': record.id, 'category': processed['category']})
        send_notification(
            user_id=current_user.id,
            title="Email Analyzed ✉️",
            message=f"Categorized as {processed['category']} (Urgency: {int(processed['urgency_score']*100)}%). Response drafted.",
            category="email",
            link="/email"
        )

        return jsonify({
            'success': True,
            'email': record.to_dict(),
            'ai_source': processed.get('ai_source'),
            'notice': processed.get('notice')
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f"Failed to analyze email: {str(e)}"}), 500


@email_bp.route('/api/emails/draft', methods=['POST'])
@login_required
def draft_email_reply():
    if not current_user.can_make_ai_request():
        return jsonify({
            'success': False,
            'error': 'AI request limit reached for Free plan. Upgrade to Clario Pro for unlimited drafts.'
        }), 429

    data = request.get_json(silent=True) or {}
    body = data.get('body', '').strip()
    tone = data.get('tone', 'Professional')
    instruction = data.get('instruction', '')

    if not body:
        return jsonify({'success': False, 'error': 'Original email body is required.'}), 400

    try:
        draft = EmailAssistant.regenerate_reply(
            email_body=body,
            tone=tone,
            custom_instruction=instruction
        )
        current_user.ai_requests_count += 1
        db.session.commit()

        return jsonify({
            'success': True,
            'reply': draft['reply'],
            'tone': draft['tone'],
            'ai_source': draft.get('source'),
            'notice': draft.get('notice')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to generate reply: {str(e)}"}), 500


@email_bp.route('/api/emails/<int:email_id>/approve', methods=['POST'])
@login_required
def approve_email(email_id):
    """Explicit human-in-the-loop approval of generated email response"""
    record = EmailRecord.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
    
    log_action(current_user.id, 'EMAIL_DRAFT_APPROVED_BY_USER', 'emails', {'email_id': record.id, 'subject': record.subject})
    send_notification(
        user_id=current_user.id,
        title="Email Draft Approved ✓",
        message=f"Response draft for '{record.subject}' verified and approved by operator.",
        category="email",
        link="/email"
    )

    return jsonify({
        'success': True,
        'message': 'Draft response approved and logged to verified outbox.',
        'email': record.to_dict()
    })


@email_bp.route('/api/emails/history', methods=['GET'])
@login_required
def get_email_history():
    records = EmailRecord.query.filter_by(user_id=current_user.id).order_by(EmailRecord.created_at.desc()).all()
    return jsonify({
        'success': True,
        'emails': [r.to_dict() for r in records]
    })
