from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Ticket, Service, Notification

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if current_user.role != 'customer':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        service_type = request.form.get('service_type')
        description = request.form.get('description')

        if not title or not service_type or not description:
            flash('All fields are required!')
            return redirect(url_for('tickets.create_ticket'))

        new_ticket = Ticket(
            title=title,
            service_type=service_type,
            description=description,
            customer_id=current_user.id,
            status='Open'
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        flash('Ticket created successfully!')
        return redirect(url_for('dashboard'))
    
    services = Service.query.all()
    return render_template('create_ticket.html', services=services)

@tickets_bp.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'customer' and ticket.customer_id != current_user.id:
        return redirect(url_for('dashboard'))
    return render_template('ticket.html', ticket=ticket)

@tickets_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.customer_id != current_user.id:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        db.session.commit()
        return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))
    
    services = Service.query.all()
    return render_template('edit_ticket.html', ticket=ticket, services=services)

@tickets_bp.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'engineer' and ticket.engineer_id == current_user.id:
        ticket.solution = request.form['solution']
        ticket.status = 'Resolved'
        
        notification = Notification(
            content=f'Your ticket #{ticket_id} has been resolved',
            user_id=ticket.customer_id
        )
        db.session.add(notification)
        db.session.commit()
    
    elif current_user.role == 'customer' and ticket.status == 'Resolved':
        ticket.status = 'Confirmed'
        db.session.commit()
    
    return redirect(url_for('tickets.view_ticket', ticket_id=ticket_id))