import ast
import re
from typing import Any
import pandas as pd


def _is_valid_column_name(name: Any) -> bool:
    """Validate that a column label consists only of letters and underscores."""
    return isinstance(name, str) and bool(re.fullmatch(r"[a-zA-Z_]+", name))


def _eval_ast(node: ast.AST, df: pd.DataFrame) -> pd.Series:
    """Recursively evaluate an AST expression consisting of +, -, * operations on DataFrame columns."""
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, df)
    elif isinstance(node, ast.BinOp):
        left = _eval_ast(node.left, df)
        right = _eval_ast(node.right, df)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        else:
            raise ValueError(f"Unsupported binary operator: {type(node.op)}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand, df)
        if isinstance(node.op, ast.UAdd):
            return +operand
        elif isinstance(node.op, ast.USub):
            return -operand
        else:
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    elif isinstance(node, ast.Name):
        if not _is_valid_column_name(node.id) or node.id not in df.columns:
            raise ValueError(f"Invalid or missing column: {node.id}")
        return df[node.id]
    else:
        raise ValueError(f"Unsupported node type: {type(node)}")


def add_virtual_column(df: pd.DataFrame, role: str, new_column: str) -> pd.DataFrame:
    """
    Add a virtual column to a pandas DataFrame computed from a mathematical expression.

    Parameters:
    - df: Any pandas DataFrame.
    - role: A mathematical expression defining how to compute values (e.g., 'col_a - col_b').
    - new_column: Name of the new virtual column to add.

    Returns:
    - A new DataFrame with the added virtual column, or an empty DataFrame if inputs or validations fail.
    """
    # Validate df
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()

    # Validate new_column label
    if not _is_valid_column_name(new_column):
        return pd.DataFrame()

    # Validate all existing column labels in df
    if not all(_is_valid_column_name(col) for col in df.columns):
        return pd.DataFrame()

    # Column labels in df must be unique
    if len(df.columns) != len(set(df.columns)):
        return pd.DataFrame()

    # Validate role string
    if not isinstance(role, str) or not role.strip():
        return pd.DataFrame()

    # Role characters must only be letters, underscores, basic operators (+, -, *), parentheses, and whitespace
    if not re.fullmatch(r"[a-zA-Z_\s\+\-\*\(\)]+", role):
        return pd.DataFrame()

    # Parse expression AST
    try:
        tree = ast.parse(role.strip(), mode="eval")
    except Exception:
        return pd.DataFrame()

    # Ensure tree has at least one column identifier
    has_name = any(isinstance(n, ast.Name) for n in ast.walk(tree))
    if not has_name:
        return pd.DataFrame()

    # Evaluate the expression
    try:
        result_series = _eval_ast(tree, df)
        result_df = df.copy()
        result_df[new_column] = result_series
        return result_df
    except Exception:
        return pd.DataFrame()
