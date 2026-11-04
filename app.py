import csv
import hmac
import io
import os
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, make_response
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True

database_url = os.environ.get("DATABASE_URL", "sqlite:///kutit_local.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

db = SQLAlchemy(app)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    name = db.Column(db.String(120), nullable=False)
    reg_no = db.Column(db.String(60), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(30), nullable=False)
    course = db.Column(db.String(120), nullable=True)
    year = db.Column(db.String(30), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default="Pending")


with app.app_context():
    db.create_all()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


def valid_csrf():
    supplied = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    return bool(supplied and expected and hmac.compare_digest(supplied, expected))


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

    try:
        member = Member(
            name=name, reg_no=reg_no, phone=phone,
            course=course or None, year=year or None
        )
        db.session.add(member)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("That registration number may already be registered. Please check it or contact the KUTIT team.", "error")
        return redirect(url_for("home") + "#register")

    flash("Registration received! The KUTIT team will share payment confirmation details.", "success")
    return redirect(url_for("home") + "#register")


@app.route("/admin", methods=["GET"])
def admin_home():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not valid_csrf():
            flash("Your session expired. Please try again.", "error")
            return redirect(url_for("admin_login"))

        configured_user = os.environ.get("ADMIN_USERNAME")
        configured_password = os.environ.get("ADMIN_PASSWORD")
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not configured_user or not configured_password:
            flash("Admin login is not configured yet. Set ADMIN_USERNAME and ADMIN_PASSWORD in your hosting environment.", "error")
        elif hmac.compare_digest(username, configured_user) and hmac.compare_digest(password, configured_password):
            session.clear()
            session["is_admin"] = True
            session["admin_username"] = configured_user
            flash("Welcome to the KUTIT admin dashboard.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect username or password.", "error")

    return render_template("admin/login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q = request.args.get("q", "").strip()
    query = Member.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Member.name.ilike(like),
            Member.reg_no.ilike(like),
            Member.phone.ilike(like),
            Member.course.ilike(like)
        ))
    members = query.order_by(Member.created_at.desc()).all()
    total = Member.query.count()
    paid = Member.query.filter_by(payment_status="Paid").count()
    pending = total - paid
    return render_template(
        "admin/dashboard.html", members=members, q=q,
        total=total, paid=paid, pending=pending
    )


@app.route("/admin/member/<int:member_id>/payment", methods=["POST"])
@admin_required
def update_payment(member_id):
    if not valid_csrf():
        flash("Your session expired. Please refresh and try again.", "error")
        return redirect(url_for("admin_dashboard"))
    member = db.get_or_404(Member, member_id)
    status = request.form.get("payment_status")
    if status not in ("Paid", "Pending"):
        flash("Invalid payment status.", "error")
    else:
        member.payment_status = status
        db.session.commit()
        flash(f"Payment status updated for {member.name}.", "success")
    return redirect(url_for("admin_dashboard", q=request.form.get("q", "")))


@app.route("/admin/export")
@admin_required
def export_members():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date registered", "Full name", "Registration number", "Phone", "Course", "Year", "Payment status"])
    for m in Member.query.order_by(Member.created_at.desc()).all():
        writer.writerow([
            m.created_at.isoformat(), m.name, m.reg_no, m.phone,
            m.course or "", m.year or "", m.payment_status
        ])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=kutit_members.csv"
    return response


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    if not valid_csrf():
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("admin_dashboard"))
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
