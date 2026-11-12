import pytest
from app import create_app
from config import TestConfig
from models import db
from models.models import User, Subscription

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def auth_user(app):
    with app.app_context():
        user = User(
            email='testuser@example.com',
            username='testuser',
            full_name='Test User',
            role='user',
            plan='FREE'
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User.query.filter_by(email='admin@clario.ai').first()
        if not admin:
            admin = User(
                email='admin@clario.ai',
                username='admin',
                full_name='System Admin',
                role='admin',
                plan='PRO'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
        return admin.id

@pytest.fixture
def logged_in_client(client, auth_user):
    client.post('/login', data={'identifier': 'testuser@example.com', 'password': 'Password123!'})
    return client

@pytest.fixture
def admin_client(client, admin_user):
    client.post('/login', data={'identifier': 'admin@clario.ai', 'password': 'Admin123!'})
    return client
