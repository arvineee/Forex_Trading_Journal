from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_pic = db.Column(db.String(255), default='default_profile.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='owner', lazy=True, cascade="all, delete-orphan")
    trades = db.relationship('Trade', backref='trader', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    account_type = db.Column(db.String(20), default='Live') # Demo / Live
    broker = db.Column(db.String(64), default='Generic Broker')
    currency = db.Column(db.String(10), default='USD')
    initial_balance = db.Column(db.Float, default=250.0)
    current_balance = db.Column(db.Float, default=250.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Details
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    time = db.Column(db.Time, nullable=False)
    session = db.Column(db.String(20), nullable=False) # London, New York, Asian, Sydney
    pair = db.Column(db.String(20), nullable=False, index=True) # e.g. EURUSD, XAUUSD
    asset_class = db.Column(db.String(20), default='Forex') # Forex, Gold, Indices, Crypto
    direction = db.Column(db.String(10), nullable=False) # Buy / Sell
    
    # Execution Architecture
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=False)
    take_profit = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=False)
    lot_size = db.Column(db.Float, nullable=False)
    risk_percentage = db.Column(db.Float, default=1.0)
    
    # Financial Impact Metrics
    balance_before = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    pip_gain_loss = db.Column(db.Float, default=0.0)
    rr_ratio = db.Column(db.Float, default=0.0)
    net_pnl = db.Column(db.Float, default=0.0)
    outcome = db.Column(db.String(15), default='Break-even') # Win, Loss, Break-even
    
    # Strategy & Parameters
    strategy = db.Column(db.String(60), default='Price Action')
    timeframe = db.Column(db.String(10), default='H1')
    confluence_count = db.Column(db.Integer, default=1)
    
    # Psychology Metrics
    emotions_before = db.Column(db.String(30))
    emotions_after = db.Column(db.String(30))
    discipline_score = db.Column(db.Integer, default=5) # 1-5 scale
    flags = db.Column(db.String(100), default='') # JSON or comma-separated string e.g., 'FOMO, Revenge'
    
    # Context & Journaling
    notes = db.Column(db.Text)
    screenshot_before = db.Column(db.String(255))
    screenshot_after = db.Column(db.String(255))

    def calculate_metrics(self):
        # Auto-compute net P&L
        self.net_pnl = self.balance_after - self.balance_before
        
        # Derive outcome state
        if self.net_pnl > 0.01:
            self.outcome = 'Win'
        elif self.net_pnl < -0.01:
            self.outcome = 'Loss'
        else:
            self.outcome = 'Break-even'
            
        # Standard Pip Engine Logic
        is_jpy = any(jpy_s in self.pair.upper() for jpy_s in ['JPY', 'XAU', 'GOLD'])
        multiplier = 100.0 if is_jpy else 10000.0
        
        if self.direction.lower() == 'buy':
            self.pip_gain_loss = (self.exit_price - self.entry_price) * multiplier
            risk_pips = (self.entry_price - self.stop_loss) * multiplier
            target_pips = (self.take_profit - self.entry_price) * multiplier
        else:
            self.pip_gain_loss = (self.entry_price - self.exit_price) * multiplier
            risk_pips = (self.stop_loss - self.entry_price) * multiplier
            target_pips = (self.entry_price - self.take_profit) * multiplier
            
        if risk_pips > 0:
            self.rr_ratio = round(target_pips / risk_pips, 2)
        else:
            self.rr_ratio = 0.0

