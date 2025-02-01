from flask import render_template, request, redirect, url_for, flash
from app import db, redis_client
from app.models import User, Ticket
from flask import Blueprint
from flask_login import login_user, logout_user, login_required, current_user

main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'client':
                return redirect(url_for('main.client_dashboard'))
            else:
                return redirect(url_for('main.engineer_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@main_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_routes.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        return redirect(url_for('main.index'))
    tickets = Ticket.query.filter_by(client_id=current_user.id).all()
    return render_template('client_dashboard.html', tickets=tickets)

@main_routes.route('/engineer/dashboard')
@login_required
def engineer_dashboard():
    if current_user.role != 'engineer':
        return redirect(url_for('main.index'))
    tickets = Ticket.query.filter_by(engineer_id=current_user.id).all()
    return render_template('engineer_dashboard.html', tickets=tickets)

@main_routes.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if current_user.role != 'client':
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ticket = Ticket(title=title, description=description, client_id=current_user.id)
        db.session.add(ticket)
        db.session.commit()
        assign_ticket_to_engineer(ticket.id)
        flash('Ticket created successfully')
        return redirect(url_for('main.client_dashboard'))
    return render_template('create_ticket.html')

@main_routes.route('/ticket/<int:ticket_id>')
@login_required
def ticket_details(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template('ticket_details.html', ticket=ticket)

def assign_ticket_to_engineer(ticket_id):
    engineers = User.query.filter_by(role='engineer').all()
    if engineers:
        engineer_id = redis_client.rpop('engineer_queue') or engineers[0].id
        redis_client.lpush('engineer_queue', engineer_id)
        ticket = Ticket.query.get(ticket_id)
        ticket.engineer_id = engineer_id
        ticket.status = 'In Progress'
        db.session.commit()