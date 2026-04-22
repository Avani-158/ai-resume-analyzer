import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from utils import extract_pdf, extract_skills, extract_sections, clean_text

# ----------------------------
# LOAD MODEL
# ----------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

# ----------------------------
# LOAD DATA
# ----------------------------
jobs = pd.read_csv("ml/data/jobs.csv")
skills_df = pd.read_csv("ml/data/skills.csv")
courses_df = pd.read_csv("ml/data/courses.csv")

# ----------------------------
# BASIC PREPROCESSING (DATA FIX)
# ----------------------------
def normalize_role(r):
    r = str(r).lower().strip()
    r = r.replace("node js", "node.js")
    r = r.replace("fullstack", "full stack")
    return r.title()

jobs["role"] = jobs["role"].apply(normalize_role)
jobs["description"] = jobs["description"].astype(str).str.lower()

skills_df["role"] = skills_df["role"].str.lower().str.strip()
courses_df["skill"] = courses_df["skill"].str.lower().str.strip()

# Remove duplicates (important for imbalance)
jobs.drop_duplicates(subset=["role", "description"], inplace=True)

# ----------------------------
# PRECOMPUTE EMBEDDINGS (FAST)
# ----------------------------
job_embeddings = model.encode(jobs["description"].tolist(), convert_to_tensor=True)

# ----------------------------
# GET REQUIRED SKILLS
# ----------------------------
def get_required_skills(role):
    role = role.lower().strip()

    # beginner-friendly version
    if "ml engineer" in role:
        return [
            "python",
            "machine learning",
            "numpy",
            "data analysis",
            "scikit-learn"
        ]

    row = skills_df[skills_df["role"] == role]

    if not row.empty:
        return [s.strip().lower() for s in row.iloc[0]["skills"].split(";")]

    return []

# ----------------------------
# HYBRID ROLE MATCHING (ACCURATE)
# ----------------------------
def match_roles(resume, user_skills, target_role):
    resume = clean_text(resume)
    resume_emb = model.encode(resume, convert_to_tensor=True)

    sim_scores = util.cos_sim(resume_emb, job_embeddings)[0]

    results = []
    for i, sim in enumerate(sim_scores):
        role = jobs.iloc[i]["role"]

        # semantic score
        semantic = float(sim)

        # skill overlap
        req_skills = get_required_skills(role)
        overlap = len(set(user_skills) & set(req_skills)) / (len(req_skills) + 1e-5)

        # target boost
        target_boost = 0.0
        if target_role.lower() in role.lower():
            target_boost = 0.15

        # ai/ml boost
        if any(k in role.lower() for k in ["ai", "ml", "data"]):
            target_boost += 0.05

        # Stronger target alignment
        intent_boost = 0
        if target_role.lower() in role.lower():
            intent_boost = 0.25

        final_score = (0.5 * semantic) + (0.3 * overlap) + target_boost + intent_boost

        results.append((role, final_score))

    # remove duplicate roles (keep best)
    role_scores = {}
    for role, score in results:
        role_scores[role] = max(role_scores.get(role, 0), score)

    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)

    return [(r, round(s * 100, 2)) for r, s in sorted_roles]

# ----------------------------
# MISSING SKILLS
# ----------------------------
def get_missing_skills(user_skills, required_skills):
    return list(set(required_skills) - set(user_skills))

# ----------------------------
# COURSES
# ----------------------------
def get_courses(missing_skills):
    rec = {}
    for skill in missing_skills:
        matched = courses_df[courses_df["skill"].str.contains(skill, case=False, na=False)]
        if not matched.empty:
            rec[skill] = matched["course"].tolist()
    return rec

# ----------------------------
# ATS SCORE
# ----------------------------
def ats_score(match_score, user_skills, required_skills, missing, sections):
    score = 0

    score += match_score * 0.5

    relevant = len(set(user_skills) & set(required_skills))
    score += relevant * 4

    score -= len(missing) * 2

    if sections["projects"]:
        score += 10
    if sections["education"]:
        score += 10

    return round(max(0, min(100, score)), 2)

# ----------------------------
# GPT CHATBOT (REAL)
# ----------------------------


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":

    resume = extract_pdf("ml/data/resume.pdf")
    target_role = input("🎯 Enter your target role: ").strip().title()

    print("\n====== AI RESUME ANALYSIS ======\n")

    skills = extract_skills(resume)
    sections = extract_sections(resume)

    print("🧠 Skills:", skills)
    print("\n📂 Sections:", sections)

    roles = match_roles(resume, skills, target_role)

    print("\n🎯 Best Roles:")
    for r in roles[:3]:
        print(f"{r[0]} → {r[1]}%")

    # ✅ DEFINE FIRST
    required_skills = get_required_skills(target_role)

    # ✅ THEN USE
    relevant = list(set(skills) & set(required_skills))

    print("\n🧠 Why this role?")
    if relevant:
        print(f"You are suited for {roles[0][0]} because you have relevant skills like {', '.join(relevant[:4])}.")
    else:
        print(f"You are partially aligned with {roles[0][0]} based on your overall profile.")

    # smooth scoring (less harsh)
    target_score = next((s for r, s in roles if target_role.lower() in r.lower()), 0)

    # normalize
    if target_score < 50:
        target_score += 10

    required_skills = get_required_skills(target_role)
    missing = get_missing_skills(skills, required_skills)

    print(f"\n📊 Match Score for {target_role}: {target_score}%")
    print("\n❗ Missing Skills:", missing)

    print("\n📚 Courses:", get_courses(missing))

    ats = ats_score(target_score, skills, required_skills, missing, sections)
    print(f"\n📈 ATS Score: {ats}/100")

    print("\n💡 Suggestions:")
    print("\n💡 Suggestions:")

    if missing:
        if "ml" in target_role.lower() or "ai" in target_role.lower():
            print("- Focus on these ML skills:", ", ".join(missing))
        elif "data" in target_role.lower():
            print("- Focus on these data skills:", ", ".join(missing))
        else:
            print("- Improve these skills:", ", ".join(missing))

    if target_score < 60:
        print("- Strengthen your core concepts with real projects")

    if "machine learning" in skills and "ml" in target_role.lower():
        print("- Move to advanced ML topics (deep learning, deployment)")

    