আপনি একটি টেকনিক্যাল সাপোর্ট সিস্টেম অ্যাপ্লিকেশন তৈরি করতে চাচ্ছেন, যেখানে ক্লায়েন্টরা তাদের প্রোব্লেম শেয়ার করবে এবং সেই প্রোব্লেম গুলো অটোমেটিক্যালি ইঞ্জিনিয়ারদের মধ্যে ভাগ হয়ে যাবে। এই অ্যাপ্লিকেশনটি তৈরি করতে আমরা Flask, Redis, SQLite, এবং Bootstrap 5 ব্যবহার করব। এছাড়াও, আমরা Docker ব্যবহার করে অ্যাপ্লিকেশনটি কন্টেইনারাইজ করব।

এই অ্যাপ্লিকেশনের মূল ফিচার গুলো হবে:
1. **ক্লায়েন্ট রেজিস্ট্রেশন এবং লগইন**।
2. **প্রোব্লেম টিকেট তৈরি**।
3. **ইঞ্জিনিয়ারদের মধ্যে প্রোব্লেম টিকেট অটোমেটিক্যালি অ্যাসাইন করা**।
4. **টিকেট স্ট্যাটাস আপডেট**।
5. **ক্লায়েন্ট এবং ইঞ্জিনিয়ারদের জন্য আলাদা ড্যাশবোর্ড**।

---

### ধাপ ১: প্রজেক্ট স্ট্রাকচার তৈরি করুন

প্রজেক্টের জন্য নিচের ফাইল এবং ফোল্ডার গুলো তৈরি করুন:

```
flask_app/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── client_dashboard.html
│   │   ├── engineer_dashboard.html
│   │   ├── create_ticket.html
│   │   ├── ticket_details.html
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│
├── config.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
```

---

### ধাপ ২: ডেটাবেস মডেল তৈরি করুন

`app/models.py` ফাইলে ডেটাবেস মডেল গুলো ডিফাইন করুন:

```python
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # client or engineer

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')  # Open, In Progress, Closed
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    engineer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    client = db.relationship('User', foreign_keys=[client_id])
    engineer = db.relationship('User', foreign_keys=[engineer_id])
```

---

### ধাপ ৩: রাউট এবং লজিক তৈরি করুন

`app/routes.py` ফাইলে রাউট এবং লজিক ডিফাইন করুন:

```python
from flask import render_template, request, redirect, url_for, flash
from app import db, redis_client
from app.models import User, Ticket
from flask import Blueprint
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

main_routes = Blueprint('main', __name__)

# লগইন ম্যানেজার সেটআপ
login_manager = LoginManager()
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
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

def assign_ticket_to_engineer(ticket_id):
    # Redis ব্যবহার করে ইঞ্জিনিয়ারদের মধ্যে টিকেট অ্যাসাইন করুন
    engineers = User.query.filter_by(role='engineer').all()
    if engineers:
        engineer_id = redis_client.rpop('engineer_queue') or engineers[0].id
        redis_client.lpush('engineer_queue', engineer_id)
        ticket = Ticket.query.get(ticket_id)
        ticket.engineer_id = engineer_id
        ticket.status = 'In Progress'
        db.session.commit()
```

---

### ধাপ ৪: টেমপ্লেট তৈরি করুন

#### `app/templates/base.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technical Support System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

#### `app/templates/client_dashboard.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Client Dashboard</h1>
<a href="{{ url_for('main.create_ticket') }}" class="btn btn-primary">Create Ticket</a>
<h2>Your Tickets</h2>
<ul>
    {% for ticket in tickets %}
    <li>
        <a href="{{ url_for('main.ticket_details', ticket_id=ticket.id) }}">{{ ticket.title }}</a> - {{ ticket.status }}
    </li>
    {% endfor %}
</ul>
{% endblock %}
```

#### `app/templates/engineer_dashboard.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Engineer Dashboard</h1>
<h2>Assigned Tickets</h2>
<ul>
    {% for ticket in tickets %}
    <li>
        <a href="{{ url_for('main.ticket_details', ticket_id=ticket.id) }}">{{ ticket.title }}</a> - {{ ticket.status }}
    </li>
    {% endfor %}
</ul>
{% endblock %}
```

---

### ধাপ ৫: Docker এবং Redis কনফিগার করুন

`docker-compose.yml` ফাইলে Redis এবং Flask অ্যাপ্লিকেশন কনফিগার করুন:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    depends_on:
      - redis
      - db

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  db:
    image: sqlite:latest
    volumes:
      - ./data:/data
```

---

### ধাপ ৬: অ্যাপ্লিকেশন রান করুন

```bash
docker-compose up --build
```

এখন আপনি ব্রাউজারে `http://localhost:5000` এ গিয়ে অ্যাপ্লিকেশনটি ব্যবহার করতে পারবেন।

---

### সারসংক্ষেপ
- ক্লায়েন্টরা টিকেট তৈরি করতে পারবে।
- টিকেট গুলো অটোমেটিক্যালি ইঞ্জিনিয়ারদের মধ্যে অ্যাসাইন হবে।
- Redis ব্যবহার করে ইঞ্জিনিয়ারদের মধ্যে টিকেট ভাগ করা হবে।
- ক্লায়েন্ট এবং ইঞ্জিনিয়ারদের জন্য আলাদা ড্যাশবোর্ড থাকবে।

এই অ্যাপ্লিকেশনটি আপনার প্রয়োজন অনুযায়ী আরো উন্নত করা যাবে, যেমন নোটিফিকেশন সিস্টেম, টিকেট প্রায়োরিটি, এবং রিপোর্টিং ফিচার অ্যাড করা।