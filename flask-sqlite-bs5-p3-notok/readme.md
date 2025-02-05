আমি আপনাকে ধাপে ধাপে Flask, SQLite এবং Bootstrap 5 ব্যবহার করে একটি সাপোর্ট টিকেট সিস্টেম বানানোর কোড দিচ্ছি। এই সিস্টেমটি স্বয়ংক্রিয় সমাধান সাজেস্ট করবে এবং ইঞ্জিনিয়ারদের জন্য প্রাসঙ্গিক তথ্য প্রদর্শন করবে।

ধাপ ১: প্রয়োজনীয় প্যাকেজ ইন্সটল করুন
```bash
pip install flask flask-sqlalchemy
```

ধাপ ২: অ্যাপ্লিকেশন স্ট্রাকচার তৈরি করুন
```
your_project_folder/
├── app.py
├── database.db
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── create_ticket.html
    └── ticket.html
```

ধাপ ৩: app.py ফাইল তৈরি করুন
```python
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
```

ধাপ ৪: টেমপ্লেট ফাইল তৈরি করুন

base.html (বুটস্ট্রাপ 5 সহ বেস টেমপ্লেট)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>সাপোর্ট সিস্টেম</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">সাপোর্ট সিস্টেম</a>
        </div>
    </nav>
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

dashboard.html
```html
{% extends "base.html" %}

{% block content %}
<h2>সকল টিকেট</h2>
<a href="{{ url_for('create_ticket') }}" class="btn btn-primary mb-3">নতুন টিকেট তৈরি করুন</a>

<div class="list-group">
    {% for ticket in tickets %}
    <a href="{{ url_for('view_ticket', ticket_id=ticket.id) }}" 
       class="list-group-item list-group-item-action {% if ticket.status == 'Auto-Resolved' %}list-group-item-success{% endif %}">
        <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{ ticket.service_type }}</h5>
            <small>স্ট্যাটাস: {{ ticket.status }}</small>
        </div>
        <p class="mb-1">{{ ticket.problem_description|truncate(50) }}</p>
    </a>
    {% endfor %}
</div>
{% endblock %}
```

create_ticket.html
```html
{% extends "base.html" %}

{% block content %}
<h2>নতুন টিকেট তৈরি করুন</h2>
<form method="POST">
    <div class="mb-3">
        <label class="form-label">সার্ভিস ধরণ</label>
        <select name="service_type" class="form-select" required>
            <option value="মেইল">মেইল</option>
            <option value="ইন্টারনেট">ইন্টারনেট</option>
            <option value="সফটওয়্যার">সফটওয়্যার</option>
        </select>
    </div>
    <div class="mb-3">
        <label class="form-label">সমস্যার বর্ণনা</label>
        <textarea name="problem" class="form-control" rows="3" required></textarea>
    </div>
    <div class="mb-3">
        <label class="form-label">কাস্টমার আইডি</label>
        <input type="number" name="customer_id" class="form-control" required>
    </div>
    <button type="submit" class="btn btn-primary">টিকেট সাবমিট করুন</button>
</form>
{% endblock %}
```

ticket.html
```html
{% extends "base.html" %}

{% block content %}
<div class="card">
    <div class="card-header">
        টিকেট #{{ ticket.id }}
    </div>
    <div class="card-body">
        <h5 class="card-title">{{ ticket.service_type }} সমস্যা</h5>
        <p class="card-text">{{ ticket.problem_description }}</p>
        
        {% if ticket.status == 'Auto-Resolved' %}
            <div class="alert alert-success">
                <h5>স্বয়ংক্রিয় সমাধান:</h5>
                {{ ticket.solution }}
            </div>
        {% else %}
            <div class="alert alert-warning">
                <h5>অ্যাসাইন্ড ইঞ্জিনিয়ার:</h5>
                {% if engineer %}
                    <p>নাম: {{ engineer.name }}</p>
                    <p>যোগাযোগ: {{ engineer.contact }}</p>
                {% else %}
                    <p>কোন ইঞ্জিনিয়ার অ্যাসাইন করা হয়নি</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</div>
<a href="{{ url_for('dashboard') }}" class="btn btn-secondary mt-3">ফিরে যান</a>
{% endblock %}
```

এই কোড রান করার পর আপনি পাবেন:

1. একটি ড্যাশবোর্ড যেখানে সকল টিকেট দেখা যাবে
2. নতুন টিকেট তৈরি করার ফর্ম
3. স্বয়ংক্রিয় সমাধান সিস্টেম
4. ইঞ্জিনিয়ার অ্যাসাইনমেন্ট সিস্টেম
5. টিকেট ডিটেলস ভিউ

বিশেষ বৈশিষ্ট্য:
- স্বয়ংক্রিয় সমাধান ডেটাবেসে ম্যাচ করলে স্বয়ংক্রিয়ভাবে সমাধান দেখাবে
- সার্ভিস টাইপ অনুযায়ী উপযুক্ত ইঞ্জিনিয়ার অ্যাসাইন করবে
- রেস্পন্সিভ ডিজাইন (বুটস্ট্রাপ 5)
- টিকেট স্ট্যাটাস ট্র্যাকিং

এই সিস্টেমটি চালানোর জন্য:
1. কোডটি সেভ করুন
2. টার্মিনালে `python app.py` রান করুন
3. ব্রাউজারে http://localhost:5000 ভিজিট করুন

আপনার প্রয়োজন অনুযায়ী মডেল এবং টেমপ্লেট পরিবর্তন করতে পারেন। প্রাথমিকভাবে কিছু ডেমো ডেটা যোগ করা আছে ইঞ্জিনিয়ারদের জন্য।