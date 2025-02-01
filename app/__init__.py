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