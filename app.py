from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
import string
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Your email password
mail = Mail(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Database setup
db = SQLAlchemy(app)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Email model
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(120), unique=True, nullable=False)
    messages = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Funny email extensions
FUNNY_EXTENSIONS = ['@funny.com', '@sillymail.com', '@crazyemail.net', '@jokemail.org', '@wacky.net']

# Load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to generate a random email
def generate_random_email():
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    extension = random.choice(FUNNY_EXTENSIONS)
    return random_name + extension

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login failed! Please check your credentials.', 'danger')
    return render_template('login.html')

@app.route('/user_dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    if request.method == 'POST':
        email_address = generate_random_email()
        new_email = Email(address=email_address, messages="")
        db.session.add(new_email)
        db.session.commit()
        
        # Send verification email
        msg = Message('Verify Your Temporary Email', sender='your_email@gmail.com', recipients=[email_address])
        msg.body = f'Your temporary email is: {email_address}\n\nPlease check for incoming messages!'
        mail.send(msg)

        return redirect(url_for('inbox', email=email_address))
    return render_template('user_dashboard.html')

@app.route('/inbox/<email>')
@login_required
def inbox(email):
    messages = Email.query.filter_by(address=email).first()
    if messages:
        # Remove old messages (older than 1 hour)
        if datetime.utcnow() - messages.created_at > timedelta(hours=1):
            db.session.delete(messages)
            db.session.commit()
            flash('Your temporary email has expired and been deleted.', 'info')
            return redirect(url_for('user_dashboard'))
    return render_template('inbox.html', email=email, messages=messages)

@app.route('/send_message/<email>', methods=['POST'])
@login_required
def send_message(email):
    message_content = request.form.get('message')
    email_record = Email.query.filter_by(address=email).first()
    if email_record:
        email_record.messages += f"{message_content}\n"
        db.session.commit()
    return redirect(url_for('inbox', email=email))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
