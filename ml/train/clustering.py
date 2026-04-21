import os
import pickle

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")


def _normalize_role(role: str) -> str:
    return str(role).strip().lower().title()


def train_role_clustering(n_clusters: int = 8) -> str:
    os.makedirs(MODELS_DIR, exist_ok=True)

    jobs = pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))
    jobs = jobs.dropna(subset=["role", "description"]).copy()
    jobs["role"] = jobs["role"].apply(_normalize_role)
    jobs["description"] = jobs["description"].astype(str)
    jobs = jobs.drop_duplicates(subset=["role", "description"])

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embedding_model.encode(
        jobs["description"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
    )

    roles = jobs["role"].tolist()
    unique_roles = sorted(set(roles))
    role_to_idx = {role: i for i, role in enumerate(unique_roles)}
    role_vectors = np.zeros((len(unique_roles), embeddings.shape[1]), dtype=float)
    counts = np.zeros(len(unique_roles), dtype=float)

    for i, role in enumerate(roles):
        ridx = role_to_idx[role]
        role_vectors[ridx] += embeddings[i]
        counts[ridx] += 1.0

    counts = np.maximum(counts.reshape(-1, 1), 1.0)
    role_vectors = role_vectors / counts

    n_clusters = max(2, min(n_clusters, len(unique_roles)))
    cluster_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = cluster_model.fit_predict(role_vectors)

    role_clusters = {
        role: int(cluster_labels[role_to_idx[role]]) for role in unique_roles
    }
    cluster_to_roles = {}
    for role, cluster_id in role_clusters.items():
        cluster_to_roles.setdefault(cluster_id, []).append(role)

    artifact = {
        "model": cluster_model,
        "unique_roles": unique_roles,
        "role_vectors": role_vectors,
        "role_clusters": role_clusters,
        "cluster_to_roles": cluster_to_roles,
    }

    output_path = os.path.join(MODELS_DIR, "cluster_model.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(artifact, f)

    return output_path


if __name__ == "__main__":
    path = train_role_clustering()
    print(f"Saved clustering artifact to: {path}")
