from flask import Flask, request, jsonify, render_template, send_file
import os
import sqlite3
import bcrypt
import qrcode
from PIL import Image

app = Flask(__name__)

# Create directories for storage
os.makedirs("uploads", exist_ok=True)
os.makedirs("qrcodes", exist_ok=True)

# Database Setup
DB_FILE = "database.db"

def create_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS id_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    image_path TEXT,
                    qr_code TEXT,
                    password TEXT)''')

    conn.commit()
    conn.close()

create_db()

# Route: Admin Uploads ID Card
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    name = request.form['name']
    password = request.form['password'].encode('utf-8')
    image = request.files['image']

    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    image_path = os.path.join("uploads", name + ".png")
    image.save(image_path)

    # Generate QR Code
    qr_code_path = os.path.join("qrcodes", name + "_qr.png")
    qr = qrcode.make(f"http://localhost:5000/view/{name}")
    qr.save(qr_code_path)

    # Store in database
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO id_cards (name, image_path, qr_code, password) VALUES (?, ?, ?, ?)",
              (name, image_path, qr_code_path, hashed_password))
    conn.commit()
    conn.close()

    return jsonify({"message": "ID card uploaded successfully", "qr_code": qr_code_path})

# Route: View ID Card (After Scanning QR)
@app.route('/view/<name>', methods=['GET'])
def view_page(name):
    return render_template("password_prompt.html", name=name)

# Route: Validate Password and Show Image
@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    name = data.get('name')
    password = data.get('password').encode('utf-8')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT image_path, password FROM id_cards WHERE name=?", (name,))
    result = c.fetchone()
    conn.close()

    if result and bcrypt.checkpw(password, result[1].encode('utf-8')):
        return send_file(result[0], mimetype='image/png')
    else:
        return jsonify({"error": "Invalid password"}), 401

if __name__ == '__main__':
    app.run(debug=True)