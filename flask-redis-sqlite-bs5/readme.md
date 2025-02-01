আপনার জন্য সম্পূর্ণ কোড নিচে দেওয়া হলো। এই কোডটি Flask, Redis, SQLite, Bootstrap 5, এবং Docker ব্যবহার করে একটি টেকনিক্যাল সাপোর্ট সিস্টেম অ্যাপ্লিকেশন তৈরি করে। এটি সর্বশেষ আপডেট অনুযায়ী সাজানো হয়েছে।

---

### ধাপ ১: প্রজেক্ট স্ট্রাকচার

প্রজেক্টের ফাইল এবং ফোল্ডার গুলো নিম্নরূপ:

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
│   │   ├── login.html
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

### ধাপ ২: `config.py`

```python
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
```

---

### ধাপ ৩: `app/__init__.py`

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import redis
from flask_login import LoginManager

db = SQLAlchemy()
bootstrap = Bootstrap()
redis_client = redis.Redis.from_url('redis://localhost:6379/0')
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app.routes import main_routes
    app.register_blueprint(main_routes)

    return app
```

---

### ধাপ ৪: `app/models.py`

```python
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # client or engineer

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

### ধাপ ৫: `app/routes.py`

```python
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
```

---

### ধাপ ৬: টেমপ্লেট ফাইল

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

#### `app/templates/index.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Welcome to Technical Support System</h1>
<a href="{{ url_for('main.login') }}" class="btn btn-primary">Login</a>
{% endblock %}
```

#### `app/templates/login.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Login</h1>
<form method="POST">
    <div class="mb-3">
        <label for="username" class="form-label">Username</label>
        <input type="text" class="form-control" id="username" name="username" required>
    </div>
    <div class="mb-3">
        <label for="password" class="form-label">Password</label>
        <input type="password" class="form-control" id="password" name="password" required>
    </div>
    <button type="submit" class="btn btn-primary">Login</button>
</form>
{% endblock %}
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

#### `app/templates/create_ticket.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Create Ticket</h1>
<form method="POST">
    <div class="mb-3">
        <label for="title" class="form-label">Title</label>
        <input type="text" class="form-control" id="title" name="title" required>
    </div>
    <div class="mb-3">
        <label for="description" class="form-label">Description</label>
        <textarea class="form-control" id="description" name="description" required></textarea>
    </div>
    <button type="submit" class="btn btn-primary">Submit</button>
</form>
{% endblock %}
```

#### `app/templates/ticket_details.html`
```html
{% extends "base.html" %}

{% block content %}
<h1>Ticket Details</h1>
<h2>{{ ticket.title }}</h2>
<p>{{ ticket.description }}</p>
<p>Status: {{ ticket.status }}</p>
<p>Created by: {{ ticket.client.username }}</p>
{% if ticket.engineer %}
<p>Assigned to: {{ ticket.engineer.username }}</p>
{% endif %}
{% endblock %}
```

---

### ধাপ ৭: `Dockerfile`

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
```

---

### ধাপ ৮: `docker-compose.yml`

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

### ধাপ ৯: `requirements.txt`

```
Flask==2.0.1
redis==4.1.0
Flask-SQLAlchemy==2.5.1
Flask-Bootstrap==3.3.7.1
Flask-Login==0.5.0
python-dotenv==0.19.0
```

---

### ধাপ ১০: অ্যাপ্লিকেশন রান করুন

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

এই অ্যাপ্লিকেশনটি আপনার প্রয়োজন অনুযায়ী আরো উন্নত করা যাবে।