"""
Module: embedding_generator.py

This module provides functionality to generate embeddings for granular pieces of code (or extracted business logic),
cluster these embeddings, and visualize them for further analysis. Beyond clustering, these embeddings can be used
for interactive search, nearest-neighbor lookup, or even to drive code reconstruction by identifying related modules.
This is powerful for deconstructing a code repository into its most granular, reconstructible components.

Dependencies:
    - sentence-transformers (for generating embeddings)
    - scikit-learn (for clustering and PCA)
    - umap-learn (for enhanced dimensionality reduction and visualization)
    - matplotlib (for visualization)
"""

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import umap
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight, fast model

def load_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """
    Load the SentenceTransformer model.
    """
    logger.info(f"Loading SentenceTransformer model: {model_name}")
    model = SentenceTransformer(model_name)
    return model

def generate_embeddings(texts: list[str], model: SentenceTransformer = None) -> np.array:
    """
    Generate embeddings for a list of text strings.
    
    Args:
        texts: List of text strings.
        model: An optional pre-loaded SentenceTransformer model. If not provided, it will be loaded.
        
    Returns:
        A NumPy array of embeddings.
    """
    if model is None:
        model = load_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings

def cluster_embeddings(embeddings: np.array, num_clusters: int = 5) -> dict:
    """
    Cluster the given embeddings using KMeans.
    
    Args:
        embeddings: A NumPy array of embeddings.
        num_clusters: The number of clusters to form.
    
    Returns:
        A dictionary mapping each cluster label to a list of indices corresponding to the input texts.
    """
    logger.info(f"Clustering {len(embeddings)} embeddings into {num_clusters} clusters")
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(embeddings)
    clusters = {}
    for idx, label in enumerate(cluster_labels):
        clusters.setdefault(int(label), []).append(idx)
    return clusters

def visualize_embeddings_pca(embeddings: np.array, cluster_labels: list[int] = None, save_path: str = None):
    """
    Visualize embeddings using PCA to reduce dimensions to 2D.
    
    Args:
        embeddings: A NumPy array of embeddings.
        cluster_labels: An optional list of cluster labels for coloring the points.
        save_path: If provided, the figure will be saved to this path.
    """
    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings)
    plt.figure(figsize=(10, 8))
    if cluster_labels is not None:
        scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=cluster_labels, cmap="viridis", alpha=0.7)
        plt.colorbar(scatter)
    else:
        plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.7)
    plt.title("Embedding Visualization (PCA Reduction)")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    if save_path:
        plt.savefig(save_path)
    plt.show()

def visualize_embeddings_umap(embeddings: np.array, cluster_labels: list[int] = None, save_path: str = None):
    """
    Visualize embeddings using UMAP to reduce dimensions to 2D.
    
    Args:
        embeddings: A NumPy array of embeddings.
        cluster_labels: An optional list of cluster labels for coloring the points.
        save_path: If provided, the figure will be saved to this path.
    """
    reducer = umap.UMAP(n_components=2, random_state=42)
    reduced = reducer.fit_transform(embeddings)
    plt.figure(figsize=(10, 8))
    if cluster_labels is not None:
        scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=cluster_labels, cmap="plasma", alpha=0.7)
        plt.colorbar(scatter)
    else:
        plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.7)
    plt.title("Embedding Visualization (UMAP Reduction)")
    plt.xlabel("UMAP Component 1")
    plt.ylabel("UMAP Component 2")
    if save_path:
        plt.savefig(save_path)
    plt.show()

if __name__ == "__main__":
    # Example test run for interactive usage:
    sample_texts = [
        "def add(a, b): return a + b",
        "class User: pass",
        "def configure_logging(): setup logging for application",
        "import os\nos.system('echo hello')",
        "def main(): print('Hello, World!')"
    ]
    model = load_model()
    embeddings = generate_embeddings(sample_texts, model)
    clusters = cluster_embeddings(embeddings, num_clusters=2)
    logger.info(f"Clusters: {clusters}")
    # For visualization, create a cluster assignment list.
    cluster_assignment = [None] * len(sample_texts)
    for label, indices in clusters.items():
        for idx in indices:
            cluster_assignment[idx] = label
    visualize_embeddings_pca(embeddings, cluster_labels=cluster_assignment)
    visualize_embeddings_umap(embeddings, cluster_labels=cluster_assignment)
