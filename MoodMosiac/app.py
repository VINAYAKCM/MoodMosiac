import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from passlib.hash import pbkdf2_sha256
import os

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
    # Create tables if they don't exist
    # Users table: id, username, email, password_hash
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    # Moods table: id, user_id, mood, reason, date (as TEXT or DATETIME)
    db.execute('''CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mood TEXT NOT NULL,
        reason TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    db.commit()


# -------------------
# Routes
# -------------------

@app.route('/')
def index():
    # If user is logged in, they may go to dashboard or mood input
    # Otherwise show the landing page
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

        # Insert user into DB
        try:
            db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
            db.commit()
        except sqlite3.IntegrityError:
            # Username or email already taken
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
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    user_id = session['user_id']

    if request.method == 'POST':
        mood = request.form['mood']
        reason = request.form.get('reason', '')
        
        existing_entry = db.execute(
            'SELECT * FROM moods WHERE user_id = ? AND date = ?',
            (user_id, current_date)
        ).fetchone()

        if existing_entry:
            # Update the existing entry
            db.execute(
                'UPDATE moods SET mood = ?, reason = ? WHERE user_id = ? AND date = ?',
                (mood, reason, user_id, current_date)
            )
        else:
            # Insert new entry
            db.execute(
                'INSERT INTO moods (user_id, mood, reason, date) VALUES (?, ?, ?, ?)',
                (user_id, mood, reason, current_date)
            )
        db.commit()

        positive_message = "Your mood has been recorded for today!"
        # Re-fetch to show updated info
        existing_entry = db.execute(
            'SELECT * FROM moods WHERE user_id = ? AND date = ?',
            (user_id, current_date)
        ).fetchone()

        return render_template('mood_input.html', existing_entry=existing_entry, positive_message=positive_message)

    # On GET request, check if there's an entry for today
    existing_entry = db.execute(
        'SELECT * FROM moods WHERE user_id = ? AND date = ?',
        (user_id, current_date)
    ).fetchone()

    return render_template('mood_input.html', existing_entry=existing_entry)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # TODO: Fetch last week's data, call AI for suggestions, generate heatmap data.
    # For now, just show the dashboard page.
    return render_template('dashboard.html')

@app.route('/api/calendar_data')
def calendar_data():
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401

    db = get_db()
    user_id = session['user_id']

    from datetime import datetime, timedelta
    now = datetime.now()
    # Fetch data for the last year
    start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    rows = db.execute('SELECT date, mood FROM moods WHERE user_id = ? AND date BETWEEN ? AND ?',
                      (user_id, start_date, end_date)).fetchall()

    mood_map = {"Sad": 0, "Stressed": 1, "Neutral": 2, "Excited": 3, "Happy": 4}

    data = {}
    for r in rows:
        d_str = r['date']  # "YYYY-MM-DD"
        mood_val = mood_map.get(r['mood'], 2)  # default Neutral if unknown
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        # Convert to timestamp at start of the day
        timestamp = int(dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        data[timestamp] = mood_val

    return data



if __name__ == "__main__":
    with app.app_context():
        init_db()  # Initialize the DB tables before the app starts serving
    app.run(debug=True)