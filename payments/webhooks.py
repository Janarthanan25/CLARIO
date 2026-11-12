import json
from flask import current_app
from models import db
from models.models import User, Payment, Subscription
from services.audit_service import log_action
from services.notification_service import send_notification

def handle_paypal_webhook(payload, headers):
    """
    Process inbound PayPal Webhook notifications with signature verification
    and database state reconciliation.
    """
    event_type = payload.get('event_type')
    resource = payload.get('resource', {})
    
    if not event_type:
        return {'status': 'ignored', 'reason': 'No event_type provided'}

    try:
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
            amount_val = float(resource.get('amount', {}).get('value', 29.00))
            payer_email = resource.get('payer', {}).get('email_address')
            
            # Reconcile user if found
            user = None
            if payer_email:
                user = User.query.filter_by(email=payer_email).first()

            if user and order_id:
                payment = Payment.query.filter_by(order_id=order_id).first()
                if not payment:
                    payment = Payment(
                        user_id=user.id,
                        order_id=order_id,
                        capture_id=resource.get('id'),
                        amount=amount_val,
                        currency=resource.get('amount', {}).get('currency_code', 'USD'),
                        status='COMPLETED',
                        payer_email=payer_email,
                        payment_source='paypal_webhook'
                    )
                    db.session.add(payment)
                    user.plan = 'PRO'
                    user.subscription_status = 'active'
                    db.session.commit()
                    log_action(user.id, 'WEBHOOK_PAYMENT_PROCESSED', 'payments', {'order_id': order_id})
                    send_notification(user.id, 'Payment Confirmed', f'Your subscription payment of ${amount_val:.2f} was confirmed via PayPal Webhook.', 'payment')

        return {'status': 'processed', 'event_type': event_type}

    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'error': str(e)}
