from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Trade, Account, db
from datetime import datetime
from app import csrf
journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/')
@login_required
def dashboard():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.date.desc(), Trade.time.desc()).all()
    account = Account.query.filter_by(user_id=current_user.id).first()
    
    total_trades = len(trades)
    wins = [t for t in trades if t.outcome == 'Win']
    losses = [t for t in trades if t.outcome == 'Loss']
    
    win_rate = round((len(wins) / total_trades * 100), 1) if total_trades > 0 else 0
    net_pnl = sum(t.net_pnl for t in trades)
    
    total_win_amt = sum(t.net_pnl for t in wins)
    total_loss_amt = abs(sum(t.net_pnl for t in losses))
    profit_factor = round(total_win_amt / total_loss_amt, 2) if total_loss_amt > 0 else total_win_amt
    
    return render_template('dashboard.html', trades=trades[:5], account=account, total_trades=total_trades, win_rate=win_rate, net_pnl=net_pnl, profit_factor=profit_factor)


@journal_bp.route('/journal', methods=['GET', 'POST'])
@login_required
def log_book():
    if request.method == 'POST':
        try:
            flags_list = request.form.getlist('flags')
            trade = Trade(
                user_id=current_user.id,
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                time=datetime.strptime(request.form.get('time'), '%H:%M').time(),
                session=request.form.get('session'),
                pair=request.form.get('pair').upper(),
                asset_class=request.form.get('asset_class'),
                direction=request.form.get('direction'),
                entry_price=float(request.form.get('entry_price')),
                stop_loss=float(request.form.get('stop_loss')),
                take_profit=float(request.form.get('take_profit')),
                exit_price=float(request.form.get('exit_price')),
                lot_size=float(request.form.get('lot_size')),
                risk_percentage=float(request.form.get('risk_percentage', 1)),
                balance_before=float(request.form.get('balance_before')),
                balance_after=float(request.form.get('balance_after')),
                strategy=request.form.get('strategy'),
                timeframe=request.form.get('timeframe'),
                emotions_before=request.form.get('emotions_before'),
                emotions_after=request.form.get('emotions_after'),
                discipline_score=int(request.form.get('discipline_score', 5)),
                flags=",".join(flags_list),
                notes=request.form.get('notes', '')
            )
            trade.calculate_metrics()
            db.session.add(trade)
            
            account = Account.query.filter_by(user_id=current_user.id).first()
            if account:
                account.current_balance = trade.balance_after
                
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'success', 'message': 'Trade logged seamlessly!'})
            flash('Trade execution metrics recorded!', 'success')
            return redirect(url_for('journal.log_book'))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': str(e)}), 400
            flash(f'Error compiling logs parsing: {str(e)}', 'danger')
            
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.date.desc(), Trade.time.desc()).all()
    account = Account.query.filter_by(user_id=current_user.id).first()
    return render_template('journal.html', trades=trades, account=account)


@journal_bp.route('/journal/import', methods=['POST'])
@login_required
@csrf.exempt
def import_trades():
    """
    Bulk import trades from a JSON array.
    Accepts application/json body — no CSRF token needed (JSON API route).
    
    Minimal required fields per trade:
        date, time, pair, direction, entry_price, exit_price,
        lot_size, net_pnl, balance_before, balance_after
    
    Optional fields (sensible defaults applied if missing):
        session, asset_class, strategy, timeframe, stop_loss,
        take_profit, risk_percentage, emotions_before, emotions_after,
        discipline_score, flags, notes
    """
    data = request.get_json(silent=True)

    if not data or not isinstance(data, list):
        return jsonify({'status': 'error', 'message': 'Expected a JSON array of trades.'}), 400

    imported = 0
    skipped = 0
    errors = []

    for i, t in enumerate(data):
        try:
            # --- Infer session from time if not provided ---
            raw_time = t.get('time', '00:00:00')
            time_obj = datetime.strptime(raw_time, '%H:%M:%S').time() if len(raw_time) == 8 else datetime.strptime(raw_time, '%H:%M').time()
            hour = time_obj.hour

            if t.get('session'):
                session = t['session']
            elif 6 <= hour < 15:
                session = 'London'
            elif 13 <= hour < 22:
                session = 'New York'
            elif 0 <= hour < 6:
                session = 'Asian'
            else:
                session = 'Sydney'

            # --- Infer asset class from pair if not provided ---
            pair = t.get('pair', '').upper()
            if t.get('asset_class'):
                asset_class = t['asset_class']
            elif 'XAU' in pair or 'GOLD' in pair:
                asset_class = 'Gold'
            elif any(idx in pair for idx in ['US30', 'NAS', 'SPX', 'DAX']):
                asset_class = 'Indices'
            elif any(crypto in pair for crypto in ['BTC', 'ETH', 'XRP']):
                asset_class = 'Crypto'
            else:
                asset_class = 'Forex'

            # --- Determine outcome from net_pnl if not provided ---
            net_pnl = float(t.get('net_pnl', 0))
            if t.get('outcome'):
                outcome = t['outcome']
            elif net_pnl > 0.01:
                outcome = 'Win'
            elif net_pnl < -0.01:
                outcome = 'Loss'
            else:
                outcome = 'Break-even'

            trade = Trade(
                user_id=current_user.id,
                date=datetime.strptime(t['date'], '%Y-%m-%d').date(),
                time=time_obj,
                session=session,
                pair=pair,
                asset_class=asset_class,
                direction=t.get('direction', 'Buy'),
                entry_price=float(t.get('entry_price', 0)),
                stop_loss=float(t.get('stop_loss') or 0),
                take_profit=float(t.get('take_profit') or 0),
                exit_price=float(t.get('exit_price', 0)),
                lot_size=float(t.get('lot_size', 0)),
                risk_percentage=float(t.get('risk_percentage', 1.0)),
                balance_before=float(t.get('balance_before', 0)),
                balance_after=float(t.get('balance_after', 0)),
                net_pnl=net_pnl,
                outcome=outcome,
                strategy=t.get('strategy', 'Price Action'),
                timeframe=t.get('timeframe', 'M15'),
                emotions_before=t.get('emotions_before', ''),
                emotions_after=t.get('emotions_after', ''),
                discipline_score=int(t.get('discipline_score', 5)),
                flags=t.get('flags', ''),
                notes=t.get('notes', '')
            )
            trade.calculate_metrics()
            db.session.add(trade)
            imported += 1

        except Exception as e:
            skipped += 1
            errors.append({'index': i, 'error': str(e), 'data': t})

    # --- Sync account balance to last imported trade ---
    if imported > 0:
        account = Account.query.filter_by(user_id=current_user.id).first()
        if account:
            last_balance = float(data[-1].get('balance_after', account.current_balance))
            account.current_balance = last_balance
        db.session.commit()

    return jsonify({
        'status': 'success' if imported > 0 else 'error',
        'imported': imported,
        'skipped': skipped,
        'final_balance': account.current_balance if imported > 0 else None,
        'errors': errors
    }), 200 if imported > 0 else 400


@journal_bp.route('/delete_trade/<int:trade_id>', methods=['DELETE'])
@login_required
def delete_trade(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    
    if trade.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized action.'}), 403
        
    try:
        account = Account.query.filter_by(user_id=current_user.id).first()
        if account:
            account.current_balance -= trade.net_pnl
            
        db.session.delete(trade)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Trade successfully deleted.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

