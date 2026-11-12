import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
basedir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(basedir))
load_dotenv(basedir / '.env', override=True)

from app import app
from services.ai_service import ai_service

def verify_live_gemini():
    with app.app_context():
        print("1. Checking API Key Configuration...")
        key = ai_service._get_api_key()
        if not key:
            print("ERROR: GEMINI_API_KEY not found in environment!")
            sys.exit(1)
        
        masked = f"{key[:4]}...{key[-4:]}"
        print(f"API Key detected successfully: {masked} (length: {len(key)})")
        print(f"Primary Model configured: {ai_service._get_model()}")

        print("\n2. Testing live generate_response()...")
        res = ai_service.generate_response("Respond with exactly: CLARIO AI Engine is online and operational.")
        print(f"Status: {res.get('status')}")
        print(f"Source: {res.get('source')}")
        print(f"Model used: {res.get('model')}")
        print(f"Response: {res.get('text').strip()[:120]}")
        
        if res.get('source') != 'gemini_live':
            print("FAIL: Expected source == 'gemini_live'")
            sys.exit(1)

        print("\n3. Testing live summarize_document() with structured JSON mode...")
        sample_doc = "CLARIO FinTech Audit: In Q3, $12,450 was flagged as duplicate wire remittances. Board review scheduled for Dec 1, 2026."
        doc_summary = ai_service.summarize_document(sample_doc, "Audit_Q3.txt")
        print(f"Document Summary Source: {doc_summary.get('ai_source')}")
        print(f"Executive Summary: {doc_summary.get('executive_summary')}")
        print(f"Key Dates detected: {doc_summary.get('key_dates')}")

        if doc_summary.get('ai_source') != 'gemini_live':
            print("FAIL: Expected document summary source == 'gemini_live'")
            sys.exit(1)

        print("\n4. Testing live analyze_email()...")
        email_body = "Hi team, please verify invoice #94021 by 5pm today. Very urgent."
        email_res = ai_service.analyze_email(email_body, subject="Urgent Invoice")
        print(f"Email Analysis Source: {email_res.get('ai_source')}")
        print(f"Category: {email_res.get('category')}")
        print(f"Urgency Score: {email_res.get('urgency_score')}")

        if email_res.get('ai_source') != 'gemini_live':
            print("FAIL: Expected email analysis source == 'gemini_live'")
            sys.exit(1)

        print("\n--> ALL REAL GEMINI API INFERENCES VERIFIED LIVE AND OPERATIONAL! <--")

if __name__ == '__main__':
    verify_live_gemini()
