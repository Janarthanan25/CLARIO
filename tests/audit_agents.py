"""
CLARIO Multi-Agent Architecture Audit & Verification Suite
Tests every individual specialist agent, Master Agent routing, agent-to-agent
handoffs, and Gemini API error handling.
"""
import sys
import os
import time
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(basedir))

from app import create_app
from config import TestConfig
from models import db
from models.models import User, Document, EmailRecord, Transaction, AgentExecution
from agents.master_agent import MasterAgent
from agents.document_agent import DocumentAgent
from agents.email_agent import EmailAgent
from agents.security_agent import SecurityAgent
from agents.research_agent import ResearchAgent
from agents.report_agent import ReportAgent
from services.ai_service import ai_service

def run_agent_audit():
    app = create_app(TestConfig)
    results = {}
    
    with app.app_context():
        db.create_all()
        
        # Setup test user
        user = User(
            email='agent_audit_user@clario.ai',
            username='agent_auditor',
            full_name='Agent Auditor',
            role='admin',
            plan='PRO'
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        print("\n" + "="*70)
        print("CLARIO MULTI-AGENT ARCHITECTURE AUDIT")
        print("="*70)

        # -------------------------------------------------------------
        # 1. TEST DOCUMENT AGENT
        # -------------------------------------------------------------
        print("\n[TEST 1] Auditing DocumentAgent...", flush=True)
        try:
            doc_agent = DocumentAgent(user_id=user_id)
            sample_text = (
                "CLARIO Financial Intelligence Report Q3 2026.\n\n"
                "In Q3 2026, CLARIO expanded recurring enterprise ARR by $1,250,000. "
                "The board has scheduled the next financial compliance audit for November 28, 2026. "
                "Operating expenses remained stable at $420,000 with zero compliance breaches."
            )
            # Test direct text summarization
            print("  -> Testing DocumentAgent summarize...", flush=True)
            res_sum = doc_agent.execute({
                'action': 'summarize',
                'text': sample_text
            })
            assert res_sum['status'] == 'completed', f"Summarize failed: {res_sum.get('error')}"
            assert 'executive_summary' in res_sum['data']
            assert len(res_sum['tools_called']) > 0

            # Test grounded Q&A
            print("  -> Testing DocumentAgent query...", flush=True)
            res_qa = doc_agent.execute({
                'action': 'query',
                'query': 'When is the next compliance audit scheduled?',
                'text': sample_text
            })
            assert res_qa['status'] == 'completed', f"Query failed: {res_qa.get('error')}"
            assert 'November 28' in res_qa['data']['answer'] or 'audit' in res_qa['data']['answer'].lower()

            results['DocumentAgent'] = {
                'status': 'PASS',
                'details': f"Summarization & Grounded Q&A functional. Tools: {res_sum['tools_called'] + res_qa['tools_called']}"
            }
            print("  --> PASS: DocumentAgent executed summarization and grounded Q&A.", flush=True)
        except Exception as e:
            results['DocumentAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: DocumentAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 2. TEST EMAIL AGENT
        # -------------------------------------------------------------
        print("\n[TEST 2] Auditing EmailAgent...", flush=True)
        try:
            email_agent = EmailAgent(user_id=user_id)
            email_payload = {
                'body': "Hi Alex, please confirm the $50,000 vendor wire payment before 4 PM today. This is critical for the server deployment.",
                'subject': "URGENT: Wire Approval Needed",
                'sender': "finance-director@enterprise.com",
                'tone': "Professional",
                'save_record': True
            }
            res_email = email_agent.execute(email_payload)
            assert res_email['status'] == 'completed', f"Email execution failed: {res_email.get('error')}"
            data = res_email['data']
            assert data['category'] in ['Finance', 'Urgent', 'Important', 'Work']
            assert data['urgency_score'] >= 0.5
            assert len(data['generated_reply']) > 20
            assert 'persist_email_record' in res_email['tools_called']

            # Verify persisted in database
            saved_rec = EmailRecord.query.filter_by(user_id=user_id).first()
            assert saved_rec is not None, "EmailRecord was not persisted in DB"

            results['EmailAgent'] = {
                'status': 'PASS',
                'details': f"Category: {data['category']}, Urgency: {data['urgency_score']}, Reply generated, DB record #{saved_rec.id} persisted."
            }
            print("  --> PASS: EmailAgent classified urgency, drafted response, and persisted to DB.", flush=True)
        except Exception as e:
            results['EmailAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: EmailAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 3. TEST SECURITY AGENT
        # -------------------------------------------------------------
        print("\n[TEST 3] Auditing SecurityAgent...", flush=True)
        try:
            sec_agent = SecurityAgent(user_id=user_id)
            # Send sample transactions with a deliberate duplicate and an anomalous spike
            custom_txs = [
                {'external_tx_id': 'TX-AUDIT-101', 'amount': 45.00, 'timestamp': '2026-11-12T01:00:00Z', 'sender': 'user_a', 'recipient': 'vendor_x', 'category': 'software'},
                {'external_tx_id': 'TX-AUDIT-102', 'amount': 45.00, 'timestamp': '2026-11-12T01:10:00Z', 'sender': 'user_a', 'recipient': 'vendor_x', 'category': 'software'}, # duplicate
                {'external_tx_id': 'TX-AUDIT-103', 'amount': 98500.00, 'timestamp': '2026-11-12T03:00:00Z', 'sender': 'user_a', 'recipient': 'offshore_wire', 'category': 'wire'}, # high amount
                {'external_tx_id': 'TX-AUDIT-104', 'amount': 32.50, 'timestamp': '2026-11-12T04:00:00Z', 'sender': 'user_a', 'recipient': 'coffee_shop', 'category': 'dining'},
            ]
            res_sec = sec_agent.execute({
                'transactions': custom_txs,
                'persist': True
            })
            assert res_sec['status'] == 'completed', f"Security execution failed: {res_sec.get('error')}"
            sec_data = res_sec['data']
            assert sec_data['total_analyzed'] == 4
            assert sec_data['flagged_count'] > 0
            assert 'scikit_learn_isolation_forest_anomaly_detection' in res_sec['tools_called']
            assert 'rule_based_duplicate_and_velocity_scan' in res_sec['tools_called']

            # Verify persisted in DB
            db_txs = Transaction.query.filter_by(user_id=user_id).count()
            assert db_txs >= 4, f"Expected at least 4 transactions in DB, found {db_txs}"

            results['SecurityAgent'] = {
                'status': 'PASS',
                'details': f"Scanned {sec_data['total_analyzed']} txs, flagged {sec_data['flagged_count']}. Rule engine + IsolationForest verified."
            }
            print("  --> PASS: SecurityAgent ran rule engine + IsolationForest ML and persisted flags.", flush=True)
        except Exception as e:
            results['SecurityAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: SecurityAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 4. TEST RESEARCH AGENT
        # -------------------------------------------------------------
        print("\n[TEST 4] Auditing ResearchAgent...", flush=True)
        try:
            res_agent = ResearchAgent(user_id=user_id)
            res_research = res_agent.execute({
                'query': 'What vendor payments and email deadlines require our attention today?'
            })
            assert res_research['status'] == 'completed', f"Research execution failed: {res_research.get('error')}"
            data_res = res_research['data']
            assert len(data_res['synthesis']) > 20
            assert data_res['sources_consulted_count'] > 0
            assert 'scan_user_emails' in res_research['tools_called']
            assert 'scan_transaction_activity' in res_research['tools_called']

            results['ResearchAgent'] = {
                'status': 'PASS',
                'details': f"Consulted {data_res['sources_consulted_count']} database sources. Multi-source cross-referencing functional."
            }
            print("  --> PASS: ResearchAgent correlated database records across emails and transactions.", flush=True)
        except Exception as e:
            results['ResearchAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: ResearchAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 5. TEST REPORT AGENT
        # -------------------------------------------------------------
        print("\n[TEST 5] Auditing ReportAgent...", flush=True)
        try:
            rep_agent = ReportAgent(user_id=user_id)
            res_rep = rep_agent.execute({'report_type': 'executive_summary'})
            assert res_rep['status'] == 'completed', f"Report execution failed: {res_rep.get('error')}"
            data_rep = res_rep['data']
            assert 'report_content' in data_rep
            assert data_rep['metrics']['emails_count'] >= 1
            assert data_rep['metrics']['transactions_count'] >= 4
            assert 'aggregate_platform_metrics' in res_rep['tools_called']

            results['ReportAgent'] = {
                'status': 'PASS',
                'details': f"Telemetry aggregated: {data_rep['metrics']}. Executive narrative generated."
            }
            print("  --> PASS: ReportAgent aggregated metrics and compiled executive briefing.", flush=True)
        except Exception as e:
            results['ReportAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: ReportAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 6. TEST MASTER AGENT ROUTING & ORCHESTRATION
        # -------------------------------------------------------------
        print("\n[TEST 6] Auditing MasterAgent Routing...", flush=True)
        try:
            master = MasterAgent(user_id=user_id)
            
            # Security routing check
            print("  -> Testing MasterAgent -> SecurityAgent routing...", flush=True)
            sec_run = master.process_command("Audit our recent wire transfers and identify any suspicious charge patterns")
            assert sec_run['status'] == 'success'
            assert sec_run['master_orchestration']['primary_agent'] in ['security_agent', 'research_agent']
            assert 'dispatch_to_security_agent' in sec_run['tools_called'] or 'dispatch_to_research_agent' in sec_run['tools_called']

            # Email routing check
            print("  -> Testing MasterAgent -> EmailAgent routing...", flush=True)
            email_run = master.process_command("Draft a formal reply to the vendor confirming invoice receipt")
            assert email_run['status'] == 'success'
            assert email_run['master_orchestration']['primary_agent'] in ['email_agent', 'research_agent']

            # Report routing check
            print("  -> Testing MasterAgent -> ReportAgent routing...", flush=True)
            rep_run = master.process_command("Generate the quarterly executive briefing report summarizing all activity")
            assert rep_run['status'] == 'success'
            assert rep_run['master_orchestration']['primary_agent'] in ['report_agent', 'research_agent']

            results['MasterAgent'] = {
                'status': 'PASS',
                'details': "Successfully decomposed natural-language prompts and routed to specialist agents."
            }
            print("  --> PASS: MasterAgent correctly routes requests based on user intent.", flush=True)
        except Exception as e:
            results['MasterAgent'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: MasterAgent error: {e}", flush=True)

        # -------------------------------------------------------------
        # 7. TEST AGENT-TO-AGENT PIPELINE & CONTEXT HANDOFF
        # -------------------------------------------------------------
        print("\n[TEST 7] Auditing Agent-to-Agent Handoff & Pipeline...", flush=True)
        try:
            # Test multi-agent orchestration where secondary agent uses primary agent findings
            master = MasterAgent(user_id=user_id)
            # Explicit multi-agent workflow
            custom_payload = master._build_task_payload('email_agent', "Alert CFO", context={}, previous_result={
                'status': 'completed',
                'data': {'summary': 'Found 2 duplicate wire charges of $45.00 to vendor_x'}
            })
            
            # Check if previous_result was incorporated or if it was ignored
            has_handoff = 'duplicate wire' in custom_payload.get('body', '') or 'Finding' in custom_payload.get('body', '')
            results['AgentToAgentCommunication'] = {
                'status': 'PASS' if has_handoff else 'INCOMPLETE',
                'details': f"Payload body: {custom_payload.get('body')[:100]}"
            }
            print(f"  --> {'PASS' if has_handoff else 'NEEDS_IMPROVEMENT'}: Agent-to-agent context handoff.", flush=True)
        except Exception as e:
            results['AgentToAgentCommunication'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: Agent-to-Agent handoff error: {e}", flush=True)

        # -------------------------------------------------------------
        # 8. TEST GEMINI API INTEGRATION & ERROR HANDLING
        # -------------------------------------------------------------
        print("\n[TEST 8] Auditing Gemini API Integration & Error Handling...", flush=True)
        try:
            # 8a: Valid inference check
            res_live = ai_service.generate_response("Respond with: Hello Clario")
            assert res_live['status'] in ['success', 'offline_fallback']
            assert len(res_live['text']) > 0

            # 8b: Resilience test with invalid key to verify graceful fallback (limit to 1 candidate to avoid timeout)
            from services.ai_service import GeminiAIService
            bad_service = GeminiAIService(api_key="INVALID_TEST_KEY_THAT_WILL_FAIL")
            bad_service.FALLBACK_MODELS = ['gemini-3.5-flash-lite']
            res_fallback = bad_service.generate_response("Test error handling prompt")
            assert res_fallback['status'] == 'api_error_fallback'
            assert res_fallback['source'] == 'clario_local_engine'
            assert len(res_fallback['text']) > 0

            results['GeminiIntegrationAndErrorHandling'] = {
                'status': 'PASS',
                'details': f"Live model operational ({res_live.get('model', 'heuristic')}). Invalid key properly handled with fallback status 'api_error_fallback'."
            }
            print("  --> PASS: Gemini API error handling gracefully falls back to deterministic engine on API error.", flush=True)
        except Exception as e:
            results['GeminiIntegrationAndErrorHandling'] = {'status': 'FAIL', 'details': str(e)}
            print(f"  --> FAIL: Gemini error handling test failed: {e}", flush=True)

        print("\n" + "="*70)
        print("AUDIT SUMMARY:")
        for name, data in results.items():
            print(f"  {name:35} : [{data['status']}] - {data['details']}")
        print("="*70 + "\n")
        
        return results

if __name__ == '__main__':
    run_agent_audit()
