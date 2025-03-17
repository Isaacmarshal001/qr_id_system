from flask import Flask, render_template, request, redirect, url_for, session, send_file
import qrcode
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "uploads"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class IDCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    qr_code_path = db.Column(db.String(200), nullable=False)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        file = request.files["file"]

        if file:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(image_path)
            password_hash = generate_password_hash(password)

            qr = qrcode.make(f"/view/{file.filename}")
            qr_code_path = f"static/qr_codes/{file.filename}.png"
            qr.save(qr_code_path)

            new_id = IDCard(name=name, image_path=image_path, password_hash=password_hash, qr_code_path=qr_code_path)
            db.session.add(new_id)
            db.session.commit()

    id_cards = IDCard.query.all()
    return render_template("dashboard.html", id_cards=id_cards)

@app.route("/view/<filename>", methods=["GET", "POST"])
def view_id(filename):
    id_card = IDCard.query.filter_by(image_path=f"uploads/{filename}").first()
    if request.method == "POST":
        password = request.form["password"]
        if check_password_hash(id_card.password_hash, password):
            return send_file(id_card.image_path)
    return render_template("enter_password.html", filename=filename)

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
