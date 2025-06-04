# Invoice and Verification Reports Validation Script

## Overview
This script validates data from a DuckDB database, checking invoices, invoice lines, verification reports, and uploads for discrepancies and missing records. It generates detailed markdown reports organized in a structured directory for easy review and sharing. [CLICK TO OPEN RESULTS](results/results.md)


1. Retrieves data from DuckDB using SQL queries and Pandas.
2. Validates uploads and checks for missing records.
3. Identifies discrepancies between invoice lines and verification reports.
4. Outputs results as markdown files in a `results/` directory, with a summary report and individual invoice discrepancy files.

## Dependencies
- `pandas`
- `duckdb`
- `tabulate`

Install using `uv` (recommended): `uv run main.py`  
Or using pip: `pip install pandas duckdb tabulate`

## File Structure
- **Script**: Core logic for database connection, validation, and report generation.
  - `main.py`
- **SQL Files** (`sql/`):
  - `account.sql`
  - `invoice_line.sql`
  - `invoice_line_vr.sql`
  - `uploads.sql`
- **Output** (`results/`):
  - `results.md`: Summary report with links to individual invoice discrepancy files.
  - `discrepancies/`: Directory containing per-invoice discrepancy markdown files (e.g., `discrepancy_inv_4.md`).

## Database
Uses DuckDB (`test.db`). The script connects to the database to retrieve data for validation.

## Functionality
1. **Missing Uploads Check** (`check_missing_records`):
   - Ensures at least one invoice upload per account-month (March to December).
   - Ensures at least two verification report uploads per account-month.
   - Reports account-months with missing uploads in markdown format.

2. **Invoice Line vs. Verification Report Discrepancies** (`check_discrepancies`):
   - Compares quantities by description between `invoice_line` and `invoice_line_vr` for each invoice.
   - Identifies:
     - Descriptions missing in `invoice_line_vr`.
     - Extra descriptions in `invoice_line_vr`.
     - Quantity mismatches between the two tables.
   - Generates detailed markdown reports for each invoice with discrepancies.

3. **Output Organization**:
   - Creates a `results/discrepancies/` directory for individual invoice discrepancy files.
   - Writes a summary `results.md` file with:
     - Missing uploads reports.
     - List of invoices with discrepancies, including links to detailed reports and discrepancy counts.
   - Sanitizes invoice IDs for safe filenames using `sanitize_filename`.

## Usage
1. Place SQL files in `sql/` and the database (`test.db`) in the script directory.
2. Run: `uv run main.py` or `python main.py`
3. Check the `results/` directory for:
   - `results.md`: Summary report with links to detailed discrepancy files.
   - `discrepancies/`: Individual markdown files for each invoice with discrepancies.

## Output
The script generates markdown files for easy sharing and review:

- [CLICK TO OPEN RESULTS](results/results.md)


## Limitations
- Hardcoded months (March to December) and database path (`test.db`).
- Assumes SQL files are correctly formatted and present in `sql/`.