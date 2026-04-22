import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
sys.path.insert(0, BASE_DIR)

from utils import extract_sections, extract_skills


def _normalize_role(role: str) -> str:
    return str(role).strip().lower().title()


def _build_feature_matrix(jobs: pd.DataFrame, model: SentenceTransformer) -> np.ndarray:
    embeddings = model.encode(
        jobs["description"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
    )
    skills = jobs["description"].apply(extract_skills).tolist()
    section_flags = jobs["description"].apply(extract_sections).tolist()

    skills_count = np.array([len(s) for s in skills], dtype=float).reshape(-1, 1)
    unique_skills_count = np.array([len(set(s)) for s in skills], dtype=float).reshape(-1, 1)
    section_count = np.array(
        [sum(1 for v in sec.values() if v) for sec in section_flags],
        dtype=float,
    ).reshape(-1, 1)

    return np.hstack([embeddings, skills_count, unique_skills_count, section_count])


def _build_pseudo_targets(feature_matrix: np.ndarray) -> np.ndarray:
    latent = PCA(n_components=1, random_state=42).fit_transform(feature_matrix).ravel()
    min_val = float(latent.min())
    max_val = float(latent.max())
    denom = max(max_val - min_val, 1e-6)
    normalized = (latent - min_val) / denom
    return normalized * 100.0


def train_ats_regressor() -> str:
    os.makedirs(MODELS_DIR, exist_ok=True)

    jobs = pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))
    jobs = jobs.dropna(subset=["role", "description"]).copy()
    jobs["role"] = jobs["role"].apply(_normalize_role)
    jobs["description"] = jobs["description"].astype(str)
    jobs = jobs.drop_duplicates(subset=["role", "description"])

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    feature_matrix = _build_feature_matrix(jobs, embedding_model)
    targets = _build_pseudo_targets(feature_matrix)

    x_train, x_val, y_train, y_val = train_test_split(
        feature_matrix,
        targets,
        test_size=0.2,
        random_state=42,
    )

    linear = LinearRegression()
    linear.fit(x_train, y_train)
    linear_mae = mean_absolute_error(y_val, linear.predict(x_val))

    gbr = GradientBoostingRegressor(random_state=42)
    gbr.fit(x_train, y_train)
    gbr_mae = mean_absolute_error(y_val, gbr.predict(x_val))

    best_model = gbr if gbr_mae <= linear_mae else linear
    artifact = {
        "model": best_model,
        "feature_description": [
            "resume_embedding",
            "skills_count",
            "unique_skills_count",
            "section_count",
        ],
        "metrics": {
            "linear_mae": float(linear_mae),
            "gbr_mae": float(gbr_mae),
            "chosen_model": type(best_model).__name__,
        },
    }

    output_path = os.path.join(MODELS_DIR, "ats_model.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(artifact, f)

    return output_path


if __name__ == "__main__":
    path = train_ats_regressor()
    print(f"Saved ATS regressor artifact to: {path}")
