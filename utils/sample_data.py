from datetime import datetime, timedelta, timezone

def get_sample_transactions():
    """
    Returns realistic demonstration transactions containing normal,
    high-amount, duplicate, and velocity-burst test cases.
    Clearly designated as DEMO sample data.
    """
    now = datetime.now(timezone.utc)
    
    return [
        {
            "external_tx_id": "DEMO-TX-101",
            "amount": 42.50,
            "currency": "USD",
            "timestamp": (now - timedelta(hours=5)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Starbucks Coffee #491",
            "category": "Food & Dining",
            "description": "Routine merchant payment"
        },
        {
            "external_tx_id": "DEMO-TX-102",
            "amount": 1250.00,
            "currency": "USD",
            "timestamp": (now - timedelta(hours=4)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Apex Cloud Hosting LLC",
            "category": "Software Infrastructure",
            "description": "Monthly cloud server hosting subscription"
        },
        {
            "external_tx_id": "DEMO-TX-103",
            "amount": 15400.00,
            "currency": "USD",
            "timestamp": (now - timedelta(hours=3, minutes=20)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Offshore Cayman Holdings Corp",
            "category": "Wire Transfer",
            "description": "High-value cross-border wire instruction"
        },
        {
            "external_tx_id": "DEMO-TX-104",
            "amount": 350.00,
            "currency": "USD",
            "timestamp": (now - timedelta(hours=2, minutes=10)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Global Crypto Gateway",
            "category": "Crypto Exchange",
            "description": "Instant digital asset purchase"
        },
        {
            "external_tx_id": "DEMO-TX-105",
            "amount": 350.00,
            "currency": "USD",
            "timestamp": (now - timedelta(hours=2, minutes=5)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Global Crypto Gateway",
            "category": "Crypto Exchange",
            "description": "Instant digital asset purchase (Duplicate detected)"
        },
        {
            "external_tx_id": "DEMO-TX-106",
            "amount": 89.99,
            "currency": "USD",
            "timestamp": (now - timedelta(minutes=45)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "Amazon Retail Inc",
            "category": "Shopping",
            "description": "Office hardware accessories"
        },
        {
            "external_tx_id": "DEMO-TX-107",
            "amount": 490.00,
            "currency": "USD",
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "QuickCash P2P Express",
            "category": "P2P Transfer",
            "description": "Rapid micro-transfer sequence 1"
        },
        {
            "external_tx_id": "DEMO-TX-108",
            "amount": 490.00,
            "currency": "USD",
            "timestamp": (now - timedelta(minutes=12)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "QuickCash P2P Express",
            "category": "P2P Transfer",
            "description": "Rapid micro-transfer sequence 2"
        },
        {
            "external_tx_id": "DEMO-TX-109",
            "amount": 490.00,
            "currency": "USD",
            "timestamp": (now - timedelta(minutes=8)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "QuickCash P2P Express",
            "category": "P2P Transfer",
            "description": "Rapid micro-transfer sequence 3"
        },
        {
            "external_tx_id": "DEMO-TX-110",
            "amount": 490.00,
            "currency": "USD",
            "timestamp": (now - timedelta(minutes=4)).isoformat(),
            "sender": "sarah.miller@example.com",
            "recipient": "QuickCash P2P Express",
            "category": "P2P Transfer",
            "description": "Rapid micro-transfer sequence 4 (Velocity anomaly)"
        }
    ]

def get_sample_emails():
    """
    Returns realistic sample emails for instant testing.
    """
    return [
        {
            "subject": "CRITICAL: Urgent Security Audit & Vendor Remittance Verification",
            "sender": "elena.rostova@cyberguard-fin.com",
            "body": (
                "Hi Team,\n\n"
                "Please be advised that our quarterly external penetration test revealed multiple unexpected outbound wire transfers. "
                "We need you to immediately verify invoice #INV-94021 totaling $18,450.00 with the accounting department before 5:00 PM EST today. "
                "Could you please pull the transaction logs and confirm whether dual authorization was enforced?\n\n"
                "This is urgent and requires your prompt attention to avoid blocking vendor payroll.\n\n"
                "Best regards,\nElena Rostova\nHead of Security Audits"
            )
        },
        {
            "subject": "Q4 Financial Planning & Project Timeline Review",
            "sender": "marcus.vance@vanguard-holdings.io",
            "body": (
                "Good morning,\n\n"
                "I hope your week is off to a productive start. "
                "I have completed the preliminary budget projections for our Q4 AI enablement roadmap. "
                "Overall capital expenditures are trending 12% below budget thanks to the server consolidation work your group completed last month.\n\n"
                "Please review the attached spreadsheet at your convenience and let me know your thoughts before our steering committee meeting on Thursday afternoon.\n\n"
                "Warm regards,\nMarcus"
            )
        },
        {
            "subject": "Exclusive 40% Off: Upgrade your enterprise analytics suite today!",
            "sender": "promotions@datavibe-cloud.com",
            "body": (
                "Hey there!\n\n"
                "Don't miss our limited autumn deal. Sign up for DataVibe Enterprise before midnight and receive an unprecedented 40% discount on annual seats. "
                "Click here to claim your coupon code: AUTUMN40.\n\n"
                "To unsubscribe from marketing alerts, click here."
            )
        }
    ]

def get_sample_document_text():
    """
    Returns a sample corporate financial report text.
    """
    return (
        "CLARIO ENTERPRISE FINANCIAL INTELLIGENCE REPORT - Q3 2026\n"
        "Confidential - For Internal Board Review Only\n\n"
        "1. Executive Overview\n"
        "During the third quarter ending September 30, 2026, CLARIO expanded its unified intelligence platform across 45 enterprise clients. "
        "Total recurring subscription revenue reached $4,250,000, representing a 34% increase quarter-over-quarter. Gross margin held steady at 82.4%.\n\n"
        "2. Key Operational Milestones\n"
        "- On July 15, 2026, the Document Intelligence module processed its 1,000,000th PDF page with 99.4% factual recall precision.\n"
        "- On August 22, 2026, the Transaction Security AI prevented $480,000 in fraudulent cross-border remittances by deploying unsupervised Isolation Forests.\n"
        "- On September 10, 2026, PayPal Sandbox integration was upgraded to full REST v2 compliance with automated webhook idempotency.\n\n"
        "3. Financial Commitments and Deadlines\n"
        "- Next quarterly audit filing deadline: November 15, 2026.\n"
        "- Annual dividend distribution scheduled for December 20, 2026.\n"
        "- Capital expenditure allocation of $850,000 earmarked for GPU infrastructure upgrades through Q1 2027.\n\n"
        "4. Risk Factors\n"
        "Key operational risks include regulatory adherence under evolving AI compliance frameworks and latency spikes during high-concurrency multi-agent orchestration."
    )
