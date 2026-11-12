import time
import json
from datetime import datetime, timezone
from models import db
from models.models import Document, EmailRecord, Transaction, RiskResult, AgentExecution
from services.ai_service import ai_service

class ReportAgent:
    """
    Report Specialist Agent:
    Compiles executive reports, compliance analytics, and operational briefs
    summarizing all cross-module activity for the user.
    """

    NAME = "report_agent"
    DESCRIPTION = "Compiles structured executive summaries and analytics across workspace and security operations."

    def __init__(self, user_id=None):
        self.user_id = user_id

    def execute(self, task_payload):
        start_time = time.time()
        report_type = task_payload.get('report_type', 'executive_summary')
        tools_called = []
        result = {}

        try:
            tools_called.append('aggregate_platform_metrics')
            
            doc_count = Document.query.filter_by(user_id=self.user_id).count() if self.user_id else 0
            email_count = EmailRecord.query.filter_by(user_id=self.user_id).count() if self.user_id else 0
            tx_count = Transaction.query.filter_by(user_id=self.user_id).count() if self.user_id else 0
            high_risk_tx_count = RiskResult.query.filter_by(user_id=self.user_id, risk_level='HIGH').count() if self.user_id else 0
            recent_agent_runs = AgentExecution.query.filter_by(user_id=self.user_id).count() if self.user_id else 0

            tools_called.append('compile_cross_module_statistics')

            stats_context = (
                f"- Documents Processed: {doc_count}\n"
                f"- Emails Analyzed: {email_count}\n"
                f"- Financial Transactions Audited: {tx_count}\n"
                f"- High-Risk Alerts Flagged: {high_risk_tx_count}\n"
                f"- Total Multi-Agent Executions: {recent_agent_runs}\n"
            )

            supplementary = task_payload.get('supplementary_context')
            if supplementary:
                stats_context += f"- Upstream Specialist Intelligence:\n  {supplementary}\n"
                tools_called.append('incorporate_prior_agent_findings')

            tools_called.append('generate_executive_narrative')
            system_prompt = (
                "You are CLARIO Report Agent. Compile a professional executive intelligence briefing "
                "based on the platform metrics provided. Format with structured sections: "
                "1. Executive Summary, 2. Key Operational Findings, 3. Security & Risk Assessment, "
                "4. Strategic Action Items."
            )
            prompt = f"Report Type: {report_type}\nPlatform Telemetry:\n{stats_context}"

            gen = ai_service.generate_response(prompt, system_instruction=system_prompt)

            result = {
                'agent': self.NAME,
                'report_type': report_type,
                'generated_at': datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC"),
                'metrics': {
                    'documents_count': doc_count,
                    'emails_count': email_count,
                    'transactions_count': tx_count,
                    'high_risk_count': high_risk_tx_count,
                    'agent_executions': recent_agent_runs
                },
                'report_content': gen['text'],
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
                result_summary=result.get('report_content') or str(result)[:300],
                execution_time_ms=exec_time
            )
            db.session.add(rec)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(f"Error logging report agent execution: {ex}")
