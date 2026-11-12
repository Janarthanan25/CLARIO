import time
import json
from models import db
from models.models import Document, EmailRecord, Transaction, AgentExecution
from services.ai_service import ai_service

class ResearchAgent:
    """
    Research Specialist Agent:
    Correlates information across user's documents, email communications,
    and security logs to answer complex multi-source inquiries.
    """

    NAME = "research_agent"
    DESCRIPTION = "Cross-references workspace files, emails, and transactions for deep intelligence queries."

    def __init__(self, user_id=None):
        self.user_id = user_id

    def execute(self, task_payload):
        start_time = time.time()
        query = task_payload.get('query', '')
        tools_called = []
        result = {}

        try:
            if not query.strip():
                return {'status': 'failed', 'error': 'Research query cannot be empty.'}

            context_snippets = []

            # 1. Gather document excerpts
            tools_called.append('scan_user_documents')
            if self.user_id:
                docs = Document.query.filter_by(user_id=self.user_id).order_by(Document.uploaded_at.desc()).limit(3).all()
                for d in docs:
                    if d.summary:
                        context_snippets.append(f"Document [{d.original_filename}]: {d.summary[:400]}")

            # 2. Gather email excerpts
            tools_called.append('scan_user_emails')
            if self.user_id:
                emails = EmailRecord.query.filter_by(user_id=self.user_id).order_by(EmailRecord.created_at.desc()).limit(3).all()
                for e in emails:
                    if e.summary:
                        context_snippets.append(f"Email [{e.subject}]: {e.summary}")

            # 3. Gather recent transactions
            tools_called.append('scan_transaction_activity')
            if self.user_id:
                txs = Transaction.query.filter_by(user_id=self.user_id).order_by(Transaction.timestamp.desc()).limit(5).all()
                for t in txs:
                    context_snippets.append(f"Transaction [{t.external_tx_id}]: ${t.amount} {t.currency} to {t.recipient} ({t.category})")

            combined_context = "\n".join(context_snippets) if context_snippets else "No prior workspace artifacts found."
            
            tools_called.append('synthesize_multi_source_intelligence')
            system_prompt = (
                "You are CLARIO Research Agent. Synthesize information accurately across "
                "available workspace documents, communications, and transactions to answer "
                "the user's research query. Provide structured key findings and strategic recommendations."
            )
            prompt = (
                f"User Inquiry: {query}\n\n"
                f"Unified Workspace Context:\n{combined_context}\n\n"
                "Provide an organized research synthesis with citations to context where applicable."
            )

            gen = ai_service.generate_response(prompt, system_instruction=system_prompt)

            result = {
                'agent': self.NAME,
                'query': query,
                'synthesis': gen['text'],
                'sources_consulted_count': len(context_snippets),
                'ai_source': gen['source'],
                'notice': gen.get('notice')
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
                result_summary=result.get('synthesis') or str(result)[:300],
                execution_time_ms=exec_time
            )
            db.session.add(rec)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(f"Error logging research agent execution: {ex}")
