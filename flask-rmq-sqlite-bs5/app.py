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