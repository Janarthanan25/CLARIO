from datetime import datetime, timezone
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user', 'admin'
    plan = db.Column(db.String(20), default='FREE', nullable=False)  # 'FREE', 'PRO'
    subscription_status = db.Column(db.String(20), default='inactive', nullable=False)  # 'active', 'inactive', 'cancelled'
    ai_requests_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    documents = db.relationship('Document', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    emails = db.relationship('EmailRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    risk_results = db.relationship('RiskResult', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    agent_executions = db.relationship('AgentExecution', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def can_upload_document(self):
        if self.plan == 'PRO':
            return True
        count = self.documents.count()
        return count < 5

    def can_make_ai_request(self):
        if self.plan == 'PRO':
            return True
        return self.ai_requests_count < 25

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name or self.username,
            'role': self.role,
            'plan': self.plan,
            'subscription_status': self.subscription_status,
            'ai_requests_count': self.ai_requests_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf', 'docx', 'txt', 'csv'
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_path = db.Column(db.String(512), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    key_dates = db.Column(db.Text, nullable=True)  # JSON string
    key_entities = db.Column(db.Text, nullable=True)  # JSON string
    csv_metadata = db.Column(db.Text, nullable=True)  # JSON string of schema and stats
    row_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processed', nullable=False)  # 'processing', 'processed', 'failed'

    def get_key_dates(self):
        try:
            return json.loads(self.key_dates) if self.key_dates else []
        except Exception:
            return []

    def get_key_entities(self):
        try:
            return json.loads(self.key_entities) if self.key_entities else {}
        except Exception:
            return {}

    def get_csv_metadata(self):
        try:
            return json.loads(self.csv_metadata) if self.csv_metadata else {}
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'summary': self.summary,
            'key_dates': self.get_key_dates(),
            'key_entities': self.get_key_entities(),
            'csv_metadata': self.get_csv_metadata(),
            'row_count': self.row_count,
            'status': self.status
        }


class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), default='New AI Conversation', nullable=False)
    agent_type = db.Column(db.String(50), default='master', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'agent_type': self.agent_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'agent', 'system'
    content = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)  # JSON for structured agent outputs
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_metadata(self):
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.sender,
            'content': self.content,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EmailRecord(db.Model):
    __tablename__ = 'email_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=True)
    sender = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='Work', nullable=False)  # 'Important', 'Work', 'Personal', 'Finance', 'Promotions', 'Urgent'
    sentiment = db.Column(db.String(20), default='Neutral', nullable=False)  # 'Positive', 'Neutral', 'Negative'
    urgency_score = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 - 1.0
    summary = db.Column(db.Text, nullable=True)
    extracted_tasks = db.Column(db.Text, nullable=True)  # JSON list
    deadlines = db.Column(db.Text, nullable=True)  # JSON list
    generated_reply = db.Column(db.Text, nullable=True)
    reply_tone = db.Column(db.String(30), default='Professional', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_tasks(self):
        try:
            return json.loads(self.extracted_tasks) if self.extracted_tasks else []
        except Exception:
            return []

    def get_deadlines(self):
        try:
            return json.loads(self.deadlines) if self.deadlines else []
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'sender': self.sender,
            'body': self.body,
            'category': self.category,
            'sentiment': self.sentiment,
            'urgency_score': self.urgency_score,
            'summary': self.summary,
            'extracted_tasks': self.get_tasks(),
            'deadlines': self.get_deadlines(),
            'generated_reply': self.generated_reply,
            'reply_tone': self.reply_tone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    batch_id = db.Column(db.String(64), nullable=True, index=True)
    external_tx_id = db.Column(db.String(64), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD', nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender = db.Column(db.String(120), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), default='Transfer', nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    risk_result = db.relationship('RiskResult', backref='transaction', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'batch_id': self.batch_id,
            'external_tx_id': self.external_tx_id,
            'amount': self.amount,
            'currency': self.currency,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'sender': self.sender,
            'recipient': self.recipient,
            'category': self.category,
            'description': self.description,
            'risk_result': self.risk_result.to_dict() if self.risk_result else None
        }


class RiskResult(db.Model):
    __tablename__ = 'risk_results'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    risk_score = db.Column(db.Float, nullable=False)  # 0.0 - 100.0
    risk_level = db.Column(db.String(20), default='LOW', nullable=False)  # 'LOW', 'MEDIUM', 'HIGH'
    is_anomaly = db.Column(db.Boolean, default=False, nullable=False)
    is_duplicate = db.Column(db.Boolean, default=False, nullable=False)
    detected_indicators = db.Column(db.Text, nullable=True)  # JSON list
    explanation = db.Column(db.Text, nullable=True)
    recommended_action = db.Column(db.String(255), nullable=True)
    review_status = db.Column(db.String(30), default='pending', nullable=False)  # 'pending', 'approved', 'flagged_fraud'
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_indicators(self):
        try:
            return json.loads(self.detected_indicators) if self.detected_indicators else []
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'is_anomaly': self.is_anomaly,
            'is_duplicate': self.is_duplicate,
            'detected_indicators': self.get_indicators(),
            'explanation': self.explanation,
            'recommended_action': self.recommended_action,
            'review_status': self.review_status,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentExecution(db.Model):
    __tablename__ = 'agent_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    agent_name = db.Column(db.String(50), nullable=False)  # 'master', 'document', 'email', 'security', 'research', 'report'
    prompt = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='completed', nullable=False)  # 'pending', 'running', 'completed', 'failed'
    tools_called = db.Column(db.Text, nullable=True)  # JSON list of tools
    result_summary = db.Column(db.Text, nullable=True)
    execution_time_ms = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_tools_called(self):
        try:
            return json.loads(self.tools_called) if self.tools_called else []
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'agent_name': self.agent_name,
            'prompt': self.prompt,
            'status': self.status,
            'tools_called': self.get_tools_called(),
            'result_summary': self.result_summary,
            'execution_time_ms': self.execution_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    capture_id = db.Column(db.String(128), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD', nullable=False)
    status = db.Column(db.String(30), default='COMPLETED', nullable=False)
    payer_email = db.Column(db.String(120), nullable=True)
    payer_id = db.Column(db.String(64), nullable=True)
    payment_source = db.Column(db.String(50), default='paypal', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'capture_id': self.capture_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payer_email': self.payer_email,
            'payer_id': self.payer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_name = db.Column(db.String(30), default='FREE', nullable=False)
    paypal_subscription_id = db.Column(db.String(128), nullable=True)
    paypal_order_id = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(30), default='ACTIVE', nullable=False)
    starts_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_name': self.plan_name,
            'paypal_order_id': self.paypal_order_id,
            'status': self.status,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='system', nullable=False)  # 'document', 'email', 'security', 'payment', 'system'
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_details(self):
        try:
            return json.loads(self.details_json) if self.details_json else {}
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'details': self.get_details(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
