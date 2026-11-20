import pandas as pd
import pytest
from solution import add_virtual_column


def test_operator_precedence():
    """Verify that multiplication has higher precedence than addition and subtraction."""
    df = pd.DataFrame({
        "qty": [2, 3],
        "price": [10, 20],
        "disc": [5, 10],
    })
    # qty * price - disc = (2*10)-5 = 15; (3*20)-10 = 50
    result = add_virtual_column(df, "qty * price - disc", "revenue")
    expected = pd.DataFrame({
        "qty": [2, 3],
        "price": [10, 20],
        "disc": [5, 10],
        "revenue": [15, 50],
    })
    assert result.equals(expected)


def test_parentheses_in_role():
    """Verify that parentheses are correctly parsed and evaluated."""
    df = pd.DataFrame({
        "a": [2, 3],
        "b": [3, 4],
        "c": [4, 2],
    })
    # (a + b) * c = (2+3)*4 = 20; (3+4)*2 = 14
    result = add_virtual_column(df, "(a + b) * c", "total")
    expected = pd.DataFrame({
        "a": [2, 3],
        "b": [3, 4],
        "c": [4, 2],
        "total": [20, 14],
    })
    assert result.equals(expected)


def test_input_immutability():
    """Verify that add_virtual_column does not mutate the input DataFrame."""
    df = pd.DataFrame({"col_a": [1, 2], "col_b": [3, 4]})
    df_copy = df.copy()
    _ = add_virtual_column(df, "col_a + col_b", "col_c")
    assert df.equals(df_copy)
    assert "col_c" not in df.columns


def test_empty_dataframe_with_columns():
    """Verify behavior on an empty DataFrame with valid column definitions."""
    df = pd.DataFrame(columns=["a", "b"])
    result = add_virtual_column(df, "a + b", "c")
    assert list(result.columns) == ["a", "b", "c"]
    assert len(result) == 0


def test_invalid_new_column_names():
    """Verify that invalid new_column names return an empty DataFrame."""
    df = pd.DataFrame({"a": [1], "b": [2]})
    invalid_names = [
        "col1",       # Contains digit
        "col name",   # Contains space
        "col-name",   # Contains hyphen
        "col.name",   # Contains dot
        "",           # Empty string
        " ",          # Whitespace
        None,         # Non-string
        123,          # Integer
    ]
    for inv in invalid_names:
        result = add_virtual_column(df, "a + b", inv)
        assert result.empty, f"Expected empty df for invalid new_column: {repr(inv)}"


def test_invalid_dataframe_columns():
    """Verify that if DataFrame itself contains invalid column labels, an empty df is returned."""
    df_invalid_num = pd.DataFrame({"a": [1], "b1": [2]})
    assert add_virtual_column(df_invalid_num, "a + a", "res").empty

    df_invalid_space = pd.DataFrame({"a": [1], "col b": [2]})
    assert add_virtual_column(df_invalid_space, "a + a", "res").empty

    df_duplicate = pd.DataFrame([[1, 2]], columns=["a", "a"])
    assert add_virtual_column(df_duplicate, "a + a", "res").empty


def test_invalid_operators_and_constants():
    """Verify that unsupported operators, constants, or malformed expressions return empty df."""
    df = pd.DataFrame({"a": [10, 20], "b": [2, 5]})

    # Division is not supported
    assert add_virtual_column(df, "a / b", "res").empty
    # Exponentiation is not supported
    assert add_virtual_column(df, "a ** b", "res").empty
    # Modulo is not supported
    assert add_virtual_column(df, "a % b", "res").empty
    # Constants / literals in role are not supported
    assert add_virtual_column(df, "a + 5", "res").empty
    # Unclosed parentheses
    assert add_virtual_column(df, "(a + b", "res").empty
    # Trailing operator
    assert add_virtual_column(df, "a +", "res").empty
    # Empty or whitespace role
    assert add_virtual_column(df, "", "res").empty
    assert add_virtual_column(df, "   ", "res").empty
    # Non-string role
    assert add_virtual_column(df, None, "res").empty


def test_non_dataframe_input():
    """Verify that passing non-DataFrame inputs returns an empty DataFrame."""
    assert add_virtual_column(None, "a + b", "res").empty
    assert add_virtual_column({"a": [1]}, "a + a", "res").empty
    assert add_virtual_column([1, 2, 3], "a + a", "res").empty


def test_column_overwrite():
    """Verify that existing column can be overwritten if specified as new_column."""
    df = pd.DataFrame({"a": [2, 4], "b": [10, 20]})
    result = add_virtual_column(df, "a + a", "b")
    expected = pd.DataFrame({"a": [2, 4], "b": [4, 8]})
    assert result.equals(expected)
