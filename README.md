# 📈 FX Trading Journal

A self-hosted, mobile-friendly trading journal built with Flask — designed to run locally on **Termux (Android)** or any Python environment. Log trades manually or bulk-import directly from MT5 history screenshots via a parsed JSON workflow.

---

## ✨ Features

- **Trade Logging** — Full execution capture: pair, direction, entry/exit, SL/TP, lot size, session, timeframe, strategy, R:R
- **Bulk Import** — POST a JSON array of trades parsed from MT5 history screenshots via `import_trades.py`
- **Advanced Analytics** — Equity curve, daily P&L, win rate, profit factor, expectancy, max drawdown, streaks, per-pair/session/direction/day-of-week breakdowns
- **Psychology Tracking** — Discipline scores, emotional state before/after, behavioural flags (FOMO, Revenge, etc.)
- **Account Management** — Auto-syncs balance after every trade logged
- **Responsive UI** — Dark theme, Tailwind CSS, Chart.js visualisations — works on mobile

---

## 🗂 Project Structure

```
fx_journal/
├── app/
│   ├── __init__.py          # App factory, extensions, blueprints, seed CLI
│   ├── models.py            # User, Account, Trade SQLAlchemy models
│   ├── auth.py              # Register, login, logout routes
│   ├── journal.py           # Trade logging, bulk import, delete routes
│   ├── analytics.py         # Full stats computation and analytics route
│   ├── api.py               # JSON API: equity curve + outcome chart data
│   ├── static/
│   │   ├── css/
│   │   ├── js/app.js
│   │   └── uploads/         # Trade screenshots
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── journal.html
│       ├── analytics.html
│       ├── login.html
│       └── register.html
├── config.py                # Flask config (secret key, DB URI, upload folder)
├── manage.py                # DB migration / management commands
├── run.sh                   # Launch script
├── requirements.txt
├── import_trades.py         # CLI bulk import script
├── trades.json              # Parsed MT5 trade data (example)
└── journal.db               # SQLite database (auto-created)
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### On Termux (Android)
```bash
pkg update && pkg upgrade
pkg install python git
pip install flask flask-sqlalchemy flask-login flask-wtf werkzeug requests
```

### On Desktop / Linux
```bash
git clone https://github.com/arvineee/Forex_Trading_Journal.git
cd Forex_Trading_Journal
pip install -r requirements.txt
```

---

## 🚀 Running the App

```bash
chmod +x run.sh
./run.sh
```

Or manually:
```bash
export FLASK_APP=app
export FLASK_ENV=development
flask run --port 5500
```

App runs at: **http://localhost:5500**

---

## 🌱 First-Time Database Setup

Seed the database with a default trader account and sample trades:

```bash
flask seed-db
```

Default credentials:
| Field | Value |
|-------|-------|
| Username | `trader` |
| Password | `password123` |
| Starting Balance | $250.00 |

> ⚠️ Change the password after first login if deploying on a shared network.

---

## 📥 Bulk Import from MT5 (Screenshot Workflow)

Instead of entering trades manually, you can import directly from MT5 history:

### Step 1 — Get the JSON
Take a screenshot of your MT5 History (Positions tab) and paste it into Claude. It will parse all trades into a ready-to-use `trades.json` file.

### Step 2 — Configure the import script
Edit the CONFIG block in `import_trades.py`:
```python
BASE_URL = "http://localhost:5500"
USERNAME = "trader"
PASSWORD = "password123"
```

### Step 3 — Run the import
Make sure the app is running in one terminal, then in another:
```bash
python import_trades.py trades.json
```

Expected output:
```
📂 Loaded 16 trade(s) from 'trades.json'
🔐 Logging in as 'trader'...
   ✅ Login successful.

📤 Importing 16 trade(s) to http://localhost:5500/journal/import...
   ✅ Import complete!
   📊 Imported  : 16 trades
   ⏭️  Skipped   : 0 trades
   💰 Balance   : $386.16
```

### JSON Trade Format
Each trade object in the array supports these fields:

| Field | Required | Example |
|-------|----------|---------|
| `date` | ✅ | `"2026-05-26"` |
| `time` | ✅ | `"16:31:29"` |
| `pair` | ✅ | `"EURUSD"` |
| `direction` | ✅ | `"Buy"` or `"Sell"` |
| `entry_price` | ✅ | `1.16405` |
| `exit_price` | ✅ | `1.16270` |
| `lot_size` | ✅ | `0.05` |
| `net_pnl` | ✅ | `-6.75` |
| `balance_before` | ✅ | `250.00` |
| `balance_after` | ✅ | `243.25` |
| `stop_loss` | ➖ | `1.16195` |
| `take_profit` | ➖ | `1.16947` |
| `session` | ➖ | `"London"` (auto-inferred from time) |
| `asset_class` | ➖ | `"Forex"` (auto-inferred from pair) |
| `strategy` | ➖ | `"Price Action"` |
| `timeframe` | ➖ | `"M15"` |
| `risk_percentage` | ➖ | `1.0` |
| `discipline_score` | ➖ | `5` (1–5 scale) |
| `emotions_before` | ➖ | `"Calm"` |
| `emotions_after` | ➖ | `"Satisfied"` |
| `flags` | ➖ | `"FOMO,Revenge"` |
| `notes` | ➖ | `"Entered on FVG retest"` |

---

## 📊 Analytics

Navigate to `/analytics` for the full stats dashboard:

| Metric | Description |
|--------|-------------|
| **Win Rate** | % of winning trades |
| **Profit Factor** | Gross profit ÷ gross loss |
| **Expectancy** | Average $ return per trade |
| **Max Drawdown** | Largest peak-to-trough drop |
| **Avg R:R** | Average risk/reward ratio |
| **Best/Worst Streak** | Consecutive wins/losses |
| **By Pair** | P&L and win rate per instrument |
| **By Session** | London / New York / Asian / Sydney |
| **By Direction** | Buy vs Sell performance |
| **By Day** | Best and worst trading days |
| **Psychology** | Discipline scores + flag frequency |

---

## 🗃 Data Models

### Trade
The core model capturing every execution:

```
date, time, session, pair, asset_class, direction
entry_price, stop_loss, take_profit, exit_price, lot_size
balance_before, balance_after, net_pnl, pip_gain_loss, rr_ratio, outcome
strategy, timeframe, confluence_count
emotions_before, emotions_after, discipline_score, flags
notes, screenshot_before, screenshot_after
```

Metrics (`net_pnl`, `pip_gain_loss`, `rr_ratio`, `outcome`) are auto-calculated via `trade.calculate_metrics()`.

---

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/chart-data` | Equity curve + outcome counts (JSON) |
| `POST` | `/journal/import` | Bulk import trades from JSON array |
| `DELETE` | `/delete_trade/<id>` | Delete a trade and revert balance |

---

## 🛡 Security Notes

- CSRF protection enabled globally via Flask-WTF
- `/journal/import` is CSRF-exempt (JSON API, session-authenticated)
- Passwords hashed with Werkzeug `pbkdf2:sha256`
- All trade routes require `@login_required`
- Trade deletion validates ownership before proceeding

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.x, Python 3.13 |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | Flask-Login + Flask-WTF |
| Frontend | Tailwind CSS, Chart.js, Font Awesome |
| Runtime | Termux (Android) / Linux |
| Import | Python `requests` library |

---

## 📋 Requirements

```
flask
flask-sqlalchemy
flask-login
flask-wtf
werkzeug
requests
```

---

## 🗺 Roadmap

- [ ] Screenshot upload and storage per trade
- [ ] CSV export of trade history
- [ ] Multi-account support
- [ ] Weekly/monthly performance summaries
- [ ] Push notifications for streak milestones
- [ ] Local ML model integration for pattern detection

---

## 👤 Author

**Arvine** — built and maintained in Termux on Android.

> *"Track every edge. Review every loss. Compound every lesson."*

