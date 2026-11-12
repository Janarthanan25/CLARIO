import time
from models import db
from models.models import Document, AgentExecution
from modules.workspace.processor import DocumentProcessor
from services.ai_service import ai_service

class DocumentAgent:
    """
    Document Specialist Agent:
    Performs real document parsing, summarization, entity extraction,
    and grounded question answering against user's uploaded repository.
    """
    
    NAME = "document_agent"
    DESCRIPTION = "Extracts document intelligence, summarizes text, and answers context-grounded queries."

    def __init__(self, user_id=None):
        self.user_id = user_id

    def execute(self, task_payload):
        start_time = time.time()
        action = task_payload.get('action', 'summarize')
        doc_id = task_payload.get('document_id')
        query = task_payload.get('query', '')
        raw_text = task_payload.get('text', '')

        tools_called = []
        result = {}

        try:
            target_text = raw_text
            doc_title = "Direct Text Input"

            if doc_id:
                doc = Document.query.filter_by(id=doc_id, user_id=self.user_id).first()
                if not doc:
                    return {'status': 'failed', 'error': f'Document #{doc_id} not found or unauthorized.'}
                doc_title = doc.original_filename
                tools_called.append('retrieve_document_from_db')
                target_text = DocumentProcessor.extract_text(doc.file_path, doc.file_type)
                tools_called.append(f'extract_text_{doc.file_type}')
            elif not target_text and self.user_id:
                doc = Document.query.filter_by(user_id=self.user_id).order_by(Document.uploaded_at.desc()).first()
                if doc:
                    doc_title = doc.original_filename
                    tools_called.append('retrieve_latest_document_from_db')
                    target_text = DocumentProcessor.extract_text(doc.file_path, doc.file_type)
                    tools_called.append(f'extract_text_{doc.file_type}')

            if not target_text.strip():
                return {
                    'status': 'failed',
                    'error': 'No document text available. Please upload a document to your workspace or provide text to analyze.',
                    'tools_called': tools_called
                }

            if action == 'query' or query:
                tools_called.append('semantic_context_search')
                qa_res = DocumentProcessor.answer_question(target_text, query, doc_title=doc_title)
                tools_called.append('grounded_qa_generation')
                result = {
                    'agent': self.NAME,
                    'action': 'query',
                    'query': query,
                    'document_title': doc_title,
                    'answer': qa_res['answer'],
                    'ai_source': qa_res['source'],
                    'notice': qa_res.get('notice')
                }
            else:
                tools_called.append('ai_document_summarization')
                summary_data = ai_service.summarize_document(target_text, doc_name=doc_title)
                result = {
                    'agent': self.NAME,
                    'action': 'summarize',
                    'document_title': doc_title,
                    'executive_summary': summary_data.get('executive_summary'),
                    'key_points': summary_data.get('key_points', []),
                    'key_dates': summary_data.get('key_dates', []),
                    'key_entities': summary_data.get('key_entities', {}),
                    'document_type': summary_data.get('document_type_detected'),
                    'ai_source': summary_data.get('ai_source'),
                    'notice': summary_data.get('notice')
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
            import json
            rec = AgentExecution(
                user_id=self.user_id,
                agent_name=self.NAME,
                prompt=json.dumps(prompt_obj) if isinstance(prompt_obj, dict) else str(prompt_obj),
                status=status,
                tools_called=json.dumps(tools),
                result_summary=result.get('answer') or result.get('executive_summary') or str(result)[:300],
                execution_time_ms=exec_time
            )
            db.session.add(rec)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(f"Error logging agent execution: {ex}")
