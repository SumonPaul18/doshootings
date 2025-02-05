from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from models import db, User, Service, Ticket
from auth import auth_bp
from tickets import tickets_bp
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(tickets_bp)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'customer':
        tickets = Ticket.query.filter_by(customer_id=current_user.id).all()
        return render_template('customer_dashboard.html', tickets=tickets)
    elif current_user.role == 'engineer':
        tickets = Ticket.query.filter_by(engineer_id=current_user.id).all()
        return render_template('engineer_dashboard.html', tickets=tickets)
    elif current_user.role == 'admin':
        tickets = Ticket.query.all()
        return render_template('admin_dashboard.html', tickets=tickets)
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Service.query.first():
            services = ['মেইল', 'ইন্টারনেট', 'সফটওয়্যার', 'অটোমেশন']
            for service in services:
                db.session.add(Service(name=service))
            db.session.commit()
    app.run(debug=True)