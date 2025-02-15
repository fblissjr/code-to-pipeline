"""
Module to generate a formatted textual tree structure from the scanned repository.
Inspired by the backend features from cyclotruc-gitingest.
"""

def create_tree_structure(directory_structure: dict[str, list[str]], base_path: str) -> str:
    """
    Generate a tree-like string representation of the directory structure.

    Parameters
    ----------
    directory_structure : dict[str, list[str]]
        A dictionary mapping relative directory paths to a list of file names in that directory.
    base_path : str
        The base path of the repository.

    Returns
    -------
    str
        A formatted string representing the directory tree.
    """
    tree_lines = []

    # The directory_structure keys are relative directory paths.
    # For top-level, we expect "" (empty string) as key or direct file list.
    # We sort the keys for a consistent output.
    for dir_path in sorted(directory_structure.keys()):
        # Create a tree line for the directory
        if dir_path == ".":
            tree_lines.append(f"{base_path}")
        else:
            tree_lines.append(dir_path)
        # Now list the files inside the directory
        for filename in sorted(directory_structure[dir_path]):
            tree_lines.append("├── " + filename)
        tree_lines.append("")  # add an empty line between directories

    return "\n".join(tree_lines)
