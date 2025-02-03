from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)

# ডেটাবেস মডেল
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    services = db.relationship('Service', backref='customer', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))  # মেইল, ইন্টারনেট, সফটওয়্যার ইত্যাদি
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50))
    description = db.Column(db.String(200))
    solution = db.Column(db.String(500))
    escalation_path = db.Column(db.String(100))

class Engineer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    expertise = db.Column(db.String(100))
    contact = db.Column(db.String(20))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    service_type = db.Column(db.String(50))
    problem_description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='Open')
    solution = db.Column(db.String(500))
    assigned_engineer = db.Column(db.Integer, db.ForeignKey('engineer.id'))

# রাউটস
@app.route('/')
def dashboard():
    tickets = Ticket.query.all()
    return render_template('dashboard.html', tickets=tickets)

@app.route('/create_ticket', methods=['GET', 'POST'])
def create_ticket():
    if request.method == 'POST':
        service_type = request.form['service_type']
        problem = request.form['problem']
        customer_id = request.form['customer_id']
        
        # স্বয়ংক্রিয় সমাধান চেক করুন
        auto_solution = Problem.query.filter_by(service_type=service_type, description=problem).first()
        
        new_ticket = Ticket(
            service_type=service_type,
            problem_description=problem,
            customer_id=customer_id,
            solution=auto_solution.solution if auto_solution else None,
            status='Auto-Resolved' if auto_solution else 'Open'
        )
        
        if not auto_solution:
            # ইঞ্জিনিয়ার অ্যাসাইন করুন
            suitable_engineer = Engineer.query.filter_by(expertise=service_type).first()
            if suitable_engineer:
                new_ticket.assigned_engineer = suitable_engineer.id
        
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('create_ticket.html')

@app.route('/ticket/<int:ticket_id>')
def view_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    engineer = Engineer.query.get(ticket.assigned_engineer) if ticket.assigned_engineer else None
    return render_template('ticket.html', ticket=ticket, engineer=engineer)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # ডেমো ডেটা যোগ করুন
        if not Engineer.query.first():
            engineers = [
                Engineer(name="আব্দুল করিম", expertise="মেইল", contact="0171XXXXXXX"),
                Engineer(name="রহিমা আক্তার", expertise="ইন্টারনেট", contact="0182XXXXXXX"),
                Engineer(name="সামিউল ইসলাম", expertise="সফটওয়্যার", contact="0191XXXXXXX")
            ]
            db.session.bulk_save_objects(engineers)
            db.session.commit()
        app.run(debug=True)