from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///documents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    documents = Document.query.filter_by(user_id=session['user_id'])\
                              .order_by(Document.expiry_date).all()

    today = datetime.today().date()

    def get_status(expiry):
        days = (expiry - today).days
        if days <= 14:
            return "red"
        elif days <= 20:
            return "yellow"
        else:
            return "green"

    def days_left(expiry):
        return (expiry - today).days

    return render_template(
        'index.html',
        documents=documents,
        get_status=get_status,
        days_left=days_left
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect('/')

        return "Invalid username or password"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        doc = Document(
            name=request.form['name'],
            expiry_date=datetime.strptime(request.form['expiry'], "%Y-%m-%d"),
            user_id=session['user_id']
        )
        db.session.add(doc)
        db.session.commit()
        return redirect('/')

    return render_template('add.html')


@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    doc = Document.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(doc)
    db.session.commit()
    return redirect('/')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    doc = Document.query.filter_by(id=id, user_id=session['user_id']).first_or_404()

    if request.method == 'POST':
        doc.name = request.form['name']
        doc.expiry_date = datetime.strptime(request.form['expiry'], "%Y-%m-%d")
        db.session.commit()
        return redirect('/')

    return render_template('edit.html', doc=doc)


if __name__ == '__main__':
    app.run()
