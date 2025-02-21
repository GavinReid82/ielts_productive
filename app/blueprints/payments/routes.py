import stripe
from flask import Blueprint, request, jsonify, redirect, url_for, session
from app.config import Config
from app.models import Task, UserTask
from app.extensions import db
from flask_login import current_user

stripe.api_key = Config.STRIPE_SECRET_KEY

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/checkout/<int:task_id>', methods=['POST'])
def checkout(task_id):
    """Creates a Stripe Checkout session for a specific task."""
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
                    'unit_amount': task.price
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=url_for('payments.payment_success', task_id=task.id, _external=True),
            cancel_url=url_for('payments.payment_cancel', _external=True)
        )
        return jsonify({'checkout_url': session.url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/payment-success/<int:task_id>')
def payment_success(task_id):
    """Marks a task as paid for the user."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    task = Task.query.get(task_id)
    if not task:
        return redirect(url_for('dashboard.dashboard_home'))

    # Store the purchased task in the database
    new_purchase = UserTask(user_id=current_user.id, task_id=task.id)
    db.session.add(new_purchase)
    db.session.commit()

    return redirect(url_for('writing.writing_general_task_1_letter'))


@payments_bp.route('/payment-cancel')
def payment_cancel():
    """Handles payment cancellation."""
    return redirect(url_for('dashboard.dashboard_home'))
