from agents.master_agent import MasterAgent

def test_master_agent_security_routing(app, auth_user):
    with app.app_context():
        master = MasterAgent(user_id=auth_user)
        result = master.process_command(
            "Scan our recent financial payments for fraudulent velocity and anomalous charges",
            context={'load_demo': True}
        )
        assert result['status'] == 'success'
        assert result['master_orchestration']['primary_agent'] in ['security_agent', 'research_agent']
        assert len(result['tools_called']) > 0
        assert len(result['final_summary']) > 10

def test_master_agent_email_routing(app, auth_user):
    with app.app_context():
        master = MasterAgent(user_id=auth_user)
        result = master.process_command(
            "Draft a professional email reply confirming the deadline extension",
            context={'email_body': "Hi, can you confirm deadline extension to Friday?", 'tone': 'Professional'}
        )
        assert result['status'] == 'success'
        assert result['master_orchestration']['primary_agent'] in ['email_agent', 'research_agent']

def test_agent_api_routes(logged_in_client):
    status_res = logged_in_client.get('/api/agents/status')
    assert status_res.status_code == 200
    agents = status_res.get_json()['agents']
    assert len(agents) == 6

    run_res = logged_in_client.post('/api/agents/run', json={
        'prompt': 'Compile executive report of workspace activities'
    })
    assert run_res.status_code == 200
    assert run_res.get_json()['success'] is True
