import os
import re
import sqlite3

from flask import (Flask, g, render_template, request, redirect, url_for,
                   session, flash, jsonify, send_file, abort)

from config import Config
from services import auth_service, resume_service, pdf_service
from services.auth_service import login_required

import io

app = Flask(__name__)
app.config.from_object(Config)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ---------- pages ----------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        ok, msg = auth_service.register_user(
            get_db(),
            request.form.get("username", ""),
            request.form.get("email", ""),
            request.form.get("password", ""),
        )
        flash(msg, "success" if ok else "error")
        if ok:
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = auth_service.authenticate(
            get_db(), request.form.get("identifier", ""), request.form.get("password", "")
        )
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    resumes = resume_service.list_resumes(get_db(), session["user_id"])
    return render_template("dashboard.html", resumes=resumes)


@app.route("/resume/new", methods=["POST"])
@login_required
def new_resume():
    db = get_db()
    user = db.execute("SELECT username, email FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if request.form.get("sample"):
        content = resume_service.sample_content()
    else:
        content = resume_service.default_content(user["username"], user["email"])
    rid = resume_service.create_resume(db, session["user_id"], request.form.get("title", "Untitled Resume"), content)
    return redirect(url_for("editor", resume_id=rid))


@app.route("/resume/<int:resume_id>/edit")
@login_required
def editor(resume_id):
    resume = resume_service.get_resume(get_db(), resume_id, session["user_id"])
    if not resume:
        abort(404)
    return render_template("resume_editor.html", resume=resume)


@app.route("/resume/<int:resume_id>/preview")
@login_required
def preview(resume_id):
    resume = resume_service.get_resume(get_db(), resume_id, session["user_id"])
    if not resume:
        abort(404)
    return render_template("preview.html", resume=resume)


@app.route("/resume/<int:resume_id>/delete", methods=["POST"])
@login_required
def delete_resume(resume_id):
    resume_service.delete_resume(get_db(), resume_id, session["user_id"])
    flash("Resume deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/resume/<int:resume_id>/pdf")
@login_required
def download_pdf(resume_id):
    resume = resume_service.get_resume(get_db(), resume_id, session["user_id"])
    if not resume:
        abort(404)
    pdf_bytes = pdf_service.build_pdf(resume["content"])
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", resume["title"]).strip("_") or "resume"
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name=f"{safe}.pdf")


# ---------- REST API ----------
@app.route("/api/resume/<int:resume_id>", methods=["GET"])
@login_required
def api_get(resume_id):
    resume = resume_service.get_resume(get_db(), resume_id, session["user_id"])
    if not resume:
        return jsonify(error="Not found"), 404
    return jsonify(resume)


@app.route("/api/resume/<int:resume_id>", methods=["PUT"])
@login_required
def api_save(resume_id):
    payload = request.get_json(silent=True) or {}
    content = resume_service.sanitize(payload.get("content", {}))
    title = str(payload.get("title", "")).strip()[:100]
    if not resume_service.update_resume(get_db(), resume_id, session["user_id"], title, content):
        return jsonify(error="Not found"), 404
    return jsonify(ok=True)


@app.route("/api/resume/<int:resume_id>/pdf", methods=["POST"])
@login_required
def api_pdf_from_draft(resume_id):
    """Render PDF from unsaved editor content."""
    if not resume_service.get_resume(get_db(), resume_id, session["user_id"]):
        return jsonify(error="Not found"), 404
    payload = request.get_json(silent=True) or {}
    content = resume_service.sanitize(payload.get("content", {}))
    return send_file(io.BytesIO(pdf_service.build_pdf(content)), mimetype="application/pdf",
                     as_attachment=True, download_name="resume.pdf")


init_db()

if __name__ == "__main__":
    app.run(debug=True)
