from models.models import User

def test_paypal_order_creation_and_capture(logged_in_client, auth_user, app):
    # 1. Create order
    order_res = logged_in_client.post('/api/paypal/create-order', json={'plan_name': 'PRO'})
    assert order_res.status_code == 200
    data = order_res.get_json()
    assert data['success'] is True
    order_id = data['orderID']
    assert order_id is not None

    # Verify initial user plan is FREE
    with app.app_context():
        u = User.query.get(auth_user)
        assert u.plan == 'FREE'

    # 2. Capture order
    capture_res = logged_in_client.post('/api/paypal/capture-order', json={'orderID': order_id})
    assert capture_res.status_code == 200
    cap_data = capture_res.get_json()
    assert cap_data['success'] is True
    assert cap_data['data']['status'] == 'COMPLETED'

    # 3. Verify user was upgraded to PRO
    with app.app_context():
        u = User.query.get(auth_user)
        assert u.plan == 'PRO'
        assert u.subscription_status == 'active'

    # 4. Check payment history
    hist_res = logged_in_client.get('/api/paypal/history')
    assert hist_res.status_code == 200
    hist = hist_res.get_json()
    assert len(hist['payments']) >= 1
    assert hist['payments'][0]['order_id'] == order_id

def test_paypal_webhook_endpoint(client):
    webhook_payload = {
        "event_type": "CHECKOUT.ORDER.APPROVED",
        "resource": {
            "id": "ORD-SAMPLE-999"
        }
    }
    res = client.post('/api/paypal/webhook', json=webhook_payload)
    assert res.status_code == 200
    assert res.get_json()['status'] == 'processed'
