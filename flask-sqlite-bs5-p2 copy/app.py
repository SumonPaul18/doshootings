from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///p3.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this for production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in'
login_manager.login_message_category = 'warning'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='customer')  # customer, engineer, admin
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open', nullable=False)  # Open, In Progress, Resolved
    priority = db.Column(db.String(20), default='Normal')  # Urgent, High, Normal
    solution = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    engineer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(datetime.timezone.utc))

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Common Validation Function
def validate_registration(email, password, name):
    errors = []
    if not email or '@' not in email:
        errors.append('Please enter a valid email address')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    if not name.strip():
        errors.append('Please enter your name')
    return errors

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid login credentials!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        role = request.form.get('role', 'customer')
        
        errors = validate_registration(email, password, name)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('This email is already registered', 'warning')
            return redirect(url_for('register'))
        
        try:
            new_user = User(
                email=email,
                password=generate_password_hash(password),
                name=name,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f'Registration error: {str(e)}')
            flash('There was an issue with registration', 'danger')
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out', 'success')
    return redirect(url_for('login'))

# Dashboard and Ticket Management Routes
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if current_user.role == 'customer':
            tickets = Ticket.query.filter_by(customer_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        elif current_user.role == 'engineer':
            tickets = Ticket.query.filter_by(engineer_id=current_user.id).order_by(Ticket.priority.desc()).all()
        elif current_user.role == 'admin':
            tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
        else:
            return redirect(url_for('login'))
            
        return render_template('dashboard.html', tickets=tickets)
    
    except Exception as e:
        app.logger.error(f'Dashboard error: {str(e)}')
        flash('There was an issue loading the dashboard', 'danger')
        return redirect(url_for('login'))

@app.route('/ticket/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if current_user.role != 'customer':
        flash('You do not have permission to create tickets', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            service_type = request.form.get('service_type', '').strip()
            description = request.form.get('description', '').strip()
            priority = request.form.get('priority', 'Normal')
            
            if not all([title, service_type, description]):
                flash('Please fill out all required fields', 'danger')
                return redirect(url_for('create_ticket'))
                
            new_ticket = Ticket(
                title=title,
                service_type=service_type,
                description=description,
                priority=priority,
                customer_id=current_user.id
            )
            
            db.session.add(new_ticket)
            db.session.commit()
            flash('Ticket created successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Ticket creation error: {str(e)}')
            flash('There was an issue creating the ticket', 'danger')

    services = Service.query.all()
    return render_template('create_ticket.html', services=services)

@app.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if current_user.role == 'customer' and ticket.customer_id != current_user.id:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        ticket.title = request.form.get('title', ticket.title).strip()
        ticket.description = request.form.get('description', ticket.description).strip()
        ticket.priority = request.form.get('priority', ticket.priority)
        
        try:
            db.session.commit()
            flash('Ticket updated successfully!', 'success')
            return redirect(url_for('view_ticket', ticket_id=ticket_id))
        
        except Exception as e:
            app.logger.error(f'Ticket update error: {str(e)}')
            flash('There was an issue updating the ticket.', 'danger')

    services = Service.query.all()
    return render_template('edit_ticket.html', ticket=ticket, services=services)

@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if current_user.role == 'customer' and ticket.customer_id != current_user.id:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('ticket.html', ticket=ticket)

# Advanced Features
@app.route('/ticket/<int:ticket_id>/resolve', methods=['POST'])
@login_required
def resolve_ticket(ticket_id):
    if current_user.role != 'engineer':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))

    ticket = Ticket.query.get_or_404(ticket_id)
    
    solution = request.form.get('solution', '').strip()

    if not solution:
        flash("Please provide a solution description", "danger")
        return redirect(url_for("view_ticket", ticket_id=ticket_id))

    try:
        ticket.solution = solution
        ticket.status = 'Resolved'
        ticket.engineer_id = current_user.id

        notification = Notification(
            content=f'Ticket #{ticket_id} has been resolved',
            user_id=ticket.customer_id
        )

        db.session.add(notification)
        db.session.commit()
        flash('Ticket resolved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Resolution error: {str(e)}')
        flash('There was an issue resolving the ticket', 'danger')

    return redirect(url_for("view_ticket", ticket_id=ticket_id))

@app.route('/notification/<int:notification_id>/mark-read')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))

    notification.is_read = True
    db.session.commit()

    flash("Notification marked as read", "success")
    return redirect(url_for("profile"))

# Database Setup Command (optional for initial setup)
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()

        # Optionally add demo services or initial data here
        if not Service.query.first():
            services_data = [
                Service(name='Email'),
                Service(name='Internet'),
                Service(name='Software'),
                Service(name='Hardware'),
            ]
            for service in services_data:
                db.session.add(service)
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables are created on startup.
        db.create_all()  # Ensure database tables are created on startup.
    app.run(debug=True)  # Start the Flask application.
