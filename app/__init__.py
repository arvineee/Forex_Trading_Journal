import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions cleanly
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Ensure upload directories exist inside Termux env
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.auth import auth_bp
    from app.journal import journal_bp
    from app.analytics import analytics_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(journal_bp, url_prefix='/')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Global CLI commands for migration/seeding setup
    @app.cli.command("seed-db")
    def seed_db():
        """Seeds database with initialization requirements including a $250 starting balance."""
        db.create_all()
        from app.models import User, Account, Trade
        from datetime import date, time
        
        if not User.query.filter_by(username='trader').first():
            trader = User(username='trader', email='trader@fxjournal.local')
            trader.set_password('password123')
            db.session.add(trader)
            db.session.commit()
            
            # Realizing user seed requirement: Start balance exactly $250 USD
            acc = Account(name='Primary Edge Portfolio', account_type='Live', broker='Pepperstone', initial_balance=250.0, current_balance=272.5, user_id=trader.id)
            db.session.add(acc)
            
            # Injecting sample trades to populate operational visualization dashboards instantly
            t1 = Trade(user_id=trader.id, date=date(2026, 5, 25), time=time(10, 15), session='London', pair='EURUSD', asset_class='Forex', direction='Buy', entry_price=1.0850, stop_loss=1.0820, take_profit=1.0940, exit_price=1.0890, lot_size=0.1, risk_percentage=1.2, balance_before=250.0, balance_after=290.0)
            t1.calculate_metrics()
            
            t2 = Trade(user_id=trader.id, date=date(2026, 5, 26), time=time(15, 30), session='New York', pair='XAUUSD', asset_class='Gold', direction='Sell', entry_price=2350.0, stop_loss=2360.0, take_profit=2320.0, exit_price=2352.5, lot_size=0.05, risk_percentage=1.5, balance_before=290.0, balance_after=272.5)
            t2.calculate_metrics()
            
            db.session.add_all([t1, t2])
            db.session.commit()
            print("Database setup complete with initial $250 profile sample environment data!")

    return app

