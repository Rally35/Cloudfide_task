# Sales Pipeline & Virtual Column Engine

This repository provides:
1. `solution.py`: The `add_virtual_column` function that dynamically computes and attaches calculated columns to pandas DataFrames based on mathematical expressions.
2. `pipeline.py`: An end-to-end data processing pipeline that cleans raw sales transaction data (`sales.csv`), computes line-item revenue via `add_virtual_column`, and aggregates total revenue by region into `revenue_by_region.csv`.
3. Unit and integration test suites (`test_virtual_column.py`, `test_solution.py`, `test_pipeline.py`).

---

## 1. Setup and Usage

### Prerequisites
- Python 3.9+
- `pip`

### Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Rally35/Cloudfide_task.git
cd Cloudfide_task
pip install -r requirements.txt
```

### Running the Pipeline
To clean `sales.csv`, compute line revenues, and generate `revenue_by_region.csv`:
```bash
python pipeline.py
```
This generates `revenue_by_region.csv` in the root directory.

### Running the Tests
All unit and integration tests run with a single command:
```bash
pytest
```
To run with detailed test execution output:
```bash
pytest -v
```

---

## 2. Assumptions

Where specifications left implementation details open, the following assumptions were made:

1. **DataFrame Immutability**:
   `add_virtual_column` returns a new DataFrame copy rather than mutating the input DataFrame in place.

2. **Column Label Validation**:
   - Column labels (both existing DataFrame columns and the `new_column` target) must consist strictly of letters (`a-z`, `A-Z`) and underscores (`_`).
   - If any column label in `df`, the `new_column` name, or column identifiers referenced in `role` contains digits, spaces, or special characters, or if columns are duplicated or missing, an empty DataFrame (`pd.DataFrame()`) is returned.

3. **Role Expression Constraints**:
   - The expression string supports basic arithmetic: addition (`+`), subtraction (`-`), and multiplication (`*`), including operator precedence (`*` evaluated before `+`/`-`) and parentheses `(...)`.
   - The expression operands must strictly be column identifiers. Hardcoded numeric constants (e.g. `col + 10`), unsupported operators (e.g. `/`, `**`, `%`), and malformed syntax return an empty DataFrame.

4. **Negative Quantities as Returns/Refunds**:
   - Quantities with negative values (e.g. `-2`, `-4`) represent customer returns or order cancellations in retail/sales systems.
   - Retaining negative quantities correctly decreases net revenue for the corresponding region (`revenue = quantity * unit_price - discount`).
   - This assumption is confirmed by the file's own `TOTAL` row, where the total quantity of `37150` exactly matches the algebraic sum when negative quantities are preserved.

5. **Deduplication of Identical Order Records**:
   - `sales.csv` contains consecutive identical rows sharing the same unique `Order ID`. Because `Order ID` is a unique transaction identifier, identical rows represent duplicate export artifacts and are deduplicated using `drop_duplicates(keep="first")`.

6. **Imputation of Missing Unit Prices**:
   - Inspection of the dataset confirms that unit prices are fixed per product across the catalog (e.g., *Headset* is always 119.00, *Printer paper* is always 21.00). Missing prices are imputed using this deterministic mapping rather than dropping rows.

7. **Imputation of Missing Discounts**:
   - As per task specifications, an empty discount denotes that no discount was applied. Missing values are filled with `0.0`.

8. **Output Schema and Precision**:
   - `revenue_by_region.csv` contains columns `region` and `revenue`, sorted alphabetically by region and rounded to two decimal places (cents).

---

## 3. Data Quality Issues in `sales.csv`

The raw dataset contains 1,507 lines. The table below details all identified issues, the number of affected rows, and how each issue was handled:

| Problem | Affected Rows | Description & Examples | Handling in Code |
| :--- | :---: | :--- | :--- |
| **Non-standard Column Headers** | All columns (7) | Column names contained spaces (`Order ID`, `Unit Price`, `Order Date`) and trailing whitespace (`Quantity `). | Headers were stripped, lowercased, and converted to snake_case (`order_id`, `region`, `product`, `quantity`, `unit_price`, `discount`, `order_date`) to meet `add_virtual_column` requirements. |
| **Repeated Header Row** | **1 row** (index 751) | A duplicate CSV header (`Order ID,Region,Product,Quantity ,Unit Price,Discount,Order Date`) appeared in the middle of the dataset (line 752). | Filtered out by matching rows where `order_id` equals `"order id"`. Cannot be converted into an order line. |
| **Summary / Total Row** | **1 row** (index 1506) | A footer row (`TOTAL, NaN, NaN, 37150, NaN, 65924.67, NaN`) summarizing batch exports was present at the end of the file. | Filtered out by matching `order_id == "total"`. As an aggregate row lacking line item data, it must not be processed as an order line. |
| **Exact Duplicate Orders** | **5 rows** (indices 305, 824, 969, 1244, 1410) | 5 order lines appeared twice consecutively with identical values across all columns (`SO-10305`, `SO-10822`, `SO-10966`, `SO-11240`, `SO-11405`). | Deduplicated using `drop_duplicates(keep="first")`, retaining the original order lines and removing redundant duplicates. |
| **Region Formatting (Whitespace)** | **8 rows** | Leading or trailing whitespace in region values (e.g., `'west  '`, `'Central '`, `' North'`, `' South'`). | Stripped whitespace via `str.strip()`. |
| **Region Formatting (Casing)** | **7 rows** | Non-standard casing in region names (e.g., `'EAST'`, `'south'`, `'north'`, `'central'`). | Standardized to title case via `str.capitalize()`, resulting in five uniform regions: Central, East, North, South, and West. |
| **European Decimal Comma in Unit Price** | **7 rows** | Unit prices formatted with a comma instead of a period (e.g., `'59,00'`, `'39,90'`, `'249,00'`). | Replaced commas with periods (`str.replace(",", ".")`) and cast to `float`. |
| **Missing Unit Price** | **4 rows** (indices 610, 1102, 1354, 1482) | Orders with empty/NaN unit prices (`SO-10610`, `SO-11099`, `SO-11350`, `SO-11477`). | Imputed the known catalog price based on `product` (`Printer paper` -> 21.00, `Keyboard` -> 89.00), preserving all transaction rows. |
| **Thousand Separators in Quantity** | **4 rows** (indices 250, 734, 1091, 1316) | Quantities formatted with spaces as thousand separators (e.g., `'1 762'`, `'1 745'`, `'1 371'`, `'1 427'`). | Stripped spaces (`str.replace(" ", "")`) and converted to numeric integers. |
| **Negative Quantities** | **6 rows** (indices 421, 515, 780, 1014, 1293, 1450) | Quantities entered with negative numbers (`-2`, `-4`, `-5`, `-3`, `-3`, `-2`). | Preserved as negative numbers to reflect returns/credits, consistent with accounting practices and matching the file's `TOTAL` control sum. |
| **Missing Discount Values** | **963 rows** | Empty cells where no discount was granted on the line item. | Filled missing discount values with `0.0` as per specification, enabling arithmetic evaluation. |

---

## 4. Pipeline Results

Aggregated revenue by region produced by `pipeline.py`:

| Region | Total Revenue |
| :--- | :---: |
| **Central** | 515,824.67 |
| **East** | 442,219.91 |
| **North** | 665,897.52 |
| **South** | 504,036.04 |
| **West** | 442,268.89 |
| **Total** | **2,570,247.03** |
