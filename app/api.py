from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Trade, Account

api_bp = Blueprint('api', __name__)

@api_bp.route('/chart-data')
@login_required
def chart_data():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.date.asc()).all()
    account = Account.query.filter_by(user_id=current_user.id).first()
    
    # Compile historical tracking for equity curves chart components
    balance_history = []
    labels = []
    
    if account:
        balance_history.append(account.initial_balance)
        labels.append("Start")
        
    for index, t in enumerate(trades):
        balance_history.append(t.balance_after)
        labels.append(f"Trade {index + 1} ({t.pair})")
        
    # Outcomes Processing Pipeline
    win_count = len([t for t in trades if t.outcome == 'Win'])
    loss_count = len([t for t in trades if t.outcome == 'Loss'])
    be_count = len([t for t in trades if t.outcome == 'Break-even'])
    
    return jsonify({
        'equity_curve': {
            'labels': labels,
            'data': balance_history
        },
        'outcomes': {
            'labels': ['Wins', 'Losses', 'Break-even'],
            'data': [win_count, loss_count, be_count]
        }
    })

