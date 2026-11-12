from services.ai_service import ai_service

class EmailAssistant:
    """
    Intelligent Email Assistant module.
    Provides automated categorization, sentiment analysis,
    urgency scoring, task extraction, deadline identification,
    and multi-tone reply drafting.
    """

    SUPPORTED_TONES = ['Professional', 'Friendly', 'Formal', 'Concise', 'Urgent']

    @staticmethod
    def process_email(body, subject=None, sender=None, desired_tone='Professional'):
        """
        Complete analysis pipeline for incoming email.
        """
        analysis = ai_service.analyze_email(body=body, subject=subject, sender=sender)
        
        reply_info = ai_service.generate_email_reply(
            email_body=body,
            tone=desired_tone,
            custom_instruction=f"Subject: {subject or ''}"
        )
        
        # Follow-up suggestion synthesis
        urgency = analysis.get('urgency_score', 0.5)
        category = analysis.get('category', 'Work')
        
        if urgency > 0.7:
            followup = "High priority: Follow up within 4 to 12 hours to confirm receipt and outline resolution."
        elif category == 'Finance':
            followup = "Financial record: Archive copy to accounting and request verified confirmation receipt."
        else:
            followup = "Standard communication: Recommend follow-up check in 48-72 business hours if unanswered."

        return {
            'subject': subject or 'No Subject',
            'sender': sender or 'Unknown Sender',
            'body': body,
            'category': analysis.get('category', 'Work'),
            'sentiment': analysis.get('sentiment', 'Neutral'),
            'urgency_score': analysis.get('urgency_score', 0.5),
            'summary': analysis.get('summary', 'Overview analyzed.'),
            'tasks': analysis.get('tasks', []),
            'deadlines': analysis.get('deadlines', []),
            'suggested_tones': EmailAssistant.SUPPORTED_TONES,
            'generated_reply': reply_info.get('reply', ''),
            'reply_tone': desired_tone,
            'followup_suggestion': followup,
            'ai_source': analysis.get('ai_source', 'clario_local_engine'),
            'notice': analysis.get('notice')
        }

    @staticmethod
    def regenerate_reply(email_body, tone='Professional', custom_instruction=None):
        """
        Regenerate reply draft with adjusted tone or specific instruction.
        """
        return ai_service.generate_email_reply(
            email_body=email_body,
            tone=tone,
            custom_instruction=custom_instruction
        )
