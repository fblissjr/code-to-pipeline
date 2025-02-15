"""
Configuration settings and defaults for the code-to-pipeline project.
"""

import os

# Sensitive files or patterns that should never be included.
SENSITIVE_FILES = {".env", ".env.local", ".env.production"}

# Default ignore list (in addition to .gitignore)
DEFAULT_IGNORE_FILES = {"LICENSE.md", "PRIVACY.md"}

# Default file extensions to include (empty means include all)
DEFAULT_INCLUDE_EXTENSIONS = set()  # e.g., {".py", ".js", ".md"}

# Default project type
DEFAULT_PROJECT_TYPE = "generic"

# Cache file for scanning results (simple pickle cache)
CACHE_FILENAME = os.path.join(os.getcwd(), ".repo_scan_cache.pkl")

# External pipeline configuration file (optional)
PIPELINE_CONFIG_FILE = os.path.join(os.getcwd(), "pipeline_config.yaml")

# Logging configuration
LOG_LEVEL = "INFO"

# For advanced dependency analysis, we plan to use NetworkX.
# (Ensure you install networkx: pip install networkx)
