from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Trade
from collections import defaultdict
from datetime import date

analytics_bp = Blueprint('analytics', __name__)


def safe_div(a, b, fallback=0.0):
    return round(a / b, 2) if b else fallback


@analytics_bp.route('/')
@login_required
def stats_center():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(
        Trade.date.asc(), Trade.time.asc()
    ).all()

    if not trades:
        return render_template('analytics.html', empty=True)

    # ── Core outcome buckets ──────────────────────────────────────────────────
    wins   = [t for t in trades if t.outcome == 'Win']
    losses = [t for t in trades if t.outcome == 'Loss']
    be     = [t for t in trades if t.outcome == 'Break-even']
    total  = len(trades)

    win_rate  = round(len(wins)   / total * 100, 1)
    loss_rate = round(len(losses) / total * 100, 1)
    be_rate   = round(len(be)     / total * 100, 1)

    # ── P&L Metrics ───────────────────────────────────────────────────────────
    total_pnl      = round(sum(t.net_pnl for t in trades), 2)
    gross_profit   = round(sum(t.net_pnl for t in wins), 2)
    gross_loss     = round(abs(sum(t.net_pnl for t in losses)), 2)
    profit_factor  = safe_div(gross_profit, gross_loss)

    avg_win        = safe_div(gross_profit, len(wins))
    avg_loss       = safe_div(gross_loss, len(losses))
    expectancy     = round((win_rate / 100 * avg_win) - (loss_rate / 100 * avg_loss), 2)

    largest_win    = round(max((t.net_pnl for t in wins),  default=0), 2)
    largest_loss   = round(min((t.net_pnl for t in losses), default=0), 2)

    # ── R:R & Pip Metrics ─────────────────────────────────────────────────────
    rr_values      = [t.rr_ratio for t in trades if t.rr_ratio > 0]
    avg_rr         = safe_div(sum(rr_values), len(rr_values))

    pip_values     = [t.pip_gain_loss for t in trades]
    total_pips     = round(sum(pip_values), 2)
    avg_pips       = safe_div(sum(pip_values), total)

    # ── Drawdown Analysis ─────────────────────────────────────────────────────
    peak = trades[0].balance_before
    max_drawdown = 0.0
    drawdown_pct = 0.0
    running_balance = trades[0].balance_before

    for t in trades:
        running_balance = t.balance_after
        if running_balance > peak:
            peak = running_balance
        dd = peak - running_balance
        if dd > max_drawdown:
            max_drawdown = dd
            drawdown_pct = safe_div(dd, peak) * 100

    max_drawdown = round(max_drawdown, 2)
    drawdown_pct = round(drawdown_pct, 2)

    # ── Streak Analysis ───────────────────────────────────────────────────────
    best_streak = cur_win = 0
    worst_streak = cur_loss = 0
    for t in trades:
        if t.outcome == 'Win':
            cur_win += 1
            cur_loss = 0
            best_streak = max(best_streak, cur_win)
        elif t.outcome == 'Loss':
            cur_loss += 1
            cur_win = 0
            worst_streak = max(worst_streak, cur_loss)
        else:
            cur_win = cur_loss = 0

    # ── Performance by Pair ───────────────────────────────────────────────────
    pair_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pips': 0.0})
    for t in trades:
        p = pair_stats[t.pair]
        p['trades'] += 1
        p['pnl']    = round(p['pnl'] + t.net_pnl, 2)
        p['pips']   = round(p['pips'] + t.pip_gain_loss, 2)
        if t.outcome == 'Win':
            p['wins'] += 1

    for p, v in pair_stats.items():
        v['win_rate'] = round(safe_div(v['wins'], v['trades']) * 100, 1)

    pair_stats = dict(sorted(pair_stats.items(), key=lambda x: x[1]['pnl'], reverse=True))

    # ── Performance by Session ────────────────────────────────────────────────
    session_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
    for t in trades:
        s = session_stats[t.session]
        s['trades'] += 1
        s['pnl']    = round(s['pnl'] + t.net_pnl, 2)
        if t.outcome == 'Win':
            s['wins'] += 1

    for s, v in session_stats.items():
        v['win_rate'] = round(safe_div(v['wins'], v['trades']) * 100, 1)

    # ── Performance by Direction ──────────────────────────────────────────────
    direction_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
    for t in trades:
        d = direction_stats[t.direction]
        d['trades'] += 1
        d['pnl']    = round(d['pnl'] + t.net_pnl, 2)
        if t.outcome == 'Win':
            d['wins'] += 1

    for d, v in direction_stats.items():
        v['win_rate'] = round(safe_div(v['wins'], v['trades']) * 100, 1)

    # ── Performance by Day of Week ────────────────────────────────────────────
    dow_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
               3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    dow_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'pnl': 0.0})
    for t in trades:
        day = dow_map[t.date.weekday()]
        dow_stats[day]['trades'] += 1
        dow_stats[day]['pnl']    = round(dow_stats[day]['pnl'] + t.net_pnl, 2)
        if t.outcome == 'Win':
            dow_stats[day]['wins'] += 1

    for d, v in dow_stats.items():
        v['win_rate'] = round(safe_div(v['wins'], v['trades']) * 100, 1)

    # Order by weekday
    ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_stats = {d: dow_stats[d] for d in ordered_days if d in dow_stats}

    # ── Equity Curve Data (for Chart.js) ──────────────────────────────────────
    equity_labels  = ['Start']
    equity_values  = [round(trades[0].balance_before, 2)]
    for i, t in enumerate(trades):
        equity_labels.append(f"#{i+1} {t.pair}")
        equity_values.append(round(t.balance_after, 2))

    # ── Daily PnL (for bar chart) ─────────────────────────────────────────────
    daily_pnl = defaultdict(float)
    for t in trades:
        daily_pnl[str(t.date)] = round(daily_pnl[str(t.date)] + t.net_pnl, 2)

    daily_pnl  = dict(sorted(daily_pnl.items()))
    daily_labels = list(daily_pnl.keys())
    daily_values = list(daily_pnl.values())

    # ── Psychology Metrics ────────────────────────────────────────────────────
    discipline_scores = [t.discipline_score for t in trades if t.discipline_score]
    avg_discipline    = safe_div(sum(discipline_scores), len(discipline_scores))

    all_flags = []
    for t in trades:
        if t.flags:
            all_flags.extend([f.strip() for f in t.flags.split(',') if f.strip()])

    flag_counts = defaultdict(int)
    for f in all_flags:
        flag_counts[f] += 1
    flag_counts = dict(sorted(flag_counts.items(), key=lambda x: x[1], reverse=True))

    # ── Asset Class Breakdown ─────────────────────────────────────────────────
    asset_stats = defaultdict(lambda: {'trades': 0, 'pnl': 0.0, 'wins': 0})
    for t in trades:
        a = asset_stats[t.asset_class]
        a['trades'] += 1
        a['pnl']    = round(a['pnl'] + t.net_pnl, 2)
        if t.outcome == 'Win':
            a['wins'] += 1

    for a, v in asset_stats.items():
        v['win_rate'] = round(safe_div(v['wins'], v['trades']) * 100, 1)

    return render_template('analytics.html',
        empty=False,
        total=total,
        wins=len(wins),
        losses=len(losses),
        be_count=len(be),
        win_rate=win_rate,
        loss_rate=loss_rate,
        be_rate=be_rate,

        total_pnl=total_pnl,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        largest_win=largest_win,
        largest_loss=largest_loss,

        avg_rr=avg_rr,
        total_pips=total_pips,
        avg_pips=avg_pips,

        max_drawdown=max_drawdown,
        drawdown_pct=drawdown_pct,
        best_streak=best_streak,
        worst_streak=worst_streak,

        pair_stats=pair_stats,
        session_stats=session_stats,
        direction_stats=direction_stats,
        dow_stats=dow_stats,
        asset_stats=asset_stats,

        equity_labels=equity_labels,
        equity_values=equity_values,
        daily_labels=daily_labels,
        daily_values=daily_values,

        avg_discipline=avg_discipline,
        flag_counts=flag_counts,
    )

