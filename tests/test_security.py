from datetime import datetime, timedelta, timezone
from modules.security.analyzer import SecurityAnalyzer

def test_security_analyzer_rules_and_ml():
    now = datetime.now(timezone.utc)
    analyzer = SecurityAnalyzer()

    # Create test transactions with duplicate & high amount
    txs = [
        {
            'id': 'TX1',
            'amount': 50.0,
            'timestamp': (now - timedelta(minutes=40)).isoformat(),
            'sender': 'Alice',
            'recipient': 'Coffee Shop',
            'category': 'Food'
        },
        {
            'id': 'TX2',
            'amount': 15000.0,  # High amount
            'timestamp': (now - timedelta(minutes=20)).isoformat(),
            'sender': 'Alice',
            'recipient': 'Unknown Offshore',
            'category': 'Wire'
        },
        {
            'id': 'TX3',
            'amount': 250.0,
            'timestamp': (now - timedelta(minutes=10)).isoformat(),
            'sender': 'Bob',
            'recipient': 'Crypto Hub',
            'category': 'Crypto'
        },
        {
            'id': 'TX4',
            'amount': 250.0,  # Duplicate of TX3
            'timestamp': (now - timedelta(minutes=5)).isoformat(),
            'sender': 'Bob',
            'recipient': 'Crypto Hub',
            'category': 'Crypto'
        }
    ]

    res = analyzer.analyze_transactions(txs)
    metrics = res['metrics']
    transactions = res['transactions']

    assert metrics['total_transactions'] == 4
    assert metrics['duplicate_count'] >= 1
    
    # High value transaction should be HIGH or MEDIUM risk
    tx_high = next(t for t in transactions if t['external_tx_id'] == 'TX2')
    assert tx_high['risk_level'] in ['HIGH', 'MEDIUM']
    assert tx_high['risk_score'] > 40.0

def test_security_review_endpoint(logged_in_client):
    # Load demo dataset first
    load_res = logged_in_client.post('/api/security/load-demo')
    assert load_res.status_code == 200
    demo_txs = load_res.get_json()['transactions']
    assert len(demo_txs) > 0

    # Get history
    hist_res = logged_in_client.get('/api/security/history')
    assert hist_res.status_code == 200
    saved_txs = hist_res.get_json()['transactions']
    assert len(saved_txs) > 0
    target_id = saved_txs[0]['id']

    # Submit review
    review_res = logged_in_client.post('/api/security/review', json={
        'transaction_id': target_id,
        'decision': 'approved'
    })
    assert review_res.status_code == 200
    assert review_res.get_json()['success'] is True
    assert review_res.get_json()['risk']['review_status'] == 'approved'
