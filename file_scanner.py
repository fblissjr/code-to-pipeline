"""
Module to scan the repository.
Uses concurrency, respects .gitignore and default ignore patterns, excludes sensitive files,
and outputs complete file content, AST analysis, tokenized representations, and LLM hints if enabled.
Requires: pip install pathspec tiktoken tree_sitter networkx
"""

import os
import pickle
import logging
import fnmatch
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import pathspec
import tiktoken

from ast_analyzer import analyze_file
from config import SENSITIVE_FILES, DEFAULT_IGNORE_FILES, DEFAULT_INCLUDE_EXTENSIONS, CACHE_FILENAME
from ignore_patterns import DEFAULT_IGNORE_PATTERNS

logger = logging.getLogger(__name__)

def load_gitignore(repo_path):
    """
    Load ignore patterns from .gitignore (if exists) and combine with default ignore patterns.
    Filters out blank lines and comments. Returns a PathSpec object.
    """
    patterns = []
    gitignore_path = os.path.join(repo_path, ".gitignore")
    if os.path.isfile(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf8", errors="replace") as f:
                patterns = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
        except Exception as e:
            logger.warning(f"Failed to read .gitignore: {e}")
    combined_patterns = set(patterns) | DEFAULT_IGNORE_PATTERNS | DEFAULT_IGNORE_FILES
    return pathspec.PathSpec.from_lines("gitwildmatch", combined_patterns)

def get_project_specific_ignore_extensions(project_type: str) -> set[str]:
    if project_type == "python_backend":
        return {".pyc", ".pyo", ".pyd", ".so"}
    elif project_type == "typescript":
        return {".d.ts"}
    elif project_type == "javascript":
        return set()
    else:
        return set()

def tokenize_content(content: str) -> dict[str, any]:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        token_ids = encoding.encode(content, disallowed_special=())
        token_count = len(token_ids)
        tokenized_text = encoding.decode(token_ids)
        return {
            "tokens": token_ids,
            "token_count": token_count,
            "tokenized_text": tokenized_text,
        }
    except Exception as e:
        logger.error(f"Tokenization error: {e}")
        return {"error": str(e)}

def get_file_info(file_path, base_path, project_type, language="python", llm_hint=False):
    """
    Extract file metadata, full content, AST analysis, tokenized version, and an LLM hint.
    """
    rel_path = os.path.relpath(file_path, base_path)
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower() or "none"
    try:
        size = os.path.getsize(file_path)
    except Exception:
        size = 0
    try:
        with open(file_path, "r", encoding="utf8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        content = f"<<Error reading file: {e}>>"
    
    tokenized = tokenize_content(content)
    file_hint = f"This file '{filename}' of type '{ext}' contains source code. "
    if project_type == "python_backend" and ext == ".py":
        file_hint += "Focus on its function and class definitions to extract business logic."
    elif project_type in {"javascript", "typescript"} and ext in {".js", ".jsx", ".ts", ".tsx"}:
        file_hint += "Analyze JavaScript/TypeScript constructs for behavior and dependencies."
    file_hint += " Full content is provided for detailed analysis."
    
    file_info = {
        "relative_path": rel_path,
        "filename": filename,
        "extension": ext,
        "size_bytes": size,
        "full_content": content,
        "tokenization": tokenized,
        "llm_hint": file_hint if llm_hint else ""
    }
    
    if project_type == "python_backend" and ext == ".py":
        file_info["ast_analysis"] = analyze_file(content, language="python", llm_hunt=llm_hint)
    elif project_type in {"javascript", "typescript"} and ext in {".js", ".jsx", ".ts", ".tsx"}:
        file_info["ast_analysis"] = analyze_file(content, language="javascript", llm_hunt=llm_hint)
    
    return file_info

def scan_repository(repo_path, ignore_spec, ignore_patterns, include_extensions, project_type, llm_hunt=False):
    repo_files = []
    directory_structure = defaultdict(list)
    total_size = 0
    total_files = 0

    project_ignore_ext = get_project_specific_ignore_extensions(project_type)
    all_files = []

    for root, dirs, files in os.walk(repo_path):
        # Compute the relative root path from repo_path
        rel_root = os.path.relpath(root, repo_path)
        # If rel_root is '.', then it means root == repo_path.
        # Remove any directories that match the ignore_spec.
        dirs[:] = [d for d in dirs if not ignore_spec.match_file(os.path.join(rel_root, d))]
        for file in files:
            all_files.append(os.path.join(root, file))
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_file = {}
        for file_path in all_files:
            rel = os.path.relpath(file_path, repo_path)
            if ignore_spec.match_file(rel):
                logger.debug(f"Ignored by gitignore: {rel}")
                continue
            # Check additional ignore patterns from CLI
            skip = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                    logger.debug(f"Ignored by CLI ignore pattern '{pattern}': {rel}")
                    skip = True
                    break
            if skip:
                continue
            if os.path.basename(file_path) in SENSITIVE_FILES:
                logger.debug(f"Ignored sensitive file: {rel}")
                continue
            ext = os.path.splitext(file_path)[1].lower()
            if ext in project_ignore_ext:
                logger.debug(f"Ignored project-specific extension '{ext}': {rel}")
                continue
            if include_extensions and ext not in include_extensions:
                logger.debug(f"Excluded due to include_extensions filter: {rel}")
                continue
            future = executor.submit(get_file_info, file_path, repo_path, project_type, "python", llm_hunt)
            future_to_file[future] = file_path

        for future in as_completed(future_to_file):
            try:
                file_info = future.result()
                repo_files.append(file_info)
                total_files += 1
                total_size += file_info.get("size_bytes", 0)
                rel_dir = os.path.dirname(file_info["relative_path"])
                directory_structure[rel_dir].append(file_info["filename"])
            except Exception as e:
                logger.error(f"Error processing file: {e}")

    return {
        "repository_path": os.path.abspath(repo_path),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "files": repo_files,
        "directory_structure": dict(directory_structure)
    }


def load_cache():
    if os.path.exists(CACHE_FILENAME):
        try:
            with open(CACHE_FILENAME, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

def save_cache(data):
    try:
        with open(CACHE_FILENAME, "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")
