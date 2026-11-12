from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from payments.paypal import paypal_client
from payments.webhooks import handle_paypal_webhook
from models.models import Payment, Subscription
from extensions import csrf

payment_bp = Blueprint('payments', __name__)

@payment_bp.route('/payments', methods=['GET'])
@login_required
def payments_view():
    plans = current_app.config['SUBSCRIPTION_PLANS']
    subscription = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).first()
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    paypal_client_id = current_app.config.get('PAYPAL_CLIENT_ID', 'sb')
    paypal_mode = current_app.config.get('PAYPAL_MODE', 'sandbox')

    return render_template(
        'payments.html',
        plans=plans,
        subscription=subscription,
        payments=payments,
        paypal_client_id=paypal_client_id,
        paypal_mode=paypal_mode
    )


@payment_bp.route('/api/paypal/create-order', methods=['POST'])
@login_required
def create_paypal_order():
    data = request.get_json(silent=True) or {}
    plan_name = data.get('plan_name', 'PRO')
    
    res = paypal_client.create_order(user_id=current_user.id, plan_name=plan_name)
    return jsonify({
        'success': True,
        'orderID': res.get('order_id'),
        'details': res
    })


@payment_bp.route('/api/paypal/capture-order', methods=['POST'])
@login_required
def capture_paypal_order():
    data = request.get_json(silent=True) or {}
    order_id = data.get('orderID') or data.get('order_id')

    if not order_id:
        return jsonify({'success': False, 'error': 'Order ID is required.'}), 400

    capture_res = paypal_client.capture_order(order_id, user_id=current_user.id)
    if capture_res.get('status') == 'COMPLETED':
        return jsonify({
            'success': True,
            'message': 'Subscription payment verified and Clario Pro activated!',
            'data': capture_res
        })
    return jsonify({
        'success': False,
        'error': capture_res.get('error', 'Payment capture could not be verified.')
    }), 400


@payment_bp.route('/api/paypal/webhook', methods=['POST'])
@csrf.exempt
def paypal_webhook():
    payload = request.get_json(silent=True) or {}
    headers = dict(request.headers)
    result = handle_paypal_webhook(payload, headers)
    return jsonify(result), 200


@payment_bp.route('/api/paypal/history', methods=['GET'])
@login_required
def payment_history():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    return jsonify({
        'success': True,
        'payments': [p.to_dict() for p in payments]
    })
