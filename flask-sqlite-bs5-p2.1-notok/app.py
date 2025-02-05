from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ডেটাবেস মডেল
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # customer, engineer, admin
    name = db.Column(db.String(100))
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    service_type = db.Column(db.String(50))
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='Open')  # Open, In Progress, Resolved, Confirmed
    solution = db.Column(db.String(500))
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    engineer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# অথেন্টিকেশন রাউটস
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        role = request.form['role']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!')
            return redirect(url_for('register'))
        
        new_user = User(email=email, password=password, name=name, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ড্যাশবোর্ড রাউটস
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
    return redirect(url_for('login'))

# টিকেট ম্যানেজমেন্ট রাউটস
@app.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if current_user.role != 'customer':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        service_type = request.form.get('service_type')
        description = request.form.get('description')

        # Validate that all fields are filled
        if not title or not service_type or not description:
            flash('All fields are required!')
            return redirect(url_for('create_ticket'))

        new_ticket = Ticket(
            title=title,
            service_type=service_type,
            description=description,
            customer_id=current_user.id,  # Automatically associate with logged-in user
            status='Open'
        )
        
        db.session.add(new_ticket)
        
        try:
            db.session.commit()
            flash('Ticket created successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the ticket. Please try again.')
    
    services = Service.query.all()
    return render_template('create_ticket.html', services=services)

    if current_user.role != 'customer':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        service_type = request.form.get('service_type')
        description = request.form.get('description')
        
        new_ticket = Ticket(
            title=title,
            service_type=service_type,
            description=description,
            customer_id=current_user.id,
            status='Open'
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    services = Service.query.all()
    return render_template('create_ticket.html', services=services)

@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket or (current_user.role == 'customer' and ticket.customer_id != current_user.id):
        return redirect(url_for('dashboard'))
    return render_template('ticket.html', ticket=ticket)

@app.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.customer_id != current_user.id:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        db.session.commit()
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    services = Service.query.all()
    return render_template('edit_ticket.html', ticket=ticket, services=services)

@app.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if current_user.role == 'engineer' and ticket.engineer_id == current_user.id:
        ticket.solution = request.form['solution']
        ticket.status = 'Resolved'
        
        # নোটিফিকেশন তৈরি করুন
        notification = Notification(
            content=f'Your ticket #{ticket_id} has been resolved',
            user_id=ticket.customer_id
        )
        db.session.add(notification)
        db.session.commit()
    
    elif current_user.role == 'customer' and ticket.status == 'Resolved':
        ticket.status = 'Confirmed'
        db.session.commit()
    
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

# প্রোফাইল এবং নোটিফিকেশন
@app.route('/profile')
@login_required
def profile():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).all()
    return render_template('profile.html', notifications=notifications)

@app.route('/mark_notification/<int:notification_id>')
@login_required
def mark_notification(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('profile'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # ডেমো সার্ভিস যোগ করুন
        if not Service.query.first():
            services = ['মেইল', 'ইন্টারনেট', 'সফটওয়্যার', 'অটোমেশন']
            for service in services:
                db.session.add(Service(name=service))
            db.session.commit()
        app.run(debug=True)