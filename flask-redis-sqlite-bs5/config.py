from dotenv import load_dotenv
import os

load_dotenv()  # .env ফাইল থেকে এনভায়রনমেন্ট ভেরিয়েবল লোড করে

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # .env ফাইলের SECRET_KEY ব্যবহার করবে, না থাকলে ডিফল্ট ভ্যালু ব্যবহার করবে
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')