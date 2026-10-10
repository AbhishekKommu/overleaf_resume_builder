# Resume Builder (Overleaf-style)

A Flask web app where you type your resume on the left and see a live-rendered preview on the right, then download it as a PDF.

## Features
- Register / login (hashed passwords)
- Dashboard to create, edit, preview, delete multiple resumes
- Split-pane editor with live preview and autosave
- Classic LaTeX-style resume layout (Objective, Education, Skills, Project Experience, Projects, Declaration), identical in live preview and PDF
- "Use Sample" button on the dashboard to start from a ready-made resume
- PDF export (ReportLab)
- SQLite storage, REST API for saving

## Tech Stack
HTML, CSS, JavaScript · Python, Flask · SQLite · ReportLab

## Project Structure
```
overleaf_resume_builder/
├── app.py            # Flask app, routes, REST API
├── config.py         # Configuration
├── requirements.txt
├── database/         # SQLite database (auto-created)
├── services/         # auth, resume, pdf logic
├── templates/        # Jinja2 pages
└── static/           # css, js, images
```

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Set a real secret key for production: `export SECRET_KEY="something-long-and-random"`.

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/resume/<id>` | Fetch a resume |
| PUT | `/api/resume/<id>` | Save title + content (JSON) |
| POST | `/api/resume/<id>/pdf` | PDF from unsaved editor content |
| GET | `/resume/<id>/pdf` | PDF of the saved resume |

## Notes
- All resume routes are scoped to the logged-in user.
- The database file is git-ignored and created on first run.
