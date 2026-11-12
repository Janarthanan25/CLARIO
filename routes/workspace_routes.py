import os
import json
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, current_app, send_file, Response
from flask_login import login_required, current_user
from models import db
from models.models import Document, Conversation, Message
from modules.workspace.processor import DocumentProcessor
from services.ai_service import ai_service
from services.audit_service import log_action
from services.notification_service import send_notification
from utils.security_utils import allowed_file, sanitize_safe_filename
from utils.sample_data import get_sample_document_text

workspace_bp = Blueprint('workspace', __name__)

@workspace_bp.route('/workspace', methods=['GET'])
@login_required
def workspace_view():
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template('workspace.html', documents=documents)


@workspace_bp.route('/api/documents/upload', methods=['POST'])
@login_required
def upload_document():
    if not current_user.can_upload_document():
        return jsonify({
            'success': False,
            'error': 'Free plan limit reached (5 documents). Please upgrade to Clario Pro for unlimited document uploads.'
        }), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in the request.'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected.'}), 400

    if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        return jsonify({
            'success': False,
            'error': f"Unsupported file extension. Allowed formats: {', '.join(current_app.config['ALLOWED_EXTENSIONS'])}"
        }), 400

    orig_name = file.filename
    clean_name = sanitize_safe_filename(orig_name)
    ext = clean_name.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{clean_name}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    try:
        file.save(save_path)
        file_size = os.path.getsize(save_path)

        # 1. Text extraction
        extracted_text = DocumentProcessor.extract_text(save_path, ext)
        
        # 2. CSV processing if applicable
        csv_meta_json = None
        row_count = 0
        if ext == 'csv':
            csv_data = DocumentProcessor.process_csv(save_path)
            csv_meta_json = json.dumps(csv_data)
            row_count = csv_data.get('row_count', 0)

        # 3. AI Document Summarization & Entity Extraction
        summary_result = ai_service.summarize_document(extracted_text, doc_name=orig_name)

        doc = Document(
            user_id=current_user.id,
            filename=unique_filename,
            original_filename=orig_name,
            file_type=ext,
            file_size=file_size,
            file_path=save_path,
            summary=summary_result.get('executive_summary', ''),
            key_dates=json.dumps(summary_result.get('key_dates', [])),
            key_entities=json.dumps(summary_result.get('key_entities', {})),
            csv_metadata=csv_meta_json,
            row_count=row_count,
            status='processed'
        )
        db.session.add(doc)
        db.session.commit()

        current_user.ai_requests_count += 1
        db.session.commit()

        log_action(current_user.id, 'DOCUMENT_UPLOAD', 'documents', {'doc_id': doc.id, 'filename': orig_name})
        send_notification(
            user_id=current_user.id,
            title="Document Processed 📄",
            message=f"'{orig_name}' has been parsed, indexed, and summarized successfully.",
            category="document",
            link="/workspace"
        )

        return jsonify({
            'success': True,
            'message': 'Document uploaded and analyzed successfully!',
            'document': doc.to_dict(),
            'key_points': summary_result.get('key_points', []),
            'ai_source': summary_result.get('ai_source'),
            'notice': summary_result.get('notice')
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f"Failed to process document: {str(e)}"}), 500


@workspace_bp.route('/api/documents/load-sample', methods=['POST'])
@login_required
def load_sample_document():
    """Load a sample demonstration financial report for instant testing"""
    sample_text = get_sample_document_text()
    orig_name = "CLARIO_Q3_Financial_Intelligence_Report_SAMPLE.txt"
    unique_filename = f"{uuid.uuid4().hex}_{orig_name}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(sample_text)

    file_size = os.path.getsize(save_path)
    summary_result = ai_service.summarize_document(sample_text, doc_name=orig_name)

    doc = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=orig_name,
        file_type='txt',
        file_size=file_size,
        file_path=save_path,
        summary=summary_result.get('executive_summary', ''),
        key_dates=json.dumps(summary_result.get('key_dates', [])),
        key_entities=json.dumps(summary_result.get('key_entities', {})),
        status='processed'
    )
    db.session.add(doc)
    db.session.commit()

    log_action(current_user.id, 'LOAD_SAMPLE_DOCUMENT', 'documents', {'doc_id': doc.id})
    return jsonify({
        'success': True,
        'message': 'Sample demonstration report loaded into workspace!',
        'document': doc.to_dict()
    })


@workspace_bp.route('/api/documents/history', methods=['GET'])
@login_required
def get_documents_history():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return jsonify({
        'success': True,
        'documents': [d.to_dict() for d in docs]
    })


@workspace_bp.route('/api/documents/<int:doc_id>', methods=['GET'])
@login_required
def get_document_details(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    
    text_content = ""
    try:
        text_content = DocumentProcessor.extract_text(doc.file_path, doc.file_type)
    except Exception as e:
        text_content = f"Error reading file contents: {e}"

    data = doc.to_dict()
    data['content_preview'] = text_content[:8000]
    return jsonify({'success': True, 'document': data})


@workspace_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        print(f"Error removing file from disk: {e}")

    log_action(current_user.id, 'DOCUMENT_DELETE', 'documents', {'doc_id': doc.id, 'filename': doc.original_filename})
    db.session.delete(doc)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Document deleted successfully.'})


@workspace_bp.route('/api/documents/chat', methods=['POST'])
@login_required
def chat_document():
    if not current_user.can_make_ai_request():
        return jsonify({
            'success': False,
            'error': 'AI request limit reached for Free plan (25 requests/day). Upgrade to Clario Pro for unlimited AI queries.'
        }), 429

    data = request.get_json(silent=True) or {}
    doc_id = data.get('document_id')
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'success': False, 'error': 'Question cannot be empty.'}), 400

    if not doc_id:
        return jsonify({'success': False, 'error': 'Please select a document to query.'}), 400

    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({'success': False, 'error': 'Document not found.'}), 404

    try:
        text = DocumentProcessor.extract_text(doc.file_path, doc.file_type)
        res = DocumentProcessor.answer_question(text, question, doc_title=doc.original_filename)

        current_user.ai_requests_count += 1

        # Multi-turn conversation persistence
        conv_title = f"Document #{doc.id}: {doc.original_filename[:50]}"
        conv = Conversation.query.filter_by(user_id=current_user.id, title=conv_title).first()
        if not conv:
            conv = Conversation(
                user_id=current_user.id,
                title=conv_title,
                agent_type='document_agent'
            )
            db.session.add(conv)
            db.session.flush()

        user_msg = Message(
            conversation_id=conv.id,
            sender='user',
            content=question
        )
        agent_msg = Message(
            conversation_id=conv.id,
            sender='agent',
            content=res['answer'],
            metadata_json=json.dumps({
                'source': res.get('source'),
                'notice': res.get('notice'),
                'document_id': doc.id
            })
        )
        db.session.add(user_msg)
        db.session.add(agent_msg)
        db.session.commit()

        log_action(current_user.id, 'DOCUMENT_QA', 'documents', {'doc_id': doc.id, 'question': question[:60]})

        return jsonify({
            'success': True,
            'question': question,
            'answer': res['answer'],
            'ai_source': res['source'],
            'notice': res.get('notice'),
            'conversation_id': conv.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f"Failed to answer question: {str(e)}"}), 500


@workspace_bp.route('/api/documents/<int:doc_id>/messages', methods=['GET'])
@login_required
def get_document_messages(doc_id):
    """Retrieve persisted multi-turn Q&A message history for this document"""
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    conv_title = f"Document #{doc.id}: {doc.original_filename[:50]}"
    conv = Conversation.query.filter_by(user_id=current_user.id, title=conv_title).first()
    
    if not conv:
        return jsonify({'success': True, 'messages': []})

    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc()).all()
    return jsonify({
        'success': True,
        'conversation_id': conv.id,
        'messages': [m.to_dict() for m in messages]
    })


@workspace_bp.route('/api/documents/<int:doc_id>/download-report', methods=['GET'])
@login_required
def download_document_report(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    
    report_md = f"""# CLARIO INTELLIGENCE REPORT
Document: {doc.original_filename}
File Type: {doc.file_type.upper()}
Processed At: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
Security Hash: {doc.filename}

---

## EXECUTIVE SUMMARY
{doc.summary or 'No summary generated.'}

## DETECTED KEY DATES
{chr(10).join(['- ' + d for d in doc.get_key_dates()]) if doc.get_key_dates() else 'No explicit dates detected.'}

## IDENTIFIED ENTITIES & FINANCIAL MARKERS
{json.dumps(doc.get_key_entities(), indent=2)}

---
Generated by CLARIO – Unified AI Workspace, Intelligent Communication & Payment Security Platform.
"""
    return Response(
        report_md,
        mimetype="text/markdown",
        headers={"Content-disposition": f"attachment; filename=CLARIO_REPORT_{doc.original_filename}.md"}
    )
