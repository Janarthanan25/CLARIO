import time
import json
from models import db
from models.models import AgentExecution
from services.ai_service import ai_service
from .document_agent import DocumentAgent
from .email_agent import EmailAgent
from .security_agent import SecurityAgent
from .research_agent import ResearchAgent
from .report_agent import ReportAgent

class MasterAgent:
    """
    CLARIO Master Orchestrator Agent.
    Interprets natural-language user commands, determines required workflows,
    coordinates specialized subordinate agents, gathers their verifiable outputs,
    and returns an integrated structured response.
    """

    NAME = "master_agent"

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.specialists = {
            'document_agent': DocumentAgent(user_id=user_id),
            'email_agent': EmailAgent(user_id=user_id),
            'security_agent': SecurityAgent(user_id=user_id),
            'research_agent': ResearchAgent(user_id=user_id),
            'report_agent': ReportAgent(user_id=user_id)
        }

    def process_command(self, user_prompt, context=None):
        """
        Main entry point for natural-language agent orchestration.
        """
        start_time = time.time()
        context = context or {}
        tools_called = ['interpret_user_intent', 'orchestrate_specialists']

        try:
            # 1. Orchestration reasoning step via AI Service
            plan = ai_service.orchestrate_agents(user_prompt, context_data=context)
            primary_agent_key = plan.get('primary_agent', 'research_agent')
            secondary_agents = plan.get('secondary_agents', [])
            reasoning = plan.get('reasoning', 'Routed based on semantic analysis.')

            # Ensure valid agent key
            if primary_agent_key not in self.specialists:
                primary_agent_key = 'research_agent'

            tools_called.append(f'dispatch_to_{primary_agent_key}')
            
            # Prepare task payload based on primary agent type and prompt
            task_payload = self._build_task_payload(primary_agent_key, user_prompt, context)
            
            # Execute primary specialist
            primary_agent = self.specialists[primary_agent_key]
            primary_exec = primary_agent.execute(task_payload)

            specialist_results = {
                primary_agent_key: primary_exec
            }

            # Optional secondary orchestration if requested in plan
            for sec_key in secondary_agents:
                if sec_key in self.specialists and sec_key != primary_agent_key:
                    tools_called.append(f'dispatch_to_{sec_key}')
                    sec_payload = self._build_task_payload(sec_key, user_prompt, context, previous_result=primary_exec)
                    sec_exec = self.specialists[sec_key].execute(sec_payload)
                    specialist_results[sec_key] = sec_exec

            # Final response synthesis
            final_summary = self._synthesize_final_brief(user_prompt, plan, specialist_results)

            execution_time = int((time.time() - start_time) * 1000)
            self._log_execution(user_prompt, 'completed', tools_called, final_summary, execution_time)

            return {
                'status': 'success',
                'master_orchestration': {
                    'intent': plan.get('intent', 'task_execution'),
                    'primary_agent': primary_agent_key,
                    'secondary_agents': secondary_agents,
                    'reasoning': reasoning,
                    'plan': plan.get('immediate_answer_or_plan', ''),
                    'ai_source': plan.get('ai_source')
                },
                'tools_called': tools_called,
                'specialist_results': specialist_results,
                'final_summary': final_summary,
                'execution_time_ms': execution_time
            }

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self._log_execution(user_prompt, 'failed', tools_called, {'error': str(e)}, execution_time)
            return {
                'status': 'error',
                'error': str(e),
                'tools_called': tools_called,
                'execution_time_ms': execution_time
            }

    def _build_task_payload(self, agent_key, prompt, context, previous_result=None):
        # Extract prior specialist findings for agent-to-agent pipeline handoffs
        prev_summary = None
        prev_agent_name = None
        if previous_result and isinstance(previous_result, dict):
            prev_data = previous_result.get('data', {})
            prev_agent_name = prev_data.get('agent', 'Specialist')
            prev_summary = (
                prev_data.get('summary')
                or prev_data.get('synthesis')
                or prev_data.get('executive_summary')
                or prev_data.get('answer')
                or prev_data.get('report_content')
            )

        if agent_key == 'document_agent':
            text = context.get('document_text', '')
            if not text and prev_summary:
                text = prev_summary
            return {
                'document_id': context.get('document_id'),
                'query': prompt,
                'text': text,
                'action': 'query' if context.get('document_id') or text else 'summarize'
            }
        elif agent_key == 'email_agent':
            body = context.get('email_body')
            if not body:
                if prev_summary:
                    body = f"Please review the following findings regarding '{prompt}':\n\n{prev_summary}"
                else:
                    body = prompt
            subject = context.get('email_subject') or (f"Intelligence Update: {prompt[:40]}" if prev_summary else 'Inbox Item')
            return {
                'body': body,
                'subject': subject,
                'sender': context.get('email_sender', 'sender@example.com'),
                'tone': context.get('tone', 'Professional'),
                'action': 'analyze_and_draft'
            }
        elif agent_key == 'security_agent':
            return {
                'transactions': context.get('transactions'),
                'load_demo': context.get('load_demo', True if not context.get('transactions') else False),
                'batch_id': context.get('batch_id', 'AGENT-TX-BATCH')
            }
        elif agent_key == 'report_agent':
            payload = {'report_type': context.get('report_type', 'executive_summary')}
            if prev_summary:
                payload['supplementary_context'] = f"Prior Finding ({prev_agent_name}): {prev_summary}"
            return payload
        else: # research_agent
            query = prompt
            if prev_summary:
                query = f"{prompt}\n\n[Context from {prev_agent_name}]: {prev_summary}"
            return {
                'query': query
            }

    def _synthesize_final_brief(self, prompt, plan, specialist_results):
        parts = []
        for agent_name, res in specialist_results.items():
            if res.get('status') == 'completed':
                data = res.get('data', {})
                if 'answer' in data:
                    parts.append(f"**Document Agent Insight:** {data['answer']}")
                elif 'executive_summary' in data:
                    parts.append(f"**Document Summary:** {data['executive_summary']}")
                elif 'summary' in data and agent_name == 'security_agent':
                    parts.append(f"**Security Evaluation:** {data['summary']}")
                elif 'summary' in data and agent_name == 'email_agent':
                    parts.append(f"**Email Assistant Analysis:** {data['summary']} (Category: {data.get('category')}, Urgency: {int(data.get('urgency_score', 0)*100)}%)")
                    if 'generated_reply' in data:
                        parts.append(f"**Drafted {data.get('reply_tone')} Response:**\n\n> {data['generated_reply']}")
                elif 'synthesis' in data:
                    parts.append(f"**Research Agent Synthesis:** {data['synthesis']}")
                elif 'report_content' in data:
                    parts.append(f"**Report Agent Briefing:**\n{data['report_content']}")
            else:
                parts.append(f"**{agent_name.replace('_', ' ').title()}:** {res.get('error', 'Execution encountered an issue.')}")

        return "\n\n".join(parts) if parts else "Task executed successfully across orchestrated AI agents."

    def _log_execution(self, prompt_str, status, tools, result, exec_time):
        if not self.user_id:
            return
        try:
            summary = result if isinstance(result, str) else json.dumps(result)[:400]
            rec = AgentExecution(
                user_id=self.user_id,
                agent_name=self.NAME,
                prompt=prompt_str[:1000],
                status=status,
                tools_called=json.dumps(tools),
                result_summary=summary[:1000],
                execution_time_ms=exec_time
            )
            db.session.add(rec)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(f"Error logging master agent execution: {ex}")
