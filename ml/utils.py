import re
from PyPDF2 import PdfReader
import docx

# ----------------------------
# PDF EXTRACT
# ----------------------------
def extract_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text


# ----------------------------
# DOCX EXTRACT
# ----------------------------
def extract_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])


# ----------------------------
# CLEAN TEXT (IMPROVED)
# ----------------------------
def clean_text(text):
    text = text.lower()

    # Replace separators
    text = text.replace("-", " ")
    text = text.replace("_", " ")

    # Remove symbols
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text


# ----------------------------
# SKILL MASTER + SYNONYMS
# ----------------------------
SKILL_SYNONYMS = {
    "ml": "machine learning",
    "ai": "machine learning",
    "dl": "deep learning",
    "js": "javascript",
    "node": "node.js",
    "reactjs": "react"
}

SKILLS_MASTER = [
    "python","machine learning","deep learning","nlp","computer vision",
    "sql","pandas","numpy","scikit-learn","tensorflow","keras",
    "react","node.js","django","flask","mongodb","firebase",
    "azure","aws","docker","kubernetes",
    "data analysis","data visualization","tableau","power bi","excel",
    "iot","api","rest api","html","css","javascript"
]


# ----------------------------
# SKILL EXTRACTION (IMPROVED)
# ----------------------------
def extract_skills(text):
    text = clean_text(text)

    # Apply synonyms
    for k, v in SKILL_SYNONYMS.items():
        text = text.replace(k, v)

    found = set()

    for skill in SKILLS_MASTER:
        if skill in text:
            found.add(skill)

    return list(found)


# ----------------------------
# SECTION DETECTION (SMARTER)
# ----------------------------
def extract_sections(text):
    text = text.lower()

    return {
        "projects": any(w in text for w in [
            "project", "projects", "developed", "built"
        ]),

        "certifications": any(w in text for w in [
            "certification", "certificate", "certifications",
            "aws", "azure", "google cloud"
        ]),

        "experience": any(w in text for w in [
            "experience", "intern", "internship", "worked"
        ]),

        "education": (
            any(w in text for w in [
                "university", "college", "degree", "cgpa"
            ]) or
            ("btech" in text or "b tech" in text or "b.e" in text)
        )
    }