"""
Default ignore patterns for code-to-pipeline.
This list contains common patterns that should be ignored when scanning a repository,
such as compiled files, virtual environments, and IDE folders.
"""

DEFAULT_IGNORE_PATTERNS = {
    # Python
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "poetry.lock",
    "Pipfile.lock",
    # Node/JavaScript
    "node_modules",
    "bower_components",
    "package-lock.json",
    "yarn.lock",
    ".npm",
    ".yarn",
    ".pnpm-store",
    "bun.lock",
    "bun.lockb",
    # Java
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    "*.nar",
    ".gradle/",
    "build/",
    ".settings/",
    ".classpath",
    # IDEs and editors
    ".idea",
    ".vscode",
    "*.swp",
    "*.swo",
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    # Miscellaneous
    "*.log",
    "*.bak",
    "*.tmp",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Build artifacts
    "dist",
    "target",
    "out",
    "*.egg-info",
    "*.egg",
}
