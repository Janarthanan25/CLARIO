def test_registration_success(client):
    res = client.post('/api/auth/register', json={
        'full_name': 'Alice Smith',
        'username': 'alicesmith',
        'email': 'alice@example.com',
        'password': 'StrongPassword123'
    })
    assert res.status_code in [200, 302]
    data = res.get_json()
    if data:
        assert data['success'] is True

def test_registration_duplicate_email(client, auth_user):
    res = client.post('/api/auth/register', json={
        'full_name': 'Duplicate User',
        'username': 'differentusername',
        'email': 'testuser@example.com',
        'password': 'Password123!'
    })
    assert res.status_code == 400
    assert 'already exists' in res.get_json()['error']

def test_login_success(client, auth_user):
    res = client.post('/api/auth/login', json={
        'identifier': 'testuser@example.com',
        'password': 'Password123!'
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

def test_login_invalid_password(client, auth_user):
    res = client.post('/api/auth/login', json={
        'identifier': 'testuser@example.com',
        'password': 'WrongPassword!'
    })
    assert res.status_code == 401
    assert res.get_json()['success'] is False

def test_logout(logged_in_client):
    res = logged_in_client.get('/logout')
    assert res.status_code == 302

def test_protected_routes_unauthorized(client):
    res = client.get('/dashboard')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

def test_admin_route_forbidden_for_user(logged_in_client):
    res = logged_in_client.get('/admin')
    assert res.status_code == 403

def test_admin_route_allowed_for_admin(admin_client):
    res = admin_client.get('/admin')
    assert res.status_code == 200

def test_admin_system_health(admin_client):
    res = admin_client.get('/api/admin/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'HEALTHY'
    assert data['subsystems']['database'] == 'OPERATIONAL'
