"""
Module to detect the project type using heuristics based on file presence and structure.
"""

import os

def detect_project_type(repo_path):
    """
    Heuristic to detect project type:
      - If 'requirements.txt', 'setup.py', or 'pyproject.toml' exist -> 'python_backend'
      - If 'package.json' exists -> 'frontend'
      - Otherwise, 'generic'
    """
    files = os.listdir(repo_path)
    if any(f in files for f in ("requirements.txt", "setup.py", "pyproject.toml")):
        return "python_backend"
    if "package.json" in files:
        return "frontend"
    return "generic"
