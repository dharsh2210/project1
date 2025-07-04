from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'lost_and_found.db'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                location TEXT,
                date TEXT,
                contact TEXT,
                image TEXT,
                status TEXT
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('items'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        date = request.form['date']
        contact = request.form['contact']
        status = request.form['status']
        image_file = request.files['image']
        image_filename = None
        if image_file and image_file.filename != '':
            image_filename = image_file.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO items (name, description, location, date, contact, image, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, location, date, contact, image_filename, status))
            conn.commit()
        return redirect(url_for('items'))
    return render_template('report.html')

@app.route('/items')
def items():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM items WHERE status = 'Lost'")
        lost_items = c.fetchall()
        c.execute("SELECT * FROM items WHERE status = 'Found'")
        found_items = c.fetchall()
    return render_template('items.html', lost_items=lost_items, found_items=found_items)

@app.route('/mark_found/<int:item_id>', methods=['POST'])
def mark_found(item_id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("UPDATE items SET status = 'Found' WHERE id = ?", (item_id,))
        conn.commit()
    return redirect(url_for('items'))

@app.route('/claim/<int:item_id>', methods=['POST'])
def claim(item_id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
    return redirect(url_for('items'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
