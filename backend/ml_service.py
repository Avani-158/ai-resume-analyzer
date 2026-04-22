"""
ml_service.py — Inference-only ML service.
All scoring and prediction paths are model-based.
"""

import os
import sys
import tempfile
import threading
import re
import difflib
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

_init_lock = threading.Lock()
_initialized = False

_model: SentenceTransformer | None = None
_skills_df: pd.DataFrame | None = None
_courses_df: pd.DataFrame | None = None
_course_skill_embeddings: np.ndarray | None = None
_role_artifact: dict | None = None
_ats_artifact: dict | None = None
_cluster_artifact: dict | None = None


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

def _ensure_initialized() -> None:
    """
    Lazy init to keep FastAPI import fast.
    This prevents Uvicorn from blocking on model downloads at import time.
    """
    global _initialized
    global _model, _skills_df, _courses_df, _course_skill_embeddings
    global _role_artifact, _ats_artifact, _cluster_artifact

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        _ensure_models()

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

        _initialized = True


def _normalize_role(role: str) -> str:
    return str(role).strip().lower().title()


ROLE_ALIASES = {
    "artificial intelligence engineer": "Ai Engineer",
    "ai eng": "Ai Engineer",
    "artificial intelligence researcher": "Ai Researcher",
    "machine learning engineer": "Ml Engineer",
    "ml engineer": "Ml Engineer",
    "nlp engineer": "Nlp Engineer",
}


def _resolve_target_role(target_role: str) -> str:
    _ensure_initialized()
    assert _role_artifact is not None

    raw = str(target_role).strip()
    normalized = re.sub(r"\s+", " ", raw.lower().strip())
    normalized = normalized.replace("&", "and")

    role_names = [str(r).strip() for r in _role_artifact.get("role_names", []) if str(r).strip()]
    role_lookup = {r.lower(): r for r in role_names}

    alias = ROLE_ALIASES.get(normalized)
    if alias and alias.lower() in role_lookup:
        return role_lookup[alias.lower()]

    if normalized in role_lookup:
        return role_lookup[normalized]

    softened = (
        normalized
        .replace("artificial intelligence", "ai")
        .replace("machine learning", "ml")
    )
    if softened in role_lookup:
        return role_lookup[softened]

    fuzzy = difflib.get_close_matches(normalized, list(role_lookup.keys()), n=1, cutoff=0.72)
    if fuzzy:
        return role_lookup[fuzzy[0]]

    return raw


def _normalize_skill_token(skill: str) -> str:
    value = str(skill).strip().lower()
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"[^a-z0-9+#.\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("powerbi", "power bi")
    value = value.replace("nodejs", "node.js").replace("node js", "node.js")
    value = value.replace("scikit learn", "scikit-learn")
    return value


def _augment_skills_from_text(resume_text: str, base_skills: list[str], required_skills: list[str]) -> list[str]:
    """
    Preserve extractor output but also detect required skills by exact token matching
    so obvious skills like "pandas" and "power bi" are not missed due to parser noise.
    """
    text = _normalize_skill_token(resume_text)
    detected = {_normalize_skill_token(s) for s in base_skills if _normalize_skill_token(s)}

    for skill in required_skills:
        norm = _normalize_skill_token(skill)
        if not norm:
            continue
        variants = {
            norm,
            norm.replace(".", " "),
            norm.replace(".", ""),
        }
        for variant in variants:
            pattern = r"\b" + re.escape(variant).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, text):
                detected.add(norm)
                break

    return sorted(detected)


def _role_match_score(
    resume_embedding: np.ndarray,
    target_role: str,
    required_skills: list[str],
    user_skills: list[str],
) -> float:
    """
    Blend semantic target-role similarity and required-skill coverage.
    This avoids pathological 0% matches when target role is not in top-k list.
    """
    _ensure_initialized()
    assert _model is not None
    assert _role_artifact is not None

    target = _normalize_role(_resolve_target_role(target_role))
    all_role_scores = predict_roles_from_embedding(
        resume_embedding,
        _role_artifact,
        top_k=max(10, len(_role_artifact.get("role_names", []))),
    )
    role_lookup = {_normalize_role(role): score for role, score in all_role_scores}
    model_score = float(role_lookup.get(target, 0.0))

    if required_skills:
        user_set = {_normalize_skill_token(s) for s in user_skills}
        req_set = {_normalize_skill_token(s) for s in required_skills}
        overlap = len(req_set.intersection(user_set))
        coverage = (overlap / max(len(req_set), 1)) * 100.0
    else:
        coverage = 0.0

    # Weighted blend gives stable, non-zero scores while still respecting model output.
    blended = 0.7 * model_score + 0.3 * coverage
    return round(max(0.0, min(100.0, blended)), 2)


def _cosine_skill_relevance(user_skills: list[str], required_skills: list[str]) -> float:
    _ensure_initialized()
    if not user_skills or not required_skills:
        return 0.0
    assert _model is not None
    user_emb = _model.encode(user_skills, convert_to_numpy=True, normalize_embeddings=True)
    req_emb = _model.encode(required_skills, convert_to_numpy=True, normalize_embeddings=True)
    sim = util.cos_sim(user_emb, req_emb).cpu().numpy()
    return float(np.max(sim, axis=0).mean())


def _embedding_missing_skills(user_skills: list[str], required_skills: list[str]) -> list[str]:
    _ensure_initialized()
    if not required_skills:
        return []
    if not user_skills:
        return required_skills

    normalized_user = {_normalize_skill_token(s) for s in user_skills}
    normalized_required = [_normalize_skill_token(s) for s in required_skills]

    exact_missing = []
    exact_present = set()
    for idx, skill in enumerate(normalized_required):
        if skill in normalized_user:
            exact_present.add(idx)
        else:
            exact_missing.append(idx)

    if not exact_missing:
        return []

    assert _model is not None
    user_emb = _model.encode(sorted(normalized_user), convert_to_numpy=True, normalize_embeddings=True)
    req_emb = _model.encode(normalized_required, convert_to_numpy=True, normalize_embeddings=True)
    sim = util.cos_sim(req_emb, user_emb).cpu().numpy()
    best = np.max(sim, axis=1)
    return [
        required_skills[i]
        for i, score in enumerate(best)
        if i not in exact_present and score < 0.50
    ]


def _recommend_courses(missing_skills: list[str], top_k: int = 3) -> dict[str, list[str]]:
    _ensure_initialized()
    if not missing_skills:
        return {}
    assert _model is not None
    assert _course_skill_embeddings is not None
    assert _courses_df is not None
    missing_emb = _model.encode(missing_skills, convert_to_numpy=True, normalize_embeddings=True)
    rec: dict[str, list[str]] = {}
    for i, skill in enumerate(missing_skills):
        sim = util.cos_sim(missing_emb[i], _course_skill_embeddings)[0].cpu().numpy()
        top_idx = np.argsort(sim)[::-1][:top_k]
        rec[skill] = _courses_df.iloc[top_idx]["course"].tolist()
    return rec


def _cluster_alternatives(roles: Iterable[str], target_role: str) -> list[str]:
    _ensure_initialized()
    assert _cluster_artifact is not None
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
    _ensure_initialized()
    assert _skills_df is not None
    resolved = _resolve_target_role(role)
    row = _skills_df[_skills_df["role"] == str(resolved).strip().lower()]
    if row.empty:
        return []
    return [s.strip().lower() for s in str(row.iloc[0]["skills"]).split(";") if s.strip()]


def get_available_roles() -> list[str]:
    _ensure_initialized()
    assert _role_artifact is not None
    role_names = _role_artifact.get("role_names", [])
    if not role_names:
        role_names = sorted(set(_role_artifact.get("job_roles", [])))
    return sorted({str(role).strip() for role in role_names if str(role).strip()})


def match_roles(resume: str, user_skills: list[str], target_role: str) -> list[tuple]:
    _ensure_initialized()
    assert _model is not None
    assert _role_artifact is not None
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
    _ensure_initialized()
    assert _ats_artifact is not None
    skill_relevance = _cosine_skill_relevance(user_skills, required_skills)
    features = build_ats_features(
        resume_embedding=resume_embedding,
        skill_count=len(user_skills),
        skill_relevance_score=skill_relevance,
        sections=sections,
    )
    model_score = predict_ats_score(features, _ats_artifact)

    user_set = {_normalize_skill_token(s) for s in user_skills}
    req_set = {_normalize_skill_token(s) for s in required_skills}
    coverage = (len(user_set.intersection(req_set)) / max(len(req_set), 1)) * 100.0 if req_set else 0.0

    section_score = (sum(1 for v in sections.values() if v) / max(len(sections), 1)) * 100.0
    skills_count_score = min(len(user_skills), 12) / 12.0 * 100.0

    heuristic_score = (0.55 * coverage) + (0.25 * section_score) + (0.20 * skills_count_score)
    blended = (0.35 * model_score) + (0.65 * heuristic_score)
    return round(max(0.0, min(100.0, blended)), 2)


def build_suggestions(target_role: str, missing: list[str], ats: float, alternatives: list[str]) -> list[str]:
    suggestions: list[str] = []
    if missing:
        suggestions.append(f"Prioritize these missing skills: {', '.join(missing[:5])}")
    if alternatives:
        suggestions.append(f"Related roles from your cluster: {', '.join(alternatives[:3])}")
    suggestions.append(f"Current ATS projection: {ats}/100. Improve experience evidence and quantified outcomes.")
    return suggestions


def _resume_quality_signal(resume_text: str, skills: list[str], sections: dict) -> dict:
    normalized = clean_text(resume_text)
    token_count = len(normalized.split())

    contact_markers = [
        "@",
        "linkedin",
        "github",
        "phone",
        "email",
    ]
    section_score = sum(1 for value in sections.values() if value)
    marker_score = sum(1 for marker in contact_markers if marker in resume_text.lower())

    # Heuristic confidence score in [0, 1].
    confidence = 0.0
    confidence += min(token_count / 250.0, 1.0) * 0.35
    confidence += min(len(skills) / 10.0, 1.0) * 0.30
    confidence += min(section_score / 4.0, 1.0) * 0.25
    confidence += min(marker_score / 3.0, 1.0) * 0.10

    likely_resume = (
        (section_score >= 2 and len(skills) >= 4 and token_count >= 100)
        or confidence >= 0.50
    )
    return {
        "likely_resume": likely_resume,
        "confidence": round(float(confidence), 3),
        "token_count": token_count,
        "section_score": section_score,
        "skills_count": len(skills),
    }


def analyze_resume(pdf_bytes: bytes, target_role: str) -> dict:
    """
    Full pipeline: bytes → structured result dict.
    Called by the FastAPI route handler.
    """
    _ensure_initialized()
    assert _model is not None
    assert _role_artifact is not None
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
    resolved_target_role = _resolve_target_role(target_role)
    required_skills = get_required_skills(resolved_target_role)
    user_skills = _augment_skills_from_text(
        resume_text=resume_text,
        base_skills=extract_skills(resume_text),
        required_skills=required_skills,
    )
    sections = extract_sections(resume_text)
    quality = _resume_quality_signal(resume_text, user_skills, sections)
    if not quality["likely_resume"]:
        raise ValueError(
            "Uploaded PDF does not look like a resume. "
            "Please upload a CV/resume with sections like Skills, Experience, Education, or Projects."
        )

    all_roles = predict_roles_from_embedding(resume_embedding, _role_artifact, top_k=10)
    target_score = _role_match_score(
        resume_embedding=resume_embedding,
        target_role=resolved_target_role,
        required_skills=required_skills,
        user_skills=user_skills,
    )
    missing = _embedding_missing_skills(user_skills, required_skills)
    courses = _recommend_courses(missing)
    ats = ats_score(resume_embedding, user_skills, required_skills, sections)
    alternatives = _cluster_alternatives([r for r, _ in all_roles], resolved_target_role)
    suggestions = build_suggestions(resolved_target_role, missing, ats, alternatives)

    return {
        "predicted_roles":    [{"role": r, "score": s} for r, s in all_roles[:10]],
        "target_match_score": round(target_score, 2),
        "skills":             user_skills,
        "missing_skills":     missing,
        "courses":            courses,
        "ats_score":          ats,
        "sections":           sections,
        "suggestions":        suggestions,
        "resume_quality":     quality,
    }
