import csv
import hmac
import io
import os
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, make_response, abort, send_file
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -------------------------------------------------------------------
# APP CONFIGURATION
# -------------------------------------------------------------------
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-secret-before-deploying"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB uploads
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True

database_url = os.environ.get("DATABASE_URL", "sqlite:///kutit_local.db")

# PostgreSQL URL compatibility for psycopg2-binary on Render.
# Local development defaults to SQLite and does not need a PostgreSQL driver.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
db = SQLAlchemy(app)


# -------------------------------------------------------------------
# DATABASE MODELS
# Existing Member table/columns are retained to protect registrations.
# -------------------------------------------------------------------
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    name = db.Column(db.String(120), nullable=False)
    reg_no = db.Column(db.String(60), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(30), nullable=False)
    course = db.Column(db.String(120), nullable=True)
    year = db.Column(db.String(30), nullable=True)
    payment_status = db.Column(
        db.String(20), nullable=False, default="Pending"
    )


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.String(30), nullable=True)
    event_time = db.Column(db.String(30), nullable=True)
    venue = db.Column(db.String(160), nullable=True)
    published = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    poster_name = db.Column(db.String(255), nullable=True)
    poster_mime = db.Column(db.String(80), nullable=True)
    poster_data = db.Column(db.LargeBinary, nullable=True)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caption = db.Column(db.String(160), nullable=False)
    image_name = db.Column(db.String(255), nullable=False)
    image_mime = db.Column(db.String(80), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class Executive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(160), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


# Create any new tables without deleting existing member records.
with app.app_context():
    db.create_all()


# -------------------------------------------------------------------
# ADMIN AUTHENTICATION AND CSRF PROTECTION
# -------------------------------------------------------------------
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
    return bool(
        supplied and expected and hmac.compare_digest(supplied, expected)
    )


def csrf_failed(endpoint="admin_dashboard"):
    flash("Your session expired. Please refresh the page and try again.", "error")
    return redirect(url_for(endpoint))


# -------------------------------------------------------------------
# IMAGE UPLOAD HELPER
# -------------------------------------------------------------------
def image_from_request(field="image"):
    uploaded = request.files.get(field)

    if not uploaded or not uploaded.filename:
        return None

    mime = (uploaded.mimetype or "").lower()
    allowed_types = {
        "image/jpeg", "image/png", "image/webp", "image/gif"
    }

    if mime not in allowed_types:
        raise ValueError("Upload a JPG, PNG, WEBP or GIF image.")

    data = uploaded.read()

    if not data:
        raise ValueError("The selected image is empty.")

    if len(data) > 5 * 1024 * 1024:
        raise ValueError("Image must be 5 MB or smaller.")

    filename = secure_filename(uploaded.filename)[:255] or "image"
    return filename, mime, data


# -------------------------------------------------------------------
# PUBLIC TEMPLATE DATA
# -------------------------------------------------------------------
@app.context_processor
def inject_public_content():
    return {
        "public_announcements": Announcement.query.filter_by(
            published=True
        ).order_by(Announcement.created_at.desc()).limit(4).all(),

        "public_activities": Activity.query.filter_by(
            published=True
        ).order_by(Activity.event_date.asc(), Activity.id.desc()).limit(6).all(),

        "public_gallery": GalleryItem.query.order_by(
            GalleryItem.created_at.desc()
        ).limit(6).all(),

        "public_executives": Executive.query.order_by(
            Executive.sort_order.asc(), Executive.name.asc()
        ).all()
    }


# -------------------------------------------------------------------
# PUBLIC WEBSITE
# -------------------------------------------------------------------
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
        flash(
            "Please fill in your name, registration number and phone number.",
            "error"
        )
        return redirect(url_for("home") + "#register")

    try:
        member = Member(
            name=name,
            reg_no=reg_no,
            phone=phone,
            course=course or None,
            year=year or None
        )
        db.session.add(member)
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash(
            "That registration number may already be registered. "
            "Please check it or contact the KUTIT team.",
            "error"
        )
        return redirect(url_for("home") + "#register")

    # No payment step is shown after registration.
    flash(
        f"Congratulations, {name}! Your KUTIT membership registration "
        "has been received. Welcome to the KUTIT family!",
        "success"
    )
    return redirect(url_for("home") + "#register")


# -------------------------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------------------------
@app.route("/admin")
def admin_home():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not valid_csrf():
            return csrf_failed("admin_login")

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        configured_user = os.environ.get("ADMIN_USERNAME")
        configured_password = os.environ.get("ADMIN_PASSWORD")

        if not configured_user or not configured_password:
            flash(
                "Admin login is not configured. Set ADMIN_USERNAME and "
                "ADMIN_PASSWORD in Render Environment.",
                "error"
            )

        elif (
            hmac.compare_digest(username, configured_user)
            and hmac.compare_digest(password, configured_password)
        ):
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
    return render_template(
        "admin/dashboard.html",
        total=Member.query.count(),
        paid=Member.query.filter_by(payment_status="Paid").count(),
        pending=Member.query.filter_by(payment_status="Pending").count(),
        activities=Activity.query.count(),
        announcements=Announcement.query.count(),
        gallery_count=GalleryItem.query.count(),
        executives=Executive.query.count()
    )


# -------------------------------------------------------------------
# MEMBERS AND PAYMENT TRACKING
# -------------------------------------------------------------------
@app.route("/admin/members")
@admin_required
def admin_members():
    search_term = request.args.get("q", "").strip()
    query = Member.query

    if search_term:
        like = f"%{search_term}%"
        query = query.filter(
            or_(
                Member.name.ilike(like),
                Member.reg_no.ilike(like),
                Member.phone.ilike(like),
                Member.course.ilike(like)
            )
        )

    members = query.order_by(Member.created_at.desc()).all()
    return render_template(
        "admin/members.html",
        members=members,
        q=search_term
    )


@app.route("/admin/member/<int:member_id>/payment", methods=["POST"])
@admin_required
def update_payment(member_id):
    if not valid_csrf():
        return csrf_failed("admin_members")

    member = db.get_or_404(Member, member_id)
    status = request.form.get("payment_status")

    if status not in ("Paid", "Pending"):
        flash("Invalid payment status.", "error")
    else:
        member.payment_status = status
        db.session.commit()
        flash(f"Payment status updated for {member.name}.", "success")

    return redirect(
        url_for("admin_members", q=request.form.get("q", ""))
    )


@app.route("/admin/export")
@admin_required
def export_members():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date registered", "Full name", "Registration number",
        "Phone", "Course", "Year", "Payment status"
    ])

    for member in Member.query.order_by(Member.created_at.desc()).all():
        writer.writerow([
            member.created_at.isoformat(),
            member.name,
            member.reg_no,
            member.phone,
            member.course or "",
            member.year or "",
            member.payment_status
        ])

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=kutit_members.csv"
    )
    return response


# -------------------------------------------------------------------
# ACTIVITIES AND EVENTS
# -------------------------------------------------------------------
@app.route("/admin/activities", methods=["GET", "POST"])
@admin_required
def admin_activities():
    if request.method == "POST":
        if not valid_csrf():
            return csrf_failed("admin_activities")

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not description:
            flash("Activity title and description are required.", "error")
        else:
            try:
                image = image_from_request("poster")

                activity = Activity(
                    title=title,
                    description=description,
                    event_date=request.form.get("event_date", "").strip() or None,
                    event_time=request.form.get("event_time", "").strip() or None,
                    venue=request.form.get("venue", "").strip() or None,
                    published=request.form.get("published") == "on"
                )

                if image:
                    (
                        activity.poster_name,
                        activity.poster_mime,
                        activity.poster_data
                    ) = image

                db.session.add(activity)
                db.session.commit()
                flash("Activity saved successfully.", "success")

            except ValueError as error:
                flash(str(error), "error")

    items = Activity.query.order_by(Activity.id.desc()).all()
    return render_template("admin/activities.html", items=items)


@app.route("/admin/activity/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_activity(item_id):
    if not valid_csrf():
        return csrf_failed("admin_activities")

    db.session.delete(db.get_or_404(Activity, item_id))
    db.session.commit()
    flash("Activity deleted.", "success")
    return redirect(url_for("admin_activities"))


# -------------------------------------------------------------------
# ANNOUNCEMENTS
# -------------------------------------------------------------------
@app.route("/admin/announcements", methods=["GET", "POST"])
@admin_required
def admin_announcements():
    if request.method == "POST":
        if not valid_csrf():
            return csrf_failed("admin_announcements")

        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()

        if title and body:
            announcement = Announcement(
                title=title,
                body=body,
                published=request.form.get("published") == "on"
            )
            db.session.add(announcement)
            db.session.commit()
            flash("Announcement saved successfully.", "success")
        else:
            flash("Title and announcement text are required.", "error")

    items = Announcement.query.order_by(
        Announcement.id.desc()
    ).all()

    return render_template(
        "admin/announcements.html",
        items=items
    )


@app.route("/admin/announcement/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_announcement(item_id):
    if not valid_csrf():
        return csrf_failed("admin_announcements")

    db.session.delete(db.get_or_404(Announcement, item_id))
    db.session.commit()
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin_announcements"))


# -------------------------------------------------------------------
# EVENT POSTERS AND GALLERY
# -------------------------------------------------------------------
@app.route("/admin/gallery", methods=["GET", "POST"])
@admin_required
def admin_gallery():
    if request.method == "POST":
        if not valid_csrf():
            return csrf_failed("admin_gallery")

        caption = request.form.get("caption", "").strip()

        try:
            image = image_from_request("image")

            if not caption or not image:
                flash("Add a caption and choose an image.", "error")
            else:
                name, mime, data = image
                gallery_item = GalleryItem(
                    caption=caption,
                    image_name=name,
                    image_mime=mime,
                    image_data=data
                )
                db.session.add(gallery_item)
                db.session.commit()
                flash("Gallery image uploaded successfully.", "success")

        except ValueError as error:
            flash(str(error), "error")

    items = GalleryItem.query.order_by(
        GalleryItem.id.desc()
    ).all()

    return render_template(
        "admin/gallery.html",
        items=items
    )


@app.route("/admin/gallery/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_gallery(item_id):
    if not valid_csrf():
        return csrf_failed("admin_gallery")

    db.session.delete(db.get_or_404(GalleryItem, item_id))
    db.session.commit()
    flash("Gallery image deleted.", "success")
    return redirect(url_for("admin_gallery"))


# -------------------------------------------------------------------
# EXECUTIVE COMMITTEE
# -------------------------------------------------------------------
@app.route("/admin/executives", methods=["GET", "POST"])
@admin_required
def admin_executives():
    if request.method == "POST":
        if not valid_csrf():
            return csrf_failed("admin_executives")

        name = request.form.get("name", "").strip()
        position = request.form.get("position", "").strip()

        if name and position:
            try:
                sort_order = int(request.form.get("sort_order") or 0)
            except ValueError:
                sort_order = 0

            executive = Executive(
                name=name,
                position=position,
                phone=request.form.get("phone", "").strip() or None,
                email=request.form.get("email", "").strip() or None,
                sort_order=sort_order
            )

            db.session.add(executive)
            db.session.commit()
            flash("Executive member added successfully.", "success")
        else:
            flash("Name and position are required.", "error")

    items = Executive.query.order_by(
        Executive.sort_order.asc(),
        Executive.name.asc()
    ).all()

    return render_template(
        "admin/executives.html",
        items=items
    )


@app.route("/admin/executive/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_executive(item_id):
    if not valid_csrf():
        return csrf_failed("admin_executives")

    db.session.delete(db.get_or_404(Executive, item_id))
    db.session.commit()
    flash("Executive record deleted.", "success")
    return redirect(url_for("admin_executives"))


# -------------------------------------------------------------------
# PUBLIC IMAGE ROUTES
# -------------------------------------------------------------------
@app.route("/media/activity/<int:item_id>")
def activity_poster(item_id):
    activity = db.get_or_404(Activity, item_id)

    if not activity.poster_data:
        abort(404)

    return send_file(
        io.BytesIO(activity.poster_data),
        mimetype=activity.poster_mime,
        download_name=activity.poster_name,
        max_age=3600
    )


@app.route("/media/gallery/<int:item_id>")
def gallery_image(item_id):
    item = db.get_or_404(GalleryItem, item_id)

    return send_file(
        io.BytesIO(item.image_data),
        mimetype=item.image_mime,
        download_name=item.image_name,
        max_age=3600
    )


# -------------------------------------------------------------------
# LOGOUT AND ERROR HANDLING
# -------------------------------------------------------------------
@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    if not valid_csrf():
        return csrf_failed("admin_dashboard")

    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.errorhandler(413)
def too_large(_error):
    flash(
        "The uploaded file is too large. Maximum size is 5 MB.",
        "error"
    )
    return redirect(request.referrer or url_for("home"))


if __name__ == "__main__":
    # Local development only. Render should run the app with Gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
