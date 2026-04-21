import os
import pickle

import numpy as np
from sentence_transformers import util


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")


def load_role_artifact(path: str | None = None) -> dict:
    model_path = path or os.path.join(MODELS_DIR, "role_model.pkl")
    with open(model_path, "rb") as f:
        return pickle.load(f)


def predict_roles_from_embedding(
    resume_embedding: np.ndarray,
    artifact: dict,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    x = np.array(resume_embedding, dtype=float).reshape(1, -1)
    role_prototypes: dict[str, np.ndarray] = artifact.get("role_prototypes", {})

    # Use per-role cosine similarity so each score is independent (not a fixed 100% split).
    if role_prototypes:
        role_names = list(role_prototypes.keys())
        proto_matrix = np.array([role_prototypes[role] for role in role_names], dtype=float)

        similarities = util.cos_sim(x, proto_matrix)[0].cpu().numpy()
        # Map cosine from [-1, 1] to [0, 100] independently per role.
        scores = ((similarities + 1.0) / 2.0) * 100.0

        sorted_idx = np.argsort(scores)[::-1][:top_k]
        return [(role_names[idx], round(float(scores[idx]), 2)) for idx in sorted_idx]

    # Fallback for older artifacts missing role prototypes.
    model = artifact["model"]
    label_encoder = artifact["label_encoder"]
    probabilities = model.predict_proba(x)[0]
    sorted_idx = np.argsort(probabilities)[::-1][:top_k]
    return [
        (label_encoder.inverse_transform([idx])[0], round(float(probabilities[idx] * 100.0), 2))
        for idx in sorted_idx
    ]


def role_similarity_scores(
    resume_embedding: np.ndarray,
    artifact: dict,
    top_k: int = 10,
) -> list[tuple[str, float]]:
    job_embeddings = np.array(artifact["job_embeddings"], dtype=float)
    job_roles = artifact["job_roles"]

    similarities = util.cos_sim(
        np.array(resume_embedding, dtype=float).reshape(1, -1),
        job_embeddings,
    )[0]

    per_role_best = {}
    for i, sim in enumerate(similarities):
        role = job_roles[i]
        score = float(sim)
        if role not in per_role_best or score > per_role_best[role]:
            per_role_best[role] = score

    sorted_roles = sorted(per_role_best.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(role, round(score * 100.0, 2)) for role, score in sorted_roles]
