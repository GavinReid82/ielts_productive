import stripe
from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from app.config import Config
from app.models import Task, Payment
from app.extensions import db
from flask_login import current_user
import logging

stripe.api_key = Config.STRIPE_SECRET_KEY

payments_bp = Blueprint('payments', __name__)

logger = logging.getLogger(__name__)

def record_payment(user_id, task_id, amount_paid, payment_status):
    payment = Payment(
        user_id=user_id,
        task_id=task_id,
        amount_paid=amount_paid,
        payment_status=payment_status
    )
    db.session.add(payment)
    db.session.commit()


@payments_bp.route('/checkout/<int:task_id>', methods=['POST'])
def checkout(task_id):
    """Creates a Stripe Checkout session for a specific task."""
    # Debug logging
    print(f"Current Stripe API key type: {stripe.api_key[:3] if stripe.api_key else 'None'}")
    
    # Explicitly set the API key from config
    stripe.api_key = Config.STRIPE_SECRET_KEY
    
    # Verify we're using the secret key
    if not stripe.api_key or not stripe.api_key.startswith('sk_'):
        return jsonify({
            "error": "Invalid Stripe configuration",
            "details": f"API key prefix: {stripe.api_key[:3] if stripe.api_key else 'None'}"
        }), 500

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    if task.is_free:
        return jsonify({"error": "This task is free and does not require payment."}), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': task.name},
                    'unit_amount': int(task.price * 100),  # Convert dollars to cents
                },
                'quantity': 1
            }],
            mode='payment',
            client_reference_id=str(task.id),
            success_url=url_for('payments.payment_success', task_id=task.id, _external=True),
            cancel_url=url_for('payments.payment_cancel', _external=True)
        )
        
        # Record the payment even if payment is not completed yet
        record_payment(current_user.id, task.id, task.price, "pending")
        
        return jsonify({'checkout_url': session.url})

    except Exception as e:
        return jsonify({
            'error': str(e),
            'api_key_type': stripe.api_key[:3] if stripe.api_key else 'None'
        }), 500



@payments_bp.route('/payment_success', methods=['GET'])
def payment_success():
    logger.info("Payment success endpoint called")
    try:
        task_id = request.args.get('task_id')
        logger.info(f"Received task_id: {task_id}")
        
        if not task_id:
            logger.error("No task ID provided in payment success")
            return render_template('payments/error.html', 
                                error="Missing task information. Please contact support."), 400
            
        task = Task.query.get(task_id)
        if not task:
            logger.error(f"Task not found for ID: {task_id}")
            return render_template('payments/error.html',
                                error="Invalid task information. Please contact support."), 404
            
        if not current_user.is_authenticated:
            logger.warning("User not authenticated in payment success")
            return redirect(url_for('auth.login'))
        
        # Record the payment in the Payment table
        try:
            logger.info(f"Recording payment for user {current_user.id} and task {task.id}")
            record_payment(current_user.id, task.id, task.price, "completed")
            logger.info("Payment recorded successfully")
        except Exception as e:
            logger.error(f"Failed to record payment: {str(e)}", exc_info=True)
            # Continue anyway - user has paid, so show success page
        
        return render_template('payments/payment_success.html', task=task)
        
    except Exception as e:
        logger.error(f"Payment success error: {str(e)}", exc_info=True)
        return render_template('payments/error.html', 
                             error="There was an issue processing your payment success. "
                             "Please contact support if you were charged."), 500


@payments_bp.route('/payment-cancel')
def payment_cancel():
    """Handles payment cancellation."""
    return redirect(url_for('dashboard.dashboard_home'))


@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event based on its type
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']  # Contains a Stripe session object
        task_id = session['client_reference_id']  # Assuming task_id is passed as the client_reference_id
        task = Task.query.get(task_id)

    return '', 200

