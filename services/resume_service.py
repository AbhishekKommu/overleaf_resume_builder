import json

EMPTY_RESUME = {
    "name": "",
    "phone": "",
    "email": "",
    "linkedin": "",
    "github": "",
    "objective": "",
    "education": [],          # {degree, institution, date, detail, location}
    "skills": [],             # {label, value}
    "experience": "",         # bullet points, one per line
    "projects": [],           # {name, description}
    "declaration": "",
}

SAMPLE_RESUME = {
    "name": "KOMMU ABHISHEK",
    "phone": "+91 7670843988",
    "email": "kommuabhishek84@gmail.com",
    "linkedin": "",
    "github": "",
    "objective": (
        "Ambitious Artificial Intelligence and Machine Learning student with strong "
        "problem-solving abilities, hands-on development experience, and a passion for "
        "learning new technologies. Seeking opportunities to contribute, collaborate, "
        "and grow within innovative tech teams."
    ),
    "education": [
        {"degree": "B.Tech in Artificial Intelligence and Machine Learning",
         "institution": "NRI Institute of Technology, Agiripally",
         "date": "Expected 2027", "detail": "CGPA: 8.59/10", "location": "AP, India"},
        {"degree": "Intermediate (MPC), DKNP Junior College",
         "institution": "", "date": "2021 \u2013 2023",
         "detail": "Percentage: 60%", "location": "AP, India"},
    ],
       "skills": [
        {"label": "Programming Languages", "value": "Basics of Python"},
        {"label": "Web Technologies", "value": "HTML, CSS, JavaScript"},
        {"label": "Databases", "value": "MySQL"},
        {"label": "Developer Tools", "value": "GitHub, Google Colab, VS Code"},
        {"label": "Academic Coursework", "value": "DBMS, Data Structures, Web Development, Computer Networks"},
        {"label": "Certifications", "value": (
            "AI in Project Management (LinkedIn Learning)\n"
            "Python Code Challenges: Working With Data (LinkedIn Learning)\n"
            "Artificial Intelligence Fundamentals (IBM)\n"
            "AI Ethics (IBM)\n"
            "Natural Language Processing and Computer Vision (IBM)")},
    ],
    "experience": (
        "Developed responsive web interfaces using HTML, CSS, and JavaScript with interactive features.\n"
        "Built basic backend functionality using Python for application logic and data processing.\n"
        "Integrated frontend and backend components in academic and personal projects.\n"
        "Used GitHub and VS Code for development, debugging, and version control."
    ),
    "projects": [
        {"name": "Movie Genre Classification",
         "description": "Built a machine learning model to classify movie genres using Python. Used Pandas for data handling and Scikit-learn for model development and evaluation. Implemented and tested the workflow in Google Colab."},
        {"name": "Spam Detection",
         "description": "Built a machine learning model to detect spam messages using Python. Used Pandas and NumPy for data preprocessing and Scikit-learn for feature extraction, model development, and evaluation."},
        {"name": "Credit Card Fraud Detection",
         "description": "Built a machine learning model to detect fraudulent credit card transactions using Python. Used Pandas for data preprocessing and Scikit-learn for model development, classification, and evaluation."},
        {"name": "Student Management System",
         "description": "Developed a web-based student management system using HTML, CSS, JavaScript, and Python."},
    ],
    "declaration": (
        "I hereby declare that the information provided in this resume is true and "
        "correct to the best of my knowledge and belief."
    ),
}


def default_content(name="", email=""):
    data = json.loads(json.dumps(EMPTY_RESUME))
    data["name"], data["email"] = name.upper(), email
    return data


def sample_content():
    return json.loads(json.dumps(SAMPLE_RESUME))


def list_resumes(db, user_id):
    return db.execute(
        "SELECT id, title, updated_at FROM resumes WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    ).fetchall()


def get_resume(db, resume_id, user_id):
    row = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "content": json.loads(row["content"]),
        "updated_at": row["updated_at"],
    }


def create_resume(db, user_id, title, content):
    cur = db.execute(
        "INSERT INTO resumes (user_id, title, content) VALUES (?, ?, ?)",
        (user_id, title or "Untitled Resume", json.dumps(content)),
    )
    db.commit()
    return cur.lastrowid


def update_resume(db, resume_id, user_id, title, content):
    cur = db.execute(
        "UPDATE resumes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND user_id = ?",
        (title or "Untitled Resume", json.dumps(content), resume_id, user_id),
    )
    db.commit()
    return cur.rowcount > 0


def delete_resume(db, resume_id, user_id):
    cur = db.execute(
        "DELETE FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)
    )
    db.commit()
    return cur.rowcount > 0


def sanitize(content):
    """Keep only known keys with expected types."""
    clean = json.loads(json.dumps(EMPTY_RESUME))
    for key, default in EMPTY_RESUME.items():
        value = content.get(key, default)
        if isinstance(default, list):
            items = value if isinstance(value, list) else []
            clean[key] = [
                {str(k): str(v) if v is not None else "" for k, v in item.items()}
                for item in items if isinstance(item, dict)
            ]
        else:
            clean[key] = str(value) if value is not None else ""
    return clean
