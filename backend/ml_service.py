"""
ml_service.py — Inference-only ML service.
All scoring and prediction paths are model-based.
"""

import os
import sys
import tempfile
from typing import Iterable

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ML_DIR = os.path.join(ROOT_DIR, "ml")
sys.path.insert(0, ROOT_DIR)

from ml.inference.predict_role import load_role_artifact, predict_roles_from_embedding
from ml.inference.predict_score import build_ats_features, load_ats_artifact, predict_ats_score
from ml.train.clustering import train_role_clustering
from ml.train.train_classifier import train_role_classifier
from ml.train.train_regressor import train_ats_regressor
from ml.utils import clean_text, extract_pdf, extract_sections, extract_skills


def _ensure_models() -> None:
    models_dir = os.path.join(ML_DIR, "models")
    role_path = os.path.join(models_dir, "role_model.pkl")
    ats_path = os.path.join(models_dir, "ats_model.pkl")
    cluster_path = os.path.join(models_dir, "cluster_model.pkl")
    if not os.path.exists(role_path):
        train_role_classifier()
    if not os.path.exists(ats_path):
        train_ats_regressor()
    if not os.path.exists(cluster_path):
        train_role_clustering()


def _normalize_role(role: str) -> str:
    return str(role).strip().lower().title()


def _cosine_skill_relevance(user_skills: list[str], required_skills: list[str]) -> float:
    if not user_skills or not required_skills:
        return 0.0
    user_emb = _model.encode(user_skills, convert_to_numpy=True, normalize_embeddings=True)
    req_emb = _model.encode(required_skills, convert_to_numpy=True, normalize_embeddings=True)
    sim = util.cos_sim(user_emb, req_emb).cpu().numpy()
    return float(np.max(sim, axis=0).mean())


def _embedding_missing_skills(user_skills: list[str], required_skills: list[str]) -> list[str]:
    if not required_skills:
        return []
    if not user_skills:
        return required_skills

    user_emb = _model.encode(user_skills, convert_to_numpy=True, normalize_embeddings=True)
    req_emb = _model.encode(required_skills, convert_to_numpy=True, normalize_embeddings=True)
    sim = util.cos_sim(req_emb, user_emb).cpu().numpy()
    best = np.max(sim, axis=1)
    return [required_skills[i] for i, score in enumerate(best) if score < 0.55]


def _recommend_courses(missing_skills: list[str], top_k: int = 3) -> dict[str, list[str]]:
    if not missing_skills:
        return {}
    missing_emb = _model.encode(missing_skills, convert_to_numpy=True, normalize_embeddings=True)
    rec: dict[str, list[str]] = {}
    for i, skill in enumerate(missing_skills):
        sim = util.cos_sim(missing_emb[i], _course_skill_embeddings)[0].cpu().numpy()
        top_idx = np.argsort(sim)[::-1][:top_k]
        rec[skill] = _courses_df.iloc[top_idx]["course"].tolist()
    return rec


def _cluster_alternatives(roles: Iterable[str], target_role: str) -> list[str]:
    role_clusters = _cluster_artifact["role_clusters"]
    cluster_to_roles = _cluster_artifact["cluster_to_roles"]
    target = _normalize_role(target_role)
    if target in role_clusters:
        cluster_id = role_clusters[target]
    else:
        normalized_roles = [_normalize_role(r) for r in roles]
        first_existing = next((r for r in normalized_roles if r in role_clusters), None)
        if first_existing is None:
            return []
        cluster_id = role_clusters[first_existing]
    candidates = cluster_to_roles.get(cluster_id, [])
    return [role for role in candidates if role != target][:5]


def get_required_skills(role: str) -> list[str]:
    row = _skills_df[_skills_df["role"] == str(role).strip().lower()]
    if row.empty:
        return []
    return [s.strip().lower() for s in str(row.iloc[0]["skills"]).split(";") if s.strip()]


def get_available_roles() -> list[str]:
    role_names = _role_artifact.get("role_names", [])
    if not role_names:
        role_names = sorted(set(_role_artifact.get("job_roles", [])))
    return sorted({str(role).strip() for role in role_names if str(role).strip()})


def match_roles(resume: str, user_skills: list[str], target_role: str) -> list[tuple]:
    resume_embedding = _model.encode(
        clean_text(resume), convert_to_numpy=True, normalize_embeddings=True
    )
    return predict_roles_from_embedding(resume_embedding, _role_artifact, top_k=10)


def ats_score(
    resume_embedding: np.ndarray,
    user_skills: list[str],
    required_skills: list[str],
    sections: dict,
) -> float:
    skill_relevance = _cosine_skill_relevance(user_skills, required_skills)
    features = build_ats_features(
        resume_embedding=resume_embedding,
        skill_count=len(user_skills),
        skill_relevance_score=skill_relevance,
        sections=sections,
    )
    return predict_ats_score(features, _ats_artifact)


def build_suggestions(target_role: str, missing: list[str], ats: float, alternatives: list[str]) -> list[str]:
    suggestions: list[str] = []
    if missing:
        suggestions.append(f"Prioritize these missing skills: {', '.join(missing[:5])}")
    if alternatives:
        suggestions.append(f"Related roles from your cluster: {', '.join(alternatives[:3])}")
    suggestions.append(f"Current ATS projection: {ats}/100. Improve experience evidence and quantified outcomes.")
    return suggestions


def analyze_resume(pdf_bytes: bytes, target_role: str) -> dict:
    """
    Full pipeline: bytes → structured result dict.
    Called by the FastAPI route handler.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        resume_text = extract_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)

    resume_clean = clean_text(resume_text)
    resume_embedding = _model.encode(
        resume_clean,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    user_skills = extract_skills(resume_text)
    sections = extract_sections(resume_text)
    all_roles = predict_roles_from_embedding(resume_embedding, _role_artifact, top_k=10)
    target_score = next(
        (s for r, s in all_roles if _normalize_role(r) == _normalize_role(target_role)),
        0.0,
    )
    required_skills = get_required_skills(target_role)
    missing = _embedding_missing_skills(user_skills, required_skills)
    courses = _recommend_courses(missing)
    ats = ats_score(resume_embedding, user_skills, required_skills, sections)
    alternatives = _cluster_alternatives([r for r, _ in all_roles], target_role)
    suggestions = build_suggestions(target_role, missing, ats, alternatives)

    return {
        "predicted_roles":    [{"role": r, "score": s} for r, s in all_roles[:10]],
        "target_match_score": round(target_score, 2),
        "skills":             user_skills,
        "missing_skills":     missing,
        "courses":            courses,
        "ats_score":          ats,
        "sections":           sections,
        "suggestions":        suggestions,
    }


_ensure_models()
print("[ml_service] Loading sentence-transformer model...")
_model = SentenceTransformer("all-MiniLM-L6-v2")
_DATA_DIR = os.path.join(ML_DIR, "data")
_skills_df = pd.read_csv(os.path.join(_DATA_DIR, "skills.csv"))
_courses_df = pd.read_csv(os.path.join(_DATA_DIR, "courses.csv"))
_skills_df["role"] = _skills_df["role"].astype(str).str.lower().str.strip()
_courses_df["skill"] = _courses_df["skill"].astype(str).str.lower().str.strip()
_course_skill_embeddings = _model.encode(
    _courses_df["skill"].tolist(),
    convert_to_numpy=True,
    normalize_embeddings=True,
)
_role_artifact = load_role_artifact()
_ats_artifact = load_ats_artifact()
with open(os.path.join(ML_DIR, "models", "cluster_model.pkl"), "rb") as _f:
    import pickle

    _cluster_artifact = pickle.load(_f)
print("[ml_service] Ready.")
