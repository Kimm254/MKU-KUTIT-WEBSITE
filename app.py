from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATA_DIR = "data"
REGISTRATIONS = os.path.join(DATA_DIR, "registrations.csv")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    reg_no = request.form.get("reg_no", "").strip()
    phone = request.form.get("phone", "").strip()
    course = request.form.get("course", "").strip()
    year = request.form.get("year", "").strip()

    if not all([name, reg_no, phone]):
        flash("Please fill in your name, registration number and phone number.", "error")
        return redirect(url_for("home") + "#register")

    os.makedirs(DATA_DIR, exist_ok=True)
    new_file = not os.path.exists(REGISTRATIONS)
    with open(REGISTRATIONS, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["Date", "Full name", "Registration number", "Phone", "Course", "Year"])
        writer.writerow([datetime.now().isoformat(timespec="minutes"), name, reg_no, phone, course, year])

    flash("Registration received! The KUTIT team will share payment confirmation details.", "success")
    return redirect(url_for("home") + "#register")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
