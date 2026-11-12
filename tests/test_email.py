from modules.email.assistant import EmailAssistant

def test_email_assistant_processing():
    body = "Hi Sarah, please review the invoice #4019 and submit payment by Friday. Thanks!"
    res = EmailAssistant.process_email(body, subject="Urgent Invoice Payment", sender="finance@example.com")
    
    assert res['category'] in ['Finance', 'Work', 'Urgent', 'Important']
    assert res['urgency_score'] > 0.0
    assert len(res['generated_reply']) > 10
    assert len(res['tasks']) > 0

def test_email_reply_tones():
    body = "Can we reschedule our sync to next Tuesday at 3pm?"
    res_prof = EmailAssistant.regenerate_reply(body, tone='Professional')
    res_friendly = EmailAssistant.regenerate_reply(body, tone='Friendly')
    
    assert res_prof['tone'] == 'Professional'
    assert res_friendly['tone'] == 'Friendly'
    assert len(res_prof['reply']) > 0

def test_email_api_routes(logged_in_client):
    res = logged_in_client.post('/api/emails/analyze', json={
        'subject': 'Project Deliverable',
        'sender': 'client@vanguard.io',
        'body': 'Please send over the updated financial audit spreadsheet by 5pm today.',
        'tone': 'Professional'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['email']['category'] in ['Work', 'Finance', 'Urgent', 'Important']
    assert 'email' in data
    email_id = data['email']['id']

    # Test Human Approval endpoint
    appr_res = logged_in_client.post(f'/api/emails/{email_id}/approve')
    assert appr_res.status_code == 200
    assert appr_res.get_json()['success'] is True
