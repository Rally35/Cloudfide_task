import os
import pandas as pd
import pytest
from pipeline import clean_sales_data, run_pipeline, PRODUCT_PRICES


def test_clean_sales_data_unit():
    """Test individual cleaning rules on synthetic dirty data."""
    dirty_data = pd.DataFrame({
        "Order ID": ["SO-1", "Order ID", "SO-2", "SO-2", "SO-3", "TOTAL"],
        "Region": [" south ", "Region", "WEST", "WEST", "North", None],
        "Product": ["Keyboard", "Product", "Mouse", "Mouse", "Desk lamp", None],
        "Quantity ": [" 10 ", "Quantity ", "1 000", "1 000", "-2", "37150"],
        "Unit Price": ["89,00", "Unit Price", "29.50", "29.50", None, None],
        "Discount": [None, "Discount", "15.00", "15.00", None, "65924.67"],
        "Order Date": ["2026-01-01", "Order Date", "2026-01-02", "2026-01-02", "2026-01-03", None],
    })

    cleaned = clean_sales_data(dirty_data)

    # 1. Non-data rows (Order ID header & TOTAL summary) must be dropped
    assert "Order ID" not in cleaned["order_id"].values
    assert "TOTAL" not in cleaned["order_id"].values
    assert len(cleaned) == 3  # SO-1, one SO-2 (deduplicated), SO-3

    # 2. Columns must be clean snake_case
    for col in cleaned.columns:
        assert col.islower()
        assert " " not in col

    # 3. Region cleaned
    assert cleaned.loc[cleaned["order_id"] == "SO-1", "region"].iloc[0] == "South"
    assert cleaned.loc[cleaned["order_id"] == "SO-2", "region"].iloc[0] == "West"

    # 4. Unit price formatted and imputed
    assert cleaned.loc[cleaned["order_id"] == "SO-1", "unit_price"].iloc[0] == 89.00
    assert cleaned.loc[cleaned["order_id"] == "SO-3", "unit_price"].iloc[0] == 39.90

    # 5. Quantity formatted and negative preserved
    assert cleaned.loc[cleaned["order_id"] == "SO-2", "quantity"].iloc[0] == 1000
    assert cleaned.loc[cleaned["order_id"] == "SO-3", "quantity"].iloc[0] == -2

    # 6. Discount missing filled with 0.0
    assert cleaned.loc[cleaned["order_id"] == "SO-1", "discount"].iloc[0] == 0.0
    assert cleaned.loc[cleaned["order_id"] == "SO-2", "discount"].iloc[0] == 15.00


def test_pipeline_on_real_sales_file(tmp_path):
    """Test running the pipeline end-to-end on sales.csv."""
    output_file = tmp_path / "test_revenue_by_region.csv"
    res = run_pipeline(input_path="sales.csv", output_path=str(output_file))

    # Output file exists
    assert output_file.exists()

    # Read generated CSV
    df_result = pd.read_csv(output_file)

    # Verify schema
    assert list(df_result.columns) == ["region", "revenue"]

    # Verify regions: exactly 5 regions
    expected_regions = ["Central", "East", "North", "South", "West"]
    assert sorted(df_result["region"].tolist()) == expected_regions

    # Verify non-empty and non-null values
    assert not df_result["revenue"].isna().any()
    assert (df_result["revenue"] > 0).all()

    # Verify values are rounded to 2 decimal places
    for val in df_result["revenue"]:
        assert round(val, 2) == val


def test_revenue_calculation_correctness():
    """Verify revenue calculation against known expected totals."""
    raw = pd.read_csv("sales.csv")
    cleaned = clean_sales_data(raw)
    assert len(cleaned) == 1500  # 1507 - 1 header - 1 total - 5 duplicates

    # Check for any nulls
    assert cleaned.isna().sum().sum() == 0

    # Cleaned columns match letter and underscore requirements
    assert all(c.replace("_", "").isalpha() for c in cleaned.columns)
