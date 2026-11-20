import pandas as pd
from solution import add_virtual_column

PRODUCT_PRICES = {
    "Desk lamp": 39.90,
    "Headset": 119.00,
    "Keyboard": 89.00,
    "Monitor stand": 59.00,
    "Mouse": 29.50,
    "Notebook pack": 12.50,
    "Office chair": 249.00,
    "Printer paper": 21.00,
}


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw sales DataFrame:
    - Standardize column names to valid lowercase snake_case (letters and underscores only).
    - Remove non-transactional rows (redundant header rows and summary TOTAL rows).
    - Normalize region names (strip whitespace and apply standard capitalization).
    - Format unit prices (replace decimal commas with dots and impute missing values from product catalog).
    - Format quantities (remove space thousand separators and convert to numeric, preserving return signs).
    - Format discounts (fill missing values with 0.0 as per specification).
    - Remove exact duplicate order lines.
    """
    cleaned = df.copy()

    # 1. Standardize column names
    cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]

    # 2. Filter out non-data rows (repeated header and summary TOTAL rows)
    is_header_row = cleaned["order_id"].astype(str).str.strip().str.lower() == "order id"
    is_total_row = cleaned["order_id"].astype(str).str.strip().str.lower() == "total"
    is_null_order = cleaned["order_id"].isna()
    cleaned = cleaned[~(is_header_row | is_total_row | is_null_order)].copy()

    # 3. Clean region: strip whitespace and title-case
    cleaned["region"] = cleaned["region"].astype(str).str.strip().str.capitalize()

    # 4. Clean unit price: replace comma with dot, convert to float, fill missing from catalog
    cleaned["unit_price"] = (
        cleaned["unit_price"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .replace({"nan": None, "None": None})
    )
    cleaned["unit_price"] = pd.to_numeric(cleaned["unit_price"], errors="coerce")
    cleaned["unit_price"] = cleaned["unit_price"].fillna(cleaned["product"].map(PRODUCT_PRICES))

    # 5. Clean quantity: remove space separators and convert to integer
    cleaned["quantity"] = cleaned["quantity"].astype(str).str.replace(" ", "", regex=False)
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="raise").astype(int)

    # 6. Clean discount: fill missing with 0.0 and convert to float
    cleaned["discount"] = pd.to_numeric(cleaned["discount"], errors="coerce").fillna(0.0)

    # 7. Deduplicate identical order records
    cleaned = cleaned.drop_duplicates(keep="first").reset_index(drop=True)

    return cleaned


def run_pipeline(
    input_path: str = "sales.csv",
    output_path: str = "revenue_by_region.csv",
) -> pd.DataFrame:
    """
    Execute the end-to-end sales pipeline:
    1. Read raw sales CSV.
    2. Clean the sales data.
    3. Add virtual column 'revenue' = quantity * unit_price - discount.
    4. Aggregate total revenue by region and save to CSV.
    """
    raw_df = pd.read_csv(input_path)
    cleaned_df = clean_sales_data(raw_df)

    # Calculate virtual column 'revenue'
    df_with_revenue = add_virtual_column(
        cleaned_df,
        "quantity * unit_price - discount",
        "revenue",
    )

    if df_with_revenue.empty:
        raise ValueError("Failed to calculate revenue virtual column.")

    # Calculate total revenue by region
    revenue_by_region = (
        df_with_revenue.groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("region")
        .reset_index(drop=True)
    )
    revenue_by_region["revenue"] = revenue_by_region["revenue"].round(2)

    # Write output CSV
    revenue_by_region.to_csv(output_path, index=False)
    return revenue_by_region


if __name__ == "__main__":
    result = run_pipeline()
    print("Pipeline executed successfully. Revenue by region:")
    print(result)
