import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")


def _normalize_role(role: str) -> str:
    return str(role).strip().lower().title()


def train_role_classifier() -> str:
    os.makedirs(MODELS_DIR, exist_ok=True)

    jobs = pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))
    jobs = jobs.dropna(subset=["role", "description"]).copy()
    jobs["role"] = jobs["role"].apply(_normalize_role)
    jobs["description"] = jobs["description"].astype(str)
    jobs = jobs.drop_duplicates(subset=["role", "description"])

    encoder_model = SentenceTransformer("all-MiniLM-L6-v2")
    description_embeddings = encoder_model.encode(
        jobs["description"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
    )

    labels = LabelEncoder().fit_transform(jobs["role"])
    try:
        x_train, x_val, y_train, y_val = train_test_split(
            description_embeddings,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels,
        )
    except ValueError:
        x_train, x_val, y_train, y_val = train_test_split(
            description_embeddings,
            labels,
            test_size=0.2,
            random_state=42,
        )

    logistic = LogisticRegression(max_iter=2000, n_jobs=None)
    logistic.fit(x_train, y_train)
    logistic_acc = accuracy_score(y_val, logistic.predict(x_val))

    forest = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1,
    )
    forest.fit(x_train, y_train)
    forest_acc = accuracy_score(y_val, forest.predict(x_val))

    best_model = forest if forest_acc >= logistic_acc else logistic

    role_prototypes = {}
    for role, group in jobs.groupby("role"):
        idx = group.index.to_numpy()
        role_prototypes[role] = np.mean(description_embeddings[idx], axis=0)

    artifact = {
        "model": best_model,
        "label_encoder": LabelEncoder().fit(jobs["role"]),
        "role_names": sorted(jobs["role"].unique().tolist()),
        "job_roles": jobs["role"].tolist(),
        "job_descriptions": jobs["description"].tolist(),
        "job_embeddings": description_embeddings,
        "role_prototypes": role_prototypes,
        "metrics": {
            "logistic_accuracy": float(logistic_acc),
            "random_forest_accuracy": float(forest_acc),
            "chosen_model": type(best_model).__name__,
        },
    }

    output_path = os.path.join(MODELS_DIR, "role_model.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(artifact, f)

    return output_path


if __name__ == "__main__":
    path = train_role_classifier()
    print(f"Saved classifier artifact to: {path}")
