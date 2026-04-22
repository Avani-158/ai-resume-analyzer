import os
import pickle

import numpy as np


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")


def load_ats_artifact(path: str | None = None) -> dict:
    model_path = path or os.path.join(MODELS_DIR, "ats_model.pkl")
    with open(model_path, "rb") as f:
        return pickle.load(f)


def build_ats_features(
    resume_embedding: np.ndarray,
    skill_count: int,
    skill_relevance_score: float,
    sections: dict,
) -> np.ndarray:
    section_count = float(sum(1 for value in sections.values() if value))
    features = np.hstack(
        [
            np.array(resume_embedding, dtype=float).ravel(),
            np.array(
                [
                    float(skill_count),
                    float(skill_relevance_score),
                    section_count,
                ],
                dtype=float,
            ),
        ]
    )
    return features.reshape(1, -1)


def predict_ats_score(feature_vector: np.ndarray, artifact: dict) -> float:
    model = artifact["model"]
    raw = float(model.predict(feature_vector)[0])
    return round(max(0.0, min(100.0, raw)), 2)
