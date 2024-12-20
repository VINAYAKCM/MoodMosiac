import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure key in production
DATABASE = 'mood_tracker.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mood TEXT NOT NULL,
        reason TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    db.commit()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('mood_input'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = pbkdf2_sha256.hash(password)

        try:
            db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
            db.commit()
        except sqlite3.IntegrityError:
            return "Username or Email already exists. Please go back and choose another."

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = request.form['password']

        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and pbkdf2_sha256.verify(password, user['password_hash']):
            session['user_id'] = user['id']
            return redirect(url_for('mood_input'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/mood_input', methods=['GET', 'POST'])
def mood_input():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        mood = request.form['mood']
        reason = request.form.get('reason', '')
        date = request.form.get('date')

        existing_entry = db.execute(
            'SELECT * FROM moods WHERE user_id = ? AND date = ?',
            (user_id, date)
        ).fetchone()

        if existing_entry:
            db.execute(
                'UPDATE moods SET mood = ?, reason = ? WHERE user_id = ? AND date = ?',
                (mood, reason, user_id, date)
            )
        else:
            db.execute(
                'INSERT INTO moods (user_id, mood, reason, date) VALUES (?, ?, ?, ?)',
                (user_id, mood, reason, date)
            )
        db.commit()

    return render_template('mood_input.html')

@app.route('/api/moods', methods=['GET'])
def api_moods():
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401

    db = get_db()
    user_id = session['user_id']
    rows = db.execute('SELECT date, mood FROM moods WHERE user_id = ?', (user_id,)).fetchall()

    data = {row['date']: row['mood'] for row in rows}
    return jsonify(data)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')  # Create a `dashboard.html` template or adjust this as needed

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)