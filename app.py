from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Email model
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(120), unique=True, nullable=False)
    messages = db.Column(db.Text, nullable=True)

# Funny email extensions
FUNNY_EXTENSIONS = ['@funny.com', '@sillymail.com', '@crazyemail.net', '@jokemail.org', '@wacky.net']

# Function to generate a random email
def generate_random_email():
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    extension = random.choice(FUNNY_EXTENSIONS)
    return random_name + extension

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email_address = generate_random_email()
        new_email = Email(address=email_address, messages="")
        db.session.add(new_email)
        db.session.commit()
        return redirect(url_for('inbox', email=email_address))
    return render_template('index.html')

@app.route('/inbox/<email>')
def inbox(email):
    messages = Email.query.filter_by(address=email).first()
    return render_template('inbox.html', email=email, messages=messages)

@app.route('/send_message/<email>', methods=['POST'])
def send_message(email):
    message_content = request.form.get('message')
    email_record = Email.query.filter_by(address=email).first()
    if email_record:
        email_record.messages += f"{message_content}\n"
        db.session.commit()
    return redirect(url_for('inbox', email=email))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
