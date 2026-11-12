import time
import json
from models import db
from models.models import Transaction, RiskResult, AgentExecution
from modules.security.analyzer import SecurityAnalyzer
from utils.sample_data import get_sample_transactions

class SecurityAgent:
    """
    Security Specialist Agent:
    Scans transaction batches for duplicate charges, rapid velocity bursts,
    unusual amounts, and IsolationForest ML anomalies.
    """

    NAME = "security_agent"
    DESCRIPTION = "Audits financial transactions, calculates risk scores, and detects payment anomalies."

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.analyzer = SecurityAnalyzer()

    def execute(self, task_payload):
        start_time = time.time()
        transactions_data = task_payload.get('transactions')
        load_demo = task_payload.get('load_demo', False)
        batch_id = task_payload.get('batch_id', f"BATCH-{int(time.time())}")

        tools_called = []
        result = {}

        try:
            if load_demo or not transactions_data:
                # If user has saved transactions in database, check for them first unless demo requested
                if not load_demo and self.user_id:
                    user_tx_objs = Transaction.query.filter_by(user_id=self.user_id).all()
                    if user_tx_objs:
                        tools_called.append('retrieve_user_transactions_from_db')
                        transactions_data = [
                            {
                                'external_tx_id': t.external_tx_id,
                                'amount': t.amount,
                                'currency': t.currency,
                                'timestamp': t.timestamp.isoformat() if t.timestamp else '',
                                'sender': t.sender,
                                'recipient': t.recipient,
                                'category': t.category,
                                'description': t.description
                            }
                            for t in user_tx_objs
                        ]

                if not transactions_data:
                    tools_called.append('load_demo_sample_dataset')
                    transactions_data = get_sample_transactions()

            tools_called.append('validate_transaction_schema')
            tools_called.append('rule_based_duplicate_and_velocity_scan')
            tools_called.append('scikit_learn_isolation_forest_anomaly_detection')
            
            analysis_result = self.analyzer.analyze_transactions(transactions_data)
            flagged = [t for t in analysis_result['transactions'] if t['risk_level'] in ['MEDIUM', 'HIGH']]

            # Persist if requested and user is authenticated
            if task_payload.get('persist', True) and self.user_id:
                tools_called.append('persist_transactions_and_risk_evaluations')
                for item in analysis_result['transactions']:
                    tx = Transaction(
                        user_id=self.user_id,
                        batch_id=batch_id,
                        external_tx_id=item['external_tx_id'],
                        amount=item['amount'],
                        currency=item.get('currency', 'USD'),
                        timestamp=pd_parse_date(item['timestamp']),
                        sender=item['sender'],
                        recipient=item['recipient'],
                        category=item['category'],
                        description=item.get('description', '')
                    )
                    db.session.add(tx)
                    db.session.flush()

                    risk = RiskResult(
                        transaction_id=tx.id,
                        user_id=self.user_id,
                        risk_score=item['risk_score'],
                        risk_level=item['risk_level'],
                        is_anomaly=item['is_anomaly'],
                        is_duplicate=item['is_duplicate'],
                        detected_indicators=json.dumps(item['detected_indicators']),
                        explanation=item['explanation'],
                        recommended_action=item['recommended_action'],
                        review_status='pending'
                    )
                    db.session.add(risk)
                db.session.commit()

            result = {
                'agent': self.NAME,
                'batch_id': batch_id,
                'metrics': analysis_result['metrics'],
                'total_analyzed': len(analysis_result['transactions']),
                'flagged_count': len(flagged),
                'flagged_transactions': flagged[:10],
                'summary': (
                    f"Security Agent evaluated {len(analysis_result['transactions'])} transactions. "
                    f"Identified {len(flagged)} transactions requiring oversight: "
                    f"{analysis_result['metrics']['high_risk_count']} HIGH risk, "
                    f"{analysis_result['metrics']['medium_risk_count']} MEDIUM risk, and "
                    f"{analysis_result['metrics']['duplicate_count']} potential duplicate charges."
                )
            }

            execution_time = int((time.time() - start_time) * 1000)
            self._log_execution(task_payload, 'completed', tools_called, result, execution_time)
            return {'status': 'completed', 'data': result, 'tools_called': tools_called, 'execution_time_ms': execution_time}

        except Exception as e:
            db.session.rollback()
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
            print(f"Error logging security agent execution: {ex}")

def pd_parse_date(val):
    from datetime import datetime, timezone
    if isinstance(val, datetime):
        return val
    try:
        from dateutil import parser
        return parser.parse(str(val))
    except Exception:
        return datetime.now(timezone.utc)
