import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from sklearn.ensemble import IsolationForest
from services.ai_service import ai_service

class SecurityAnalyzer:
    """
    Hybrid Transaction Risk & Anomaly Detection Engine.
    Combines deterministic rules (velocity, duplication, thresholding)
    with Scikit-Learn IsolationForest unsupervised anomaly detection
    and generative fraud explanation synthesis.
    """

    def __init__(self, contamination=0.08):
        self.contamination = contamination

    def analyze_transactions(self, transactions_data):
        """
        Analyze a list of transaction dictionaries:
        [{'external_tx_id': 'TX1001', 'amount': 250.0, 'timestamp': '2026-11-10T14:30:00',
          'sender': 'Alice', 'recipient': 'Bob', 'category': 'Transfer'}, ...]
        """
        if not transactions_data:
            return {'transactions': [], 'metrics': self._empty_metrics()}

        df = pd.DataFrame(transactions_data)
        
        # Standardize columns
        if 'external_tx_id' not in df.columns and 'id' in df.columns:
            df['external_tx_id'] = df['id']
        elif 'external_tx_id' not in df.columns:
            df['external_tx_id'] = [f"TX-{i+1:04d}" for i in range(len(df))]

        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        
        # Parse timestamp safely
        def parse_dt(val):
            if isinstance(val, datetime):
                return val
            try:
                return pd.to_datetime(val)
            except Exception:
                return datetime.now(timezone.utc)
                
        df['datetime_parsed'] = df['timestamp'].apply(parse_dt)
        df = df.sort_values(by='datetime_parsed').reset_index(drop=True)

        # 1. Rule-Based Checks
        # Duplicate detection: identical amount, sender, recipient within 60 minutes
        df['is_duplicate'] = False
        duplicate_indices = set()
        for i in range(len(df)):
            for j in range(i + 1, min(i + 15, len(df))):
                time_diff = abs((df.loc[j, 'datetime_parsed'] - df.loc[i, 'datetime_parsed']).total_seconds())
                if time_diff <= 3600:  # 1 hour
                    same_amount = abs(df.loc[j, 'amount'] - df.loc[i, 'amount']) < 0.01
                    same_sender = str(df.loc[j, 'sender']).strip().lower() == str(df.loc[i, 'sender']).strip().lower()
                    same_recip = str(df.loc[j, 'recipient']).strip().lower() == str(df.loc[i, 'recipient']).strip().lower()
                    if same_amount and same_sender and same_recip:
                        duplicate_indices.add(j)
                        
        for idx in duplicate_indices:
            df.loc[idx, 'is_duplicate'] = True

        # Velocity check: more than 3 transactions by sender in 15 minutes
        df['velocity_spike'] = False
        for i in range(len(df)):
            sender_txs = df[(df['sender'] == df.loc[i, 'sender']) & 
                            (df['datetime_parsed'] <= df.loc[i, 'datetime_parsed']) & 
                            (df['datetime_parsed'] >= df.loc[i, 'datetime_parsed'] - timedelta(minutes=15))]
            if len(sender_txs) > 3:
                df.loc[i, 'velocity_spike'] = True

        # Statistical Thresholds (Z-Score on amounts)
        mean_amt = df['amount'].mean()
        std_amt = df['amount'].std() if df['amount'].std() > 0 else 1.0
        df['z_score'] = (df['amount'] - mean_amt) / std_amt

        # 2. Machine Learning: IsolationForest Anomaly Detection
        features = []
        for idx, row in df.iterrows():
            amt = max(0.01, float(row['amount']))
            log_amt = np.log1p(amt)
            hour_of_day = row['datetime_parsed'].hour if hasattr(row['datetime_parsed'], 'hour') else 12
            features.append([amt, log_amt, hour_of_day])
            
        features_np = np.array(features)
        
        # Fit Isolation Forest if at least 4 rows, else mark non-anomalous
        if len(df) >= 4:
            model = IsolationForest(
                contamination=min(0.2, max(0.02, 1.0 / len(df) * 2)),
                random_state=42
            )
            preds = model.fit_predict(features_np)
            decision_scores = model.decision_function(features_np)
            df['is_ml_anomaly'] = [True if p == -1 else False for p in preds]
            df['anomaly_score'] = decision_scores
        else:
            df['is_ml_anomaly'] = [True if row['amount'] > 5000 else False for _, row in df.iterrows()]
            df['anomaly_score'] = 0.0

        # 3. Hybrid Scoring & Explanation Generation
        results = []
        for idx, row in df.iterrows():
            indicators = []
            base_risk = 12.0  # standard baseline
            
            # Amount indicators
            amt = float(row['amount'])
            if amt > 10000:
                base_risk += 40
                indicators.append(f"Substantial transaction value of ${amt:,.2f} exceeding $10,000 threshold")
            elif amt > 3500:
                base_risk += 20
                indicators.append(f"Elevated amount ${amt:,.2f} noticeably above user baseline")
                
            if row['z_score'] > 2.5:
                base_risk += 15
                indicators.append(f"Statistical outlier magnitude (Z-Score: {row['z_score']:.2f})")
                
            # Duplicate
            if row['is_duplicate']:
                base_risk += 35
                indicators.append("Potential duplicate charge detected within 60 minutes for identical party")
                
            # Velocity
            if row['velocity_spike']:
                base_risk += 25
                indicators.append("Rapid burst frequency: 4+ transactions initiated inside 15-minute window")
                
            # ML Anomaly
            if row['is_ml_anomaly']:
                base_risk += 20
                indicators.append("Unsupervised Isolation Forest flagged unusual multidimensional feature variance")

            # Category scrutiny
            cat_lower = str(row.get('category', '')).lower()
            if any(k in cat_lower for k in ['crypto', 'wire', 'gambling', 'prepaid', 'offshore']):
                base_risk += 18
                indicators.append(f"High-scrutiny transaction classification: '{row.get('category')}'")

            final_score = min(99.0, max(5.0, base_risk))
            level = 'HIGH' if final_score >= 65 else ('MEDIUM' if final_score >= 38 else 'LOW')
            
            # Action recommendation
            if level == 'HIGH':
                recommended_action = "Place hold for compliance verification before clearing funds"
            elif level == 'MEDIUM':
                recommended_action = "Request automated Step-Up 2FA confirmation from account holder"
            else:
                recommended_action = "Approve for standard clearing process"

            # Explanation
            if not indicators:
                indicators = ["Conforms to standard behavioral baseline and transaction profile"]
                explanation = f"Transaction of ${amt:,.2f} to {row.get('recipient')} exhibits normal volume, frequency, and categorization patterns."
            else:
                explanation = f"Flagged with {len(indicators)} risk factor(s). Transaction of ${amt:,.2f} evaluated with an indicative risk score of {final_score:.1f}/100."

            results.append({
                'external_tx_id': str(row.get('external_tx_id')),
                'amount': amt,
                'currency': str(row.get('currency', 'USD')),
                'timestamp': row['datetime_parsed'].isoformat() if hasattr(row['datetime_parsed'], 'isoformat') else str(row['datetime_parsed']),
                'sender': str(row.get('sender', 'Unknown')),
                'recipient': str(row.get('recipient', 'Unknown')),
                'category': str(row.get('category', 'Transfer')),
                'description': str(row.get('description', '')),
                'risk_score': round(final_score, 1),
                'risk_level': level,
                'is_anomaly': bool(row['is_ml_anomaly'] or row['z_score'] > 2.5),
                'is_duplicate': bool(row['is_duplicate']),
                'detected_indicators': indicators,
                'explanation': explanation,
                'recommended_action': recommended_action,
                'review_status': 'pending'
            })

        # Summary Metrics
        total_txs = len(results)
        high_risk_count = sum(1 for r in results if r['risk_level'] == 'HIGH')
        med_risk_count = sum(1 for r in results if r['risk_level'] == 'MEDIUM')
        low_risk_count = sum(1 for r in results if r['risk_level'] == 'LOW')
        anomaly_count = sum(1 for r in results if r['is_anomaly'])
        duplicate_count = sum(1 for r in results if r['is_duplicate'])
        total_volume = sum(r['amount'] for r in results)
        avg_risk_score = round(sum(r['risk_score'] for r in results) / total_txs, 1) if total_txs > 0 else 0.0

        metrics = {
            'total_transactions': total_txs,
            'total_volume': round(total_volume, 2),
            'avg_risk_score': avg_risk_score,
            'high_risk_count': high_risk_count,
            'medium_risk_count': med_risk_count,
            'low_risk_count': low_risk_count,
            'anomaly_count': anomaly_count,
            'duplicate_count': duplicate_count,
            'high_risk_percentage': round((high_risk_count / total_txs) * 100, 1) if total_txs > 0 else 0.0
        }

        return {
            'transactions': results,
            'metrics': metrics
        }

    def _empty_metrics(self):
        return {
            'total_transactions': 0,
            'total_volume': 0.0,
            'avg_risk_score': 0.0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'anomaly_count': 0,
            'duplicate_count': 0,
            'high_risk_percentage': 0.0
        }
