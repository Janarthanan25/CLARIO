import time
import json
from models import db
from models.models import EmailRecord, AgentExecution
from modules.email.assistant import EmailAssistant
from services.ai_service import ai_service

class EmailAgent:
    """
    Email Specialist Agent:
    Performs sentiment analysis, urgency detection, task/deadline extraction,
    and adaptive multi-tone reply generation.
    """

    NAME = "email_agent"
    DESCRIPTION = "Evaluates inbound emails, categorizes urgency, extracts tasks, and generates replies."

    def __init__(self, user_id=None):
        self.user_id = user_id

    def execute(self, task_payload):
        start_time = time.time()
        body = task_payload.get('body', '')
        subject = task_payload.get('subject', 'General Correspondence')
        sender = task_payload.get('sender', 'stakeholder@example.com')
        tone = task_payload.get('tone', 'Professional')
        action = task_payload.get('action', 'analyze_and_draft')

        tools_called = []
        result = {}

        try:
            if not body.strip():
                return {'status': 'failed', 'error': 'Email body cannot be empty.'}

            tools_called.append('parse_email_headers')
            tools_called.append('extract_sentiment_and_urgency')
            
            processed = EmailAssistant.process_email(
                body=body,
                subject=subject,
                sender=sender,
                desired_tone=tone
            )
            tools_called.append(f'draft_{tone.lower()}_reply')

            # Save to user email records if requested
            if task_payload.get('save_record', True) and self.user_id:
                tools_called.append('persist_email_record')
                record = EmailRecord(
                    user_id=self.user_id,
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
                db.session.commit()
                processed['record_id'] = record.id

            result = {
                'agent': self.NAME,
                'subject': subject,
                'category': processed['category'],
                'sentiment': processed['sentiment'],
                'urgency_score': processed['urgency_score'],
                'summary': processed['summary'],
                'tasks': processed['tasks'],
                'deadlines': processed['deadlines'],
                'generated_reply': processed['generated_reply'],
                'reply_tone': tone,
                'followup_suggestion': processed['followup_suggestion'],
                'ai_source': processed.get('ai_source'),
                'notice': processed.get('notice')
            }

            execution_time = int((time.time() - start_time) * 1000)
            self._log_execution(task_payload, 'completed', tools_called, result, execution_time)
            return {'status': 'completed', 'data': result, 'tools_called': tools_called, 'execution_time_ms': execution_time}

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self._log_execution(task_payload, 'failed', tools_called, {'error': str(e)}, execution_time)
            return {'status': 'failed', 'error': str(e), 'tools_called': tools_called}

    def _log_execution(self, prompt_obj, status, tools, result, exec_time):
        if not self.user_id:
            return
        try:
            rec = AgentExecution(
                user_id=self.user_id,
                agent_name=self.NAME,
                prompt=json.dumps(prompt_obj) if isinstance(prompt_obj, dict) else str(prompt_obj),
                status=status,
                tools_called=json.dumps(tools),
                result_summary=result.get('summary') or str(result)[:300],
                execution_time_ms=exec_time
            )
            db.session.add(rec)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(f"Error logging email agent execution: {ex}")
