import os
import json
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, redirect, url_for, flash,
    request, send_file, abort
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from config import Config
from extensions import db, login_manager
from models import User, Scan
from utils.predict import predict_tumor
from utils.report_generator import build_report_pdf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        os.makedirs(os.path.join(app.instance_path), exist_ok=True)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        db.create_all()

    register_routes(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def register_routes(app):

    # ---------------------------------------------------------------
    # Home
    # ---------------------------------------------------------------
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    # ---------------------------------------------------------------
    # Auth: Register
    # ---------------------------------------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not all([full_name, username, email, password, confirm_password]):
                flash("Please fill in all fields.", "error")
                return redirect(url_for("register"))

            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return redirect(url_for("register"))

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "error")
                return redirect(url_for("register"))

            if User.query.filter_by(username=username).first():
                flash("That username is already taken.", "error")
                return redirect(url_for("register"))

            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return redirect(url_for("register"))

            user = User(full_name=full_name, username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    # ---------------------------------------------------------------
    # Auth: Login
    # ---------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            identifier = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            remember = bool(request.form.get("remember"))

            user = User.query.filter(
                (User.username == identifier) | (User.email == identifier.lower())
            ).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash(f"Welcome back, {user.full_name.split(' ')[0]}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("dashboard"))

            flash("Invalid username/email or password.", "error")
            return redirect(url_for("login"))

        return render_template("login.html")

    # ---------------------------------------------------------------
    # Auth: Logout
    # ---------------------------------------------------------------
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # ---------------------------------------------------------------
    # Dashboard: upload + predict
    # ---------------------------------------------------------------
    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        if request.method == "POST":
            patient_name = request.form.get("patient_name", "").strip()
            file = request.files.get("mri_image")

            if not file or file.filename == "":
                flash("Please choose an MRI image to upload.", "error")
                return redirect(url_for("dashboard"))

            if not allowed_file(file.filename):
                flash("Only PNG, JPG, and JPEG image files are allowed.", "error")
                return redirect(url_for("dashboard"))

            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            safe_name = secure_filename(unique_name)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            file.save(save_path)

            try:
                predicted_label, confidence, probabilities = predict_tumor(
                    save_path,
                    app.config["CLASS_LABELS"],
                    app.config["IMAGE_SIZE"],
                )
            except FileNotFoundError as e:
                flash(str(e), "error")
                return redirect(url_for("dashboard"))
            except Exception as e:
                flash(f"Could not analyze image: {e}", "error")
                return redirect(url_for("dashboard"))

            scan = Scan(
                user_id=current_user.id,
                patient_name=patient_name or None,
                image_filename=safe_name,
                predicted_class=predicted_label,
                confidence=confidence,
                probabilities_json=json.dumps(probabilities),
            )
            db.session.add(scan)
            db.session.commit()

            return redirect(url_for("result", scan_id=scan.id))

        recent_scans = (
            Scan.query.filter_by(user_id=current_user.id)
            .order_by(Scan.created_at.desc())
            .limit(5)
            .all()
        )
        total_scans = Scan.query.filter_by(user_id=current_user.id).count()
        tumor_found = Scan.query.filter(
            Scan.user_id == current_user.id, Scan.predicted_class != "No Tumor"
        ).count()

        return render_template(
            "dashboard.html",
            recent_scans=recent_scans,
            total_scans=total_scans,
            tumor_found=tumor_found,
        )

    # ---------------------------------------------------------------
    # Result page for a single scan
    # ---------------------------------------------------------------
    @app.route("/result/<int:scan_id>")
    @login_required
    def result(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            abort(403)
        probabilities = json.loads(scan.probabilities_json)
        return render_template(
            "result.html",
            scan=scan,
            probabilities=probabilities,
            class_info=app.config["CLASS_INFO"],
        )

    # ---------------------------------------------------------------
    # History of all past scans
    # ---------------------------------------------------------------
    @app.route("/history")
    @login_required
    def history():
        scans = (
            Scan.query.filter_by(user_id=current_user.id)
            .order_by(Scan.created_at.desc())
            .all()
        )
        return render_template("history.html", scans=scans)

    # ---------------------------------------------------------------
    # Download PDF report for a scan
    # ---------------------------------------------------------------
    @app.route("/report/<int:scan_id>")
    @login_required
    def download_report(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            abort(403)

        image_path = os.path.join(app.config["UPLOAD_FOLDER"], scan.image_filename)
        pdf_buffer = build_report_pdf(scan, current_user, image_path)

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"NeuroScan_Report_{scan.id}.pdf",
        )

    # ---------------------------------------------------------------
    # Tumor information page
    # ---------------------------------------------------------------
    @app.route("/info")
    @login_required
    def info():
        return render_template("info.html", class_info=app.config["CLASS_INFO"])

    # ---------------------------------------------------------------
    # Error handlers
    # ---------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Access forbidden."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        flash("File is too large. Maximum upload size is 8 MB.", "error")
        return redirect(url_for("dashboard"))


app = create_app()

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )