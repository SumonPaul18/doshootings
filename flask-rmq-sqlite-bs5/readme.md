এটি একটি সাধারণ টাস্ক ম্যানেজমেন্ট অ্যাপ্লিকেশন তৈরি করার জন্য একটি ধাপে ধাপে গাইড। এই অ্যাপ্লিকেশনটি Flask (Python ওয়েব ফ্রেমওয়ার্ক), SQLite (ডাটাবেস), RabbitMQ (মেসেজ ব্রোকার), এবং Bootstrap 5 (ফ্রন্টএন্ড ডিজাইন) ব্যবহার করে তৈরি করা হবে।

### ধাপ ১: প্রজেক্ট সেটআপ
প্রথমে আপনার প্রজেক্টের জন্য একটি ডিরেক্টরি তৈরি করুন এবং প্রয়োজনীয় প্যাকেজ ইনস্টল করুন।

```bash
mkdir task-management-app
cd task-management-app
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask sqlite3 pika
```

### ধাপ ২: ফাইল স্ট্রাকচার তৈরি করুন
প্রজেক্টের ফাইল স্ট্রাকচার নিম্নরূপ হবে:

```
task-management-app/
│
├── app.py
├── models.py
├── templates/
│   ├── base.html
│   ├── customer.html
│   ├── admin.html
│   └── task.html
├── static/
│   └── styles.css
└── requirements.txt
```

### ধাপ ৩: ডাটাবেস মডেল তৈরি করুন (`models.py`)
এখানে আমরা SQLite ডাটাবেস ব্যবহার করব এবং টাস্ক ম্যানেজমেন্টের জন্য একটি মডেল তৈরি করব।

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    customer_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Task {self.title}>'
```

### ধাপ ৪: Flask অ্যাপ্লিকেশন তৈরি করুন (`app.py`)
এখানে আমরা Flask অ্যাপ্লিকেশন তৈরি করব এবং রাউটস যোগ করব।

```python
from flask import Flask, render_template, request, redirect, url_for
from models import db, Task
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_updates')

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/customer', methods=['GET', 'POST'])
def customer():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        customer_id = 1  # Assuming a single customer for simplicity
        new_task = Task(title=title, description=description, customer_id=customer_id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('customer'))
    tasks = Task.query.filter_by(customer_id=1).all()
    return render_template('customer.html', tasks=tasks)

@app.route('/admin')
def admin():
    tasks = Task.query.all()
    return render_template('admin.html', tasks=tasks)

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get(task_id)
    task.status = 'Completed'
    db.session.commit()
    
    # Send message to RabbitMQ
    channel.basic_publish(exchange='',
                          routing_key='task_updates',
                          body=f'Task {task_id} completed')
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```

### ধাপ ৫: টেমপ্লেট ফাইল তৈরি করুন (`templates/`)
#### `base.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

#### `customer.html`
```html
{% extends 'base.html' %}

{% block content %}
<h1>Customer Portal</h1>
<form method="POST">
    <div class="mb-3">
        <label for="title" class="form-label">Task Title</label>
        <input type="text" class="form-control" id="title" name="title" required>
    </div>
    <div class="mb-3">
        <label for="description" class="form-label">Task Description</label>
        <textarea class="form-control" id="description" name="description" rows="3" required></textarea>
    </div>
    <button type="submit" class="btn btn-primary">Submit Task</button>
</form>

<h2>Your Tasks</h2>
<ul>
    {% for task in tasks %}
    <li>{{ task.title }} - {{ task.status }}</li>
    {% endfor %}
</ul>
{% endblock %}
```

#### `admin.html`
```html
{% extends 'base.html' %}

{% block content %}
<h1>Admin Portal</h1>
<table class="table">
    <thead>
        <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Status</th>
            <th>Action</th>
        </tr>
    </thead>
    <tbody>
        {% for task in tasks %}
        <tr>
            <td>{{ task.title }}</td>
            <td>{{ task.description }}</td>
            <td>{{ task.status }}</td>
            <td>
                {% if task.status == 'Pending' %}
                <a href="{{ url_for('complete_task', task_id=task.id) }}" class="btn btn-success">Complete</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

### ধাপ ৬: RabbitMQ কনজিউমার তৈরি করুন
একটি আলাদা Python স্ক্রিপ্ট তৈরি করুন (`consumer.py`) যা RabbitMQ থেকে মেসেজ গ্রহণ করবে এবং টাস্ক আপডেট দেখাবে।

```python
import pika

def callback(ch, method, properties, body):
    print(f"Received {body}")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_updates')

channel.basic_consume(queue='task_updates',
                      on_message_callback=callback,
                      auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

### ধাপ ৭: অ্যাপ্লিকেশন রান করুন
1. Flask অ্যাপ্লিকেশন রান করুন:
   ```bash
   python app.py
   ```

2. RabbitMQ কনজিউমার রান করুন:
   ```bash
   python consumer.py
   ```

3. ব্রাউজারে `http://127.0.0.1:5000/customer` এ যান এবং টাস্ক জমা দিন।

4. অ্যাডমিন প্যানেলে (`http://127.0.0.1:5000/admin`) টাস্ক কমপ্লিট করুন এবং RabbitMQ কনজিউমার লগ দেখুন।

### ধাপ ৮: স্টাইলিং (ঐচ্ছিক)
Bootstrap 5 ব্যবহার করে আপনি আপনার অ্যাপ্লিকেশনটি স্টাইল করতে পারেন। `static/styles.css` ফাইলে কাস্টম CSS যোগ করতে পারেন।

### ধাপ ৯: ডিপ্লয়মেন্ট (ঐচ্ছিক)
আপনি এই অ্যাপ্লিকেশনটি Heroku, PythonAnywhere, বা অন্য কোনো হোস্টিং সার্ভিসে ডিপ্লয় করতে পারেন।

এই গাইডটি অনুসরণ করে আপনি একটি সাধারণ টাস্ক ম্যানেজমেন্ট অ্যাপ্লিকেশন তৈরি করতে পারবেন। এটি একটি বেসিক ইমপ্লিমেন্টেশন, আপনি চাইলে এটিকে আরও উন্নত করতে পারেন।