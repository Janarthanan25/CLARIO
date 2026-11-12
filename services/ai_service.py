import os
import json
import re
import logging
import requests
from flask import current_app

logger = logging.getLogger('clario.ai_service')

class GeminiAIService:
    """
    Robust Google Gemini AI Integration Service.
    Supports official REST endpoints for Gemini models (e.g. gemini-3.5-flash-lite)
    with JSON mode, structured prompting, automatic model fallback on spikes/deprecations,
    and graceful deterministic fallback when API keys are missing or offline.
    """

    FALLBACK_MODELS = [
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
        'gemini-flash-lite-latest',
        'gemini-3.1-flash-lite'
    ]

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key
        self.model = model
        self.api_url_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    def _get_api_key(self):
        if self.api_key:
            return self.api_key
        if current_app:
            return current_app.config.get('GEMINI_API_KEY', '').strip()
        return os.environ.get('GEMINI_API_KEY', '').strip()

    def _get_model(self):
        if self.model and self.model not in ['gemini-1.5-flash', 'gemini-2.5-flash']:
            return self.model
        if current_app and current_app.config.get('GEMINI_MODEL'):
            conf_model = current_app.config.get('GEMINI_MODEL').strip()
            if conf_model not in ['gemini-1.5-flash', 'gemini-2.5-flash']:
                return conf_model
        env_model = os.environ.get('GEMINI_MODEL', '').strip()
        if env_model and env_model not in ['gemini-1.5-flash', 'gemini-2.5-flash']:
            return env_model
        return 'gemini-3.5-flash-lite'

    def _get_candidate_models(self):
        primary = self._get_model()
        candidates = [primary]
        for m in self.FALLBACK_MODELS:
            if m not in candidates:
                candidates.append(m)
        return candidates

    def is_live_configured(self):
        key = self._get_api_key()
        return bool(key and len(key) > 10)

    def generate_response(self, prompt, system_instruction=None, json_format=False):
        """
        Query Gemini API with automatic model failover or fall back to high-grade deterministic synthesis.
        """
        api_key = self._get_api_key()
        
        if not api_key:
            return {
                'text': self._heuristic_generate_fallback(prompt, system_instruction, json_format),
                'source': 'clario_local_engine',
                'status': 'offline_fallback',
                'notice': 'Running with Clario local intelligence engine. Add GEMINI_API_KEY in Settings or .env for live Gemini API.'
            }

        headers = {'Content-Type': 'application/json'}
        contents = [{"parts": [{"text": prompt}]}]
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2 if json_format else 0.7,
                "topP": 0.8,
                "maxOutputTokens": 2048,
            }
        }
        
        if json_format:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        candidate_models = self._get_candidate_models()
        last_error_msg = None

        for target_model in candidate_models:
            url = self.api_url_template.format(model=target_model, key=api_key)
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts:
                            text_output = parts[0].get('text', '')
                            logger.info(f"[CLARIO GEMINI API] Live generation successful using model '{target_model}'.")
                            return {
                                'text': text_output,
                                'source': 'gemini_live',
                                'status': 'success',
                                'model': target_model
                            }
                
                # If non-200, extract and log the actual error message safely (without exposing key)
                try:
                    error_json = response.json().get('error', {})
                    last_error_msg = error_json.get('message', f'HTTP {response.status_code}')
                except Exception:
                    last_error_msg = f'HTTP {response.status_code}'
                    
                logger.warning(
                    f"[CLARIO GEMINI API ERROR] Model '{target_model}' returned HTTP {response.status_code}: {last_error_msg}. "
                    f"Attempting next candidate..."
                )

            except Exception as conn_err:
                last_error_msg = str(conn_err)
                logger.warning(f"[CLARIO GEMINI API CONNECTION ERROR] Model '{target_model}' connection error: {conn_err}")

        # If all candidates exhausted, log error and return deterministic analysis
        logger.error(f"[CLARIO GEMINI API EXHAUSTED] All candidate models failed. Last error: {last_error_msg}")
        return {
            'text': self._heuristic_generate_fallback(prompt, system_instruction, json_format),
            'source': 'clario_local_engine',
            'status': 'api_error_fallback',
            'notice': f'Gemini API error ({last_error_msg}). Returned Clario deterministic analysis.'
        }

    def summarize_document(self, text, doc_name=None):
        """
        Summarize document and extract key dates, figures, and topics.
        """
        cleaned_text = (text or '').strip()
        api_key = self._get_api_key()
        if not api_key:
            return self._heuristic_document_summary(cleaned_text, doc_name, 'clario_local_engine', 'Analyzed using Clario deterministic document intelligence.')

        doc_sample = cleaned_text[:12000] # Safe chunk
        
        system_instruction = (
            "You are CLARIO Document Agent, an expert document analyst. "
            "Analyze the provided document text accurately. Output ONLY valid JSON with keys: "
            "'executive_summary', 'key_points' (array of strings), 'key_dates' (array of strings/dates), "
            "'key_entities' (object with people, organizations, financial_terms), 'document_type_detected'."
        )
        prompt = f"Document: {doc_name or 'Uploaded Document'}\n\nContent:\n{doc_sample}"
        
        res = self.generate_response(prompt, system_instruction=system_instruction, json_format=True)
        try:
            structured = self._clean_json(res['text'])
            structured['ai_source'] = res['source']
            structured['notice'] = res.get('notice')
            return structured
        except Exception:
            # Fallback deterministic extractor
            return self._heuristic_document_summary(cleaned_text, doc_name, res.get('source'), res.get('notice'))

    def analyze_email(self, body, subject=None, sender=None):
        """
        Analyze email category, sentiment, urgency, action items, and deadlines.
        """
        api_key = self._get_api_key()
        if not api_key:
            return self._heuristic_email_analysis(body, subject, sender, 'clario_local_engine', 'Analyzed using Clario email intelligence heuristics.')

        system_instruction = (
            "You are CLARIO Smart Email Assistant. Analyze incoming emails. "
            "Output ONLY valid JSON with keys: 'category' (one of: Important, Work, Personal, Finance, Promotions, Urgent), "
            "'sentiment' (Positive, Neutral, Negative), 'urgency_score' (0.0 to 1.0), "
            "'summary' (concise 1-2 sentence overview), 'tasks' (list of action items), "
            "'deadlines' (list of mentioned dates/deadlines), 'suggested_tones' (list of 3 suggested tones)."
        )
        prompt = f"Subject: {subject or 'No Subject'}\nFrom: {sender or 'Unknown'}\n\nBody:\n{body}"
        
        res = self.generate_response(prompt, system_instruction=system_instruction, json_format=True)
        try:
            structured = self._clean_json(res['text'])
            structured['ai_source'] = res['source']
            structured['notice'] = res.get('notice')
            return structured
        except Exception:
            return self._heuristic_email_analysis(body, subject, sender, res.get('source'), res.get('notice'))

    def generate_email_reply(self, email_body, tone='Professional', custom_instruction=None):
        """
        Generate contextual email reply matching specified tone.
        """
        system_instruction = (
            f"You are CLARIO Smart Email Assistant. Compose a complete, ready-to-send email response. "
            f"Tone: {tone}. Maintain high emotional intelligence and clarity."
        )
        prompt = f"Original Email:\n{email_body}\n\nTone Requested: {tone}\nAdditional Instructions: {custom_instruction or 'None'}"
        
        res = self.generate_response(prompt, system_instruction=system_instruction, json_format=False)
        return {
            'reply': res['text'],
            'tone': tone,
            'source': res['source'],
            'notice': res.get('notice')
        }

    def analyze_transaction(self, tx_data):
        """
        Evaluate transaction security indicators and generate human-readable security explanation.
        """
        api_key = self._get_api_key()
        if not api_key:
            return self._heuristic_transaction_analysis(tx_data, 'clario_local_engine', 'Evaluated using Clario rule-based risk profiling engine.')

        system_instruction = (
            "You are CLARIO Security AI. Evaluate financial transaction risk factors. "
            "Output ONLY valid JSON with keys: 'risk_score' (number 0-100), "
            "'risk_level' ('LOW', 'MEDIUM', 'HIGH'), 'detected_indicators' (array of strings), "
            "'explanation' (clear reasoning for risk determination), 'recommended_action' (concrete remediation step)."
        )
        prompt = f"Transaction details:\n{json.dumps(tx_data, indent=2)}"
        
        res = self.generate_response(prompt, system_instruction=system_instruction, json_format=True)
        try:
            structured = self._clean_json(res['text'])
            structured['ai_source'] = res['source']
            structured['notice'] = res.get('notice')
            return structured
        except Exception:
            return self._heuristic_transaction_analysis(tx_data, res.get('source'), res.get('notice'))

    def orchestrate_agents(self, user_request, context_data=None):
        """
        Master agent reasoning step: routes request, selects tools, and coordinates specialists.
        """
        api_key = self._get_api_key()
        if not api_key:
            return self._heuristic_orchestration(user_request, 'clario_local_engine', 'Master Agent routed via Clario intention-dispatch matrix.')

        system_instruction = (
            "You are CLARIO Master Orchestrator Agent. Your task is to interpret user requests "
            "and determine which specialist agent should handle it. "
            "Specialist agents: 'document_agent', 'email_agent', 'security_agent', 'research_agent', 'report_agent'. "
            "Output ONLY valid JSON with keys: 'intent', 'primary_agent', 'secondary_agents' (array), "
            "'reasoning', 'required_tools' (array), 'immediate_answer_or_plan'."
        )
        prompt = f"User Request: {user_request}\nAvailable Context: {json.dumps(context_data or {})}"
        
        res = self.generate_response(prompt, system_instruction=system_instruction, json_format=True)
        try:
            structured = self._clean_json(res['text'])
            structured['ai_source'] = res['source']
            structured['notice'] = res.get('notice')
            return structured
        except Exception:
            return self._heuristic_orchestration(user_request, res.get('source'), res.get('notice'))

    # Helper JSON cleaning
    def _clean_json(self, text):
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json", 1)[1]
            if "```" in clean:
                clean = clean.split("```", 1)[0]
        elif "```" in clean:
            clean = clean.split("```", 1)[1]
            if "```" in clean:
                clean = clean.split("```", 1)[0]
        clean = clean.strip()
        # Extract bounded JSON object or array
        start = -1
        for i, ch in enumerate(clean):
            if ch in ['{', '[']:
                start = i
                break
        if start != -1:
            end = max(clean.rfind('}'), clean.rfind(']'))
            if end != -1 and end > start:
                clean = clean[start:end+1]
        return json.loads(clean)

    # Deterministic Heuristic Fallbacks (when Gemini API key is unset or offline)
    def _heuristic_generate_fallback(self, prompt, system_instruction, json_format):
        prompt_lower = prompt.lower()
        if json_format:
            if "category" in prompt_lower or "email" in prompt_lower:
                return json.dumps({
                    "category": "Work",
                    "sentiment": "Neutral",
                    "urgency_score": 0.45,
                    "summary": "Email received regarding business operations.",
                    "tasks": ["Review details", "Prepare response"],
                    "deadlines": ["Within 48 hours"],
                    "suggested_tones": ["Professional", "Formal", "Friendly"]
                })
            elif "risk_score" in prompt_lower or "transaction" in prompt_lower:
                return json.dumps({
                    "risk_score": 35.0,
                    "risk_level": "LOW",
                    "detected_indicators": ["Standard transaction volume", "Verified account"],
                    "explanation": "Transaction parameters conform to typical behavioral profiles with low variance.",
                    "recommended_action": "Standard processing. No manual approval required."
                })
            elif "primary_agent" in prompt_lower or "orchestrator" in prompt_lower:
                return json.dumps({
                    "intent": "general_inquiry",
                    "primary_agent": "document_agent",
                    "secondary_agents": ["report_agent"],
                    "reasoning": "Determined best routing path based on query terms.",
                    "required_tools": ["search_workspace", "summarize"],
                    "immediate_answer_or_plan": "Coordinating specialist agents to fulfill your request."
                })
            else:
                return json.dumps({
                    "status": "processed",
                    "result": f"Synthesized analysis for query: {prompt[:80]}"
                })
        return f"CLARIO AI Analysis:\n\nRegarding your request ('{prompt[:100]}...'), the unified intelligence platform has processed the context. For extended multimodal reasoning and live model inference, please ensure GEMINI_API_KEY is configured in your platform settings."

    def _heuristic_document_summary(self, text, doc_name, source, notice):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        first_few = " ".join(lines[:6]) if lines else "Document uploaded to Clario Workspace."
        
        # Regex date finding
        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b', text, re.IGNORECASE)
        # Regex currency finding
        money = re.findall(r'[\$€£]\s?\d+(?:,\d{3})*(?:\.\d{2})?', text)
        
        return {
            'executive_summary': f"Document '{doc_name or 'Uploaded File'}' contains approximately {len(text.split())} words. Key overview: {first_few[:300]}...",
            'key_points': [
                f"Total text extracted: {len(text)} characters across {len(lines)} structured paragraphs.",
                f"Identified {len(dates)} temporal markers and {len(money)} monetary references.",
                "Structured for semantic indexing and vector-like keyword querying."
            ],
            'key_dates': list(set(dates))[:8],
            'key_entities': {
                'people': ['Authorized Stakeholders'],
                'organizations': ['Clario Intelligence Workspace'],
                'financial_terms': list(set(money))[:6]
            },
            'document_type_detected': 'Structured Document',
            'ai_source': source or 'clario_local_engine',
            'notice': notice or 'Analyzed using Clario deterministic document intelligence.'
        }

    def _heuristic_email_analysis(self, body, subject, sender, source, notice):
        b_lower = (body + " " + (subject or "")).lower()
        
        # Urgency detection
        urgency = 0.3
        if any(w in b_lower for w in ['urgent', 'asap', 'immediately', 'deadline', 'critical', 'emergency', 'right away']):
            urgency = 0.9
        elif any(w in b_lower for w in ['soon', 'important', 'today', 'priority', 'action required']):
            urgency = 0.65
            
        # Category detection
        category = 'Work'
        if any(w in b_lower for w in ['invoice', 'payment', 'transfer', 'dollar', 'receipt', 'charge', 'bank', 'usd']):
            category = 'Finance'
        elif any(w in b_lower for w in ['sale', 'discount', 'off', 'deal', 'promo', 'subscribe', 'newsletter']):
            category = 'Promotions'
        elif any(w in b_lower for w in ['urgent', 'emergency', 'immediate action']):
            category = 'Urgent'
        elif any(w in b_lower for w in ['family', 'friend', 'weekend', 'dinner', 'catch up']):
            category = 'Personal'
        elif urgency >= 0.7:
            category = 'Important'

        # Sentiment
        positive_words = ['thank', 'great', 'pleasure', 'excellent', 'appreciate', 'delighted', 'good', 'congrats']
        negative_words = ['unhappy', 'delayed', 'error', 'issue', 'problem', 'fail', 'cancel', 'urgent', 'disappointed']
        pos_count = sum(1 for w in positive_words if w in b_lower)
        neg_count = sum(1 for w in negative_words if w in b_lower)
        sentiment = 'Positive' if pos_count > neg_count else ('Negative' if neg_count > pos_count else 'Neutral')

        # Task extraction
        tasks = []
        for line in body.split('\n'):
            line_str = line.strip()
            if any(cue in line_str.lower() for cue in ['please', 'need to', 'could you', 'action item', 'ensure', 'review', 'send']):
                if len(line_str) > 10:
                    tasks.append(line_str[:120])
        if not tasks:
            tasks = ["Review correspondence and confirm receipt"]

        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|tomorrow|today|EOD)\b)', body, re.IGNORECASE)

        return {
            'category': category,
            'sentiment': sentiment,
            'urgency_score': round(urgency, 2),
            'summary': f"Email from {sender or 'sender'} regarding '{subject or 'general inquiry'}'. Sentiment appears {sentiment.lower()} with urgency rating of {int(urgency*100)}%.",
            'tasks': tasks[:5],
            'deadlines': list(set(dates))[:4] if dates else ["Standard response window (48h)"],
            'suggested_tones': ['Professional', 'Friendly', 'Formal'],
            'ai_source': source or 'clario_local_engine',
            'notice': notice or 'Analyzed using Clario email intelligence heuristics.'
        }

    def _heuristic_transaction_analysis(self, tx_data, source, notice):
        amount = float(tx_data.get('amount', 0))
        indicators = []
        risk_score = 15.0
        
        if amount > 10000:
            risk_score += 45
            indicators.append(f"High-value transaction magnitude (${amount:,.2f}) exceeds $10,000 threshold")
        elif amount > 3000:
            risk_score += 20
            indicators.append(f"Elevated transaction sum (${amount:,.2f}) above typical retail average")
            
        category = str(tx_data.get('category', '')).lower()
        if category in ['crypto', 'wire', 'gambling', 'offshore']:
            risk_score += 25
            indicators.append(f"Transaction sector category '{category}' associated with heightened scrutiny")
            
        risk_score = min(98.0, risk_score)
        level = 'HIGH' if risk_score >= 70 else ('MEDIUM' if risk_score >= 40 else 'LOW')
        
        action = "Approve transaction"
        if level == 'HIGH':
            action = "Escalate to compliance team for immediate verification"
        elif level == 'MEDIUM':
            action = "Request secondary multi-factor authentication or manual clearance"
            
        return {
            'risk_score': round(risk_score, 1),
            'risk_level': level,
            'detected_indicators': indicators if indicators else ["Routine velocity and recipient pattern within standard baseline"],
            'explanation': f"Evaluated transaction of ${amount:,.2f} to {tx_data.get('recipient', 'recipient')}. Risk profile categorized as {level} based on amount metrics and sector categorization.",
            'recommended_action': action,
            'ai_source': source or 'clario_local_engine',
            'notice': notice or 'Evaluated using Clario rule-based risk profiling engine.'
        }

    def _heuristic_orchestration(self, user_request, source, notice):
        req_lower = user_request.lower()
        if any(w in req_lower for w in ['email', 'reply', 'draft', 'inbox', 'subject', 'tone']):
            agent = 'email_agent'
            tools = ['analyze_email', 'generate_email_reply']
            reasoning = "User request focuses on email communications and response drafting."
        elif any(w in req_lower for w in ['transaction', 'fraud', 'security', 'suspicious', 'risk', 'anomaly', 'money', 'payment']):
            agent = 'security_agent'
            tools = ['scan_transactions', 'calculate_risk_score', 'detect_anomalies']
            reasoning = "User request involves financial safety, transaction risk, or anomaly detection."
        elif any(w in req_lower for w in ['document', 'pdf', 'docx', 'csv', 'summary', 'extract', 'file']):
            agent = 'document_agent'
            tools = ['extract_document_text', 'summarize_document', 'query_document']
            reasoning = "User request targets document analysis, text extraction, or file summarization."
        elif any(w in req_lower for w in ['report', 'export', 'metrics', 'audit', 'dashboard']):
            agent = 'report_agent'
            tools = ['generate_executive_report', 'export_summary']
            reasoning = "User request requests executive reports, analytics, or summaries."
        else:
            agent = 'research_agent'
            tools = ['search_knowledge_base', 'synthesize_findings']
            reasoning = "General synthesis and exploration query routed to Research Agent."

        return {
            'intent': 'task_execution',
            'primary_agent': agent,
            'secondary_agents': ['report_agent'] if agent != 'report_agent' else [],
            'reasoning': reasoning,
            'required_tools': tools,
            'immediate_answer_or_plan': f"Master Agent dispatched task to {agent.replace('_', ' ').title()}.",
            'ai_source': source or 'clario_local_engine',
            'notice': notice or 'Master Agent routed via Clario intention-dispatch matrix.'
        }

# Global singleton helper
ai_service = GeminiAIService()
