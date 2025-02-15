"""
Module to perform AST analysis using Tree-sitter and generate a basic dependency graph.
Now supports both Python and JavaScript.
Requires: pip install tree_sitter networkx
"""

import sys
import logging
import networkx as nx
from tree_sitter import Language, Parser

logger = logging.getLogger(__name__)

TREE_SITTER_LANGUAGE_PATH = "build/my-languages.so"

try:
    PY_LANGUAGE = Language(TREE_SITTER_LANGUAGE_PATH, "python")
except Exception as e:
    sys.exit(f"Error loading Tree-sitter language library for Python: {e}")

try:
    JS_LANGUAGE = Language(TREE_SITTER_LANGUAGE_PATH, "javascript")
except Exception as e:
    logger.error(f"Error loading Tree-sitter language library for JavaScript: {e}")
    JS_LANGUAGE = None

parser_py = Parser()
parser_py.set_language(PY_LANGUAGE)

if JS_LANGUAGE:
    parser_js = Parser()
    parser_js.set_language(JS_LANGUAGE)
else:
    parser_js = None

def analyze_python_file_treesitter(content, llm_hunt=False):
    """
    Parse Python content using Tree-sitter and extract function and class definitions.
    If llm_hunt is True, include an 'llm_hint' for each node.
    Returns a dictionary with lists of functions and classes.
    """
    try:
        byte_content = content.encode("utf8")
        tree = parser_py.parse(byte_content)
    except Exception as e:
        logger.error(f"Tree-sitter parse error (Python): {e}")
        return {"error": f"Tree-sitter parse error: {e}"}
    
    root_node = tree.root_node
    functions = []
    classes = []

    def traverse(node):
        if node.type == "function_definition":
            for child in node.children:
                if child.type == "identifier":
                    func_name = byte_content[child.start_byte:child.end_byte].decode("utf8")
                    hint = f"Examine the function '{func_name}' to determine its role and business logic."
                    functions.append({
                        "name": func_name,
                        "start_point": node.start_point,
                        "end_point": node.end_point,
                        "llm_hint": hint if llm_hunt else ""
                    })
                    break
        elif node.type == "class_definition":
            for child in node.children:
                if child.type == "identifier":
                    class_name = byte_content[child.start_byte:child.end_byte].decode("utf8")
                    hint = f"Analyze the class '{class_name}' to understand its methods and responsibilities."
                    classes.append({
                        "name": class_name,
                        "start_point": node.start_point,
                        "end_point": node.end_point,
                        "llm_hint": hint if llm_hunt else ""
                    })
                    break
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return {"functions": functions, "classes": classes}

def analyze_javascript_file_treesitter(content, llm_hunt=False):
    """
    Parse JavaScript content using Tree-sitter and extract function and class definitions.
    If llm_hunt is True, include an 'llm_hint' for each node.
    Returns a dictionary with lists of functions and classes.
    """
    if not parser_js:
        return {"error": "JavaScript parser is not available."}
    try:
        byte_content = content.encode("utf8")
        tree = parser_js.parse(byte_content)
    except Exception as e:
        logger.error(f"Tree-sitter parse error (JavaScript): {e}")
        return {"error": f"Tree-sitter parse error: {e}"}
    
    root_node = tree.root_node
    functions = []
    classes = []

    def traverse(node):
        if node.type == "function_declaration":
            for child in node.children:
                if child.type == "identifier":
                    func_name = byte_content[child.start_byte:child.end_byte].decode("utf8")
                    hint = f"Inspect the JavaScript function '{func_name}' to understand its functionality."
                    functions.append({
                        "name": func_name,
                        "start_point": node.start_point,
                        "end_point": node.end_point,
                        "llm_hint": hint if llm_hunt else ""
                    })
                    break
        elif node.type == "class_declaration":
            for child in node.children:
                if child.type == "identifier":
                    class_name = byte_content[child.start_byte:child.end_byte].decode("utf8")
                    hint = f"Examine the JavaScript class '{class_name}' for its properties and methods."
                    classes.append({
                        "name": class_name,
                        "start_point": node.start_point,
                        "end_point": node.end_point,
                        "llm_hint": hint if llm_hunt else ""
                    })
                    break
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return {"functions": functions, "classes": classes}

def generate_dependency_graph(functions):
    """
    Stub function to generate a dependency graph.
    For demonstration, we create a graph where each function is a node.
    In a full implementation, you would analyze function bodies for calls.
    """
    graph = nx.DiGraph()
    for func in functions:
        graph.add_node(func["name"], start=func["start_point"], end=func["end_point"])
    # Placeholder: edges can be added by analyzing function calls.
    return nx.node_link_data(graph, edges="links")  # Explicitly set edges to suppress FutureWarning.


def analyze_file(content, language="python", llm_hunt=False):
    """
    Dispatch AST analysis based on language.
    Supports "python" and "javascript".
    """
    if language.lower() == "python":
        analysis = analyze_python_file_treesitter(content, llm_hunt=llm_hunt)
        if "functions" in analysis:
            dependency_graph = generate_dependency_graph(analysis["functions"])
            analysis["dependency_graph"] = dependency_graph
        return analysis
    elif language.lower() == "javascript":
        analysis = analyze_javascript_file_treesitter(content, llm_hunt=llm_hunt)
        if "functions" in analysis:
            dependency_graph = generate_dependency_graph(analysis["functions"])
            analysis["dependency_graph"] = dependency_graph
        return analysis
    else:
        return {"error": f"AST analysis for language '{language}' is not supported yet."}
