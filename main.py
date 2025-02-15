#!/usr/bin/env python3
"""
Main CLI driver for code-to-pipeline.
By default, it scans the entire repository recursively using the repository’s .gitignore rules (and built-in defaults)
to exclude files. It extracts full file content along with AST/dependency analysis and LLM hints (if enabled),
then generates granular text chunks (e.g., per function/class from AST, plus file-level fallback) for embedding.
If embedding generation is enabled (default), embeddings are generated and clustered,
and the resulting high-dimensional data is written to a separate file ("embeddings.json").
The final YAML output includes repository metadata, a formatted project tree, a detailed directory structure,
an adaptive pipeline definition, and a reference to the embeddings file.
Supports YAML or JSON export and includes LLM hints when enabled (--llm-hint flag).
"""

import argparse
import glob
import os
import sys
import logging
import yaml
import json
from collections import defaultdict
import fnmatch

from config import DEFAULT_PROJECT_TYPE, DEFAULT_IGNORE_FILES, DEFAULT_INCLUDE_EXTENSIONS
from project_detector import detect_project_type
from file_scanner import load_gitignore, scan_repository, load_cache, save_cache
from pipeline_generator import generate_pipeline_definition
from tree_generator import create_tree_structure
from embedding_generator import load_model, generate_embeddings, cluster_embeddings, MODEL_NAME

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def expand_source_patterns(source_patterns):
    """
    If source_patterns are provided, expand them to full paths.
    If none are provided, default to scanning the entire repository ('.').
    """
    if not source_patterns:
        return ["."]
    expanded = []
    for pattern in source_patterns:
        pattern = os.path.expanduser(pattern)
        if "*" in pattern and "**" not in pattern:
            directory = os.path.dirname(pattern)
            file_pattern = os.path.basename(pattern)
            recursive_pattern = os.path.join(directory, "**", file_pattern)
            matches = glob.glob(recursive_pattern, recursive=True)
            if matches:
                expanded.extend(matches)
            else:
                expanded.extend(glob.glob(pattern, recursive=True))
        else:
            expanded.extend(glob.glob(pattern, recursive=True))
    return expanded

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scan a code repository and output a structured document (YAML/JSON) for reasoning models. "
                    "By default, the entire repository is scanned recursively using .gitignore and built-in ignore rules. "
                    "The tool also generates granular embeddings for the code's business logic for clustering, interactive search, and reconstruction."
    )
    # Default: if no source_patterns provided, scan the whole repo.
    parser.add_argument("source_patterns", nargs="*", default=["."],
                        help="Optional: One or more source paths or glob patterns (e.g., ./src, ./hyvideo, ./src/*.py). "
                             "If omitted, the entire repository ('.') is scanned.")
    parser.add_argument("--project-type", default=DEFAULT_PROJECT_TYPE,
                        help="Specify the project type (e.g., 'python_backend', 'frontend', 'generic'). "
                             "If not provided, the tool will auto-detect from the repo.")
    parser.add_argument("--ignore-files", nargs="*", default=list(DEFAULT_IGNORE_FILES),
                        help="Filenames to ignore (e.g., LICENSE.md, PRIVACY.md).")
    parser.add_argument("--ignore", nargs="*", default=[],
                        help="Additional ignore patterns (e.g., *.mp4, somefile.txt) to exclude from scanning.")
    parser.add_argument("--include-extensions", nargs="*", default=list(DEFAULT_INCLUDE_EXTENSIONS),
                        help="File extensions to include (e.g., .py, .md). If empty, all files are included.")
    parser.add_argument("--output-format", choices=["yaml", "json"], default="yaml",
                        help="Output format: YAML (default) or JSON.")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching of scan results.")
    parser.add_argument("--llm-hint", action="store_true", help="Include LLM hints at each granular level.")
    parser.add_argument("--cluster", type=int, default=5, help="Number of clusters for embeddings.")
    parser.add_argument("--no-embeddings", action="store_true", help="Skip embedding generation entirely.")
    return parser.parse_args()

def combine_results(results_list):
    combined = {
        "repository_path": "Multiple Sources",
        "total_files": 0,
        "total_size_bytes": 0,
        "files": [],
        "directory_structure": {}
    }
    ds = defaultdict(list)
    for res in results_list:
        combined["total_files"] += res.get("total_files", 0)
        combined["total_size_bytes"] += res.get("total_size_bytes", 0)
        combined["files"].extend(res.get("files", []))
        for key, files in res.get("directory_structure", {}).items():
            ds[key].extend(files)
    combined["directory_structure"] = dict(ds)
    return combined

def extract_texts_for_embedding(files: list[dict]) -> list[dict]:
    """
    Extract a list of text chunks for embedding from the file list.
    For each file:
      - If AST analysis is available, extract each function's and class's llm_hint (or a fallback description)
        as a separate text chunk.
      - Always include a fallback file-level text (using llm_hint if available, else full_content).
    Returns a list of dictionaries with 'source' and 'metadata'.
    """
    chunks = []
    for file in files:
        base_meta = {"file": file.get("filename"), "path": file.get("relative_path")}
        ast_data = file.get("ast_analysis", {})
        if ast_data:
            for func in ast_data.get("functions", []):
                text = func.get("llm_hint") or f"Function {func.get('name')} in {file.get('filename')}"
                meta = base_meta.copy()
                meta.update({"type": "function", "name": func.get("name")})
                chunks.append({"source": text, "metadata": meta})
            for cls in ast_data.get("classes", []):
                text = cls.get("llm_hint") or f"Class {cls.get('name')} in {file.get('filename')}"
                meta = base_meta.copy()
                meta.update({"type": "class", "name": cls.get("name")})
                chunks.append({"source": text, "metadata": meta})
        file_text = file.get("llm_hint") or file.get("full_content", "")
        meta = base_meta.copy()
        meta.update({"type": "file"})
        chunks.append({"source": file_text, "metadata": meta})
    return chunks

def main():
    args = parse_arguments()
    source_paths = expand_source_patterns(args.source_patterns)
    if not source_paths:
        logger.error("No valid source paths found. Exiting.")
        sys.exit(1)

    if args.project_type != DEFAULT_PROJECT_TYPE:
        project_type = args.project_type
    else:
        first_dir = next((path for path in source_paths if os.path.isdir(path)), None)
        project_type = detect_project_type(first_dir) if first_dir else "generic"
    logger.info(f"Detected/Using project type: {project_type}")

    first_dir = next((path for path in source_paths if os.path.isdir(path)), os.path.dirname(source_paths[0]))
    ignore_spec = load_gitignore(first_dir)
    combined_ignore = set(args.ignore_files) | set(args.ignore)

    scan_results = []
    for path in source_paths:
        if os.path.isdir(path):
            cache_data = None
            if not args.no_cache:
                cache_data = load_cache()
            if cache_data and cache_data.get("repository_path") == os.path.abspath(path):
                logger.info(f"Using cached data for {path}.")
                res = cache_data
            else:
                res = scan_repository(path, ignore_spec, combined_ignore, set(args.include_extensions), project_type, llm_hunt=args.llm_hint)
                save_cache(res)
            scan_results.append(res)
        elif os.path.isfile(path):
            from file_scanner import get_file_info
            res = {
                "repository_path": os.path.abspath(os.path.dirname(path)),
                "total_files": 1,
                "total_size_bytes": os.path.getsize(path),
                "files": [get_file_info(path, os.path.dirname(path), project_type, llm_hunt=args.llm_hint)],
                "directory_structure": {".": [os.path.basename(path)]}
            }
            scan_results.append(res)
        else:
            logger.warning(f"Skipping unknown source type: {path}")

    combined_result = combine_results(scan_results)
    pipeline_definition = generate_pipeline_definition(project_type, llm_hunt=args.llm_hint)
    project_tree = create_tree_structure(combined_result.get("directory_structure", {}), combined_result["repository_path"])

    # Embedding generation is optional. If --no-embeddings is set, skip it.
    if not args.no_embeddings:
        from embedding_generator import load_model, generate_embeddings, cluster_embeddings
        text_chunks = extract_texts_for_embedding(combined_result["files"])
        texts_for_embedding = [chunk["source"] for chunk in text_chunks if chunk["source"].strip()]
        if texts_for_embedding:
            model = load_model()
            embeddings = generate_embeddings(texts_for_embedding, model)
            clusters = cluster_embeddings(embeddings, num_clusters=args.cluster)
            # Build a per-chunk cluster assignment list.
            cluster_assignment = [None] * len(texts_for_embedding)
            for label, indices in clusters.items():
                for idx in indices:
                    cluster_assignment[idx] = label
            granular_embeddings = []
            for i, chunk in enumerate(text_chunks):
                granular_embeddings.append({
                    "source": chunk["source"],
                    "metadata": chunk["metadata"],
                    "embedding": embeddings[i].tolist(),
                    "cluster": cluster_assignment[i]
                })
            # Save embeddings to a separate JSON file.
            with open("embeddings.json", "w", encoding="utf8") as f:
                json.dump({
                    "model": f"SentenceTransformer: {MODEL_NAME}",
                    "granular_embeddings": granular_embeddings
                }, f, indent=2)
            embeddings_output_ref = "embeddings.json"
        else:
            granular_embeddings = None
            embeddings_output_ref = None
    else:
        granular_embeddings = None
        embeddings_output_ref = None

    output = {
        "repository_metadata": {
            "repository_path": combined_result["repository_path"],
            "total_files": combined_result["total_files"],
            "total_size_bytes": combined_result["total_size_bytes"]
        },
        "project_tree": project_tree,
        "directory_structure": combined_result["directory_structure"],
        "files": combined_result["files"],
        "pipeline_definition": pipeline_definition["pipeline"],
        "embeddings_file": embeddings_output_ref  # Reference to the separate embeddings file.
    }

    if args.output_format == "json":
        print(json.dumps(output, indent=2))
    else:
        print(yaml.dump(output, sort_keys=False, allow_unicode=True))

if __name__ == "__main__":
    main()
