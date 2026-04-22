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

    # Keep a few symbols used in technical skills (c++, c#, node.js).
    text = re.sub(r"[^a-zA-Z0-9+#.\s]", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ----------------------------
# SKILL MASTER + SYNONYMS
# ----------------------------
SKILL_SYNONYMS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "js": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node js": "node.js",
    "powerbi": "power bi",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "nlp": "natural language processing",
    "cv": "computer vision",
}

SKILLS_MASTER = [
    "python", "machine learning", "artificial intelligence", "deep learning",
    "natural language processing", "computer vision", "sql", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "keras", "statistics",
    "data analysis", "data visualization", "tableau", "power bi", "excel",
    "react", "node.js", "django", "flask", "mongodb", "firebase",
    "azure", "aws", "docker", "kubernetes", "hadoop", "spark",
    "api", "rest api", "html", "css", "javascript", "c++", "c#", "java",
    "feature engineering", "model deployment", "mlops", "etl",
]


# ----------------------------
# SKILL EXTRACTION (IMPROVED)
# ----------------------------
def extract_skills(text):
    cleaned = clean_text(text)
    found = set()

    # Match aliases with word boundaries to avoid false replacements
    # (e.g., "ai" in "email").
    for alias, canonical in SKILL_SYNONYMS.items():
        alias_pattern = r"\b" + re.escape(alias).replace(r"\ ", r"\s+") + r"\b"
        if re.search(alias_pattern, cleaned):
            found.add(canonical)

    for skill in SKILLS_MASTER:
        variants = {
            skill,
            skill.replace(".", " "),
            skill.replace(".", ""),
            skill.replace("-", " "),
        }
        matched = False
        for variant in variants:
            pattern = r"\b" + re.escape(variant).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, cleaned):
                matched = True
                break
        if matched:
            found.add(skill)

    return sorted(found)


# ----------------------------
# SECTION DETECTION (SMARTER)
# ----------------------------
def extract_sections(text):
    text = clean_text(text)

    return {
        "projects": any(w in text for w in [
            "project", "projects", "capstone", "portfolio", "github",
            "developed", "implemented", "built"
        ]),

        "certifications": any(w in text for w in [
            "certification", "certificate", "certifications",
            "aws", "azure", "google cloud", "coursera", "udemy"
        ]),

        "experience": any(w in text for w in [
            "experience", "work experience", "intern", "internship",
            "worked", "employment"
        ]),

        "education": (
            any(w in text for w in [
                "university", "college", "degree", "cgpa", "gpa", "bachelor",
                "master", "b.tech", "btech", "be", "mtech"
            ]) or
            ("btech" in text or "b tech" in text or "b.e" in text)
        )
    }