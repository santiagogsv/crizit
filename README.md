# Invoice and Verification Reports Validation Script

## Overview
Validates data from a DuckDB database, checking invoices, invoice lines, verification reports, and uploads for discrepancies and missing records.

1. Retrieve data from DuckDB using SQL and Pandas
2. Validates and checks for missing files.
3. Prints results in terminal with details for easy fix.

## Dependencies
- `pandas`
- `duckdb`

Install: `pip install pandas duckdb`
or using uv `uv run main.py`

## File Structure
- **Script**: Main logic for database connection and validation.
  - main.py
- **SQL Files** (`sql/`):
  - `account.sql`
  - `invoice.sql`
  - `invoice_line.sql`
  - `invoice_line_vr.sql`
  - `uploads.sql`

## Database
Uses DuckDB (`test.db` or `test_missing.db`). Switch by commenting/uncommenting.
- test.db is unedited.
- test_missing.db edited for testing error checks.

## Functionality
1. **Invoice Match** (`check_invoice_match`):
   - Compares `amount` in `invoice` vs. `uploads`.
   - Reports mismatches or confirms matches.

2. **Invoice Line** (`check_invoice_line`):
   - Compares sum of `amount` in `invoice_line` vs. `invoice`.
   - Reports discrepancies.

3. **Invoice Line VR** (`check_invoice_line_vr`):
   - Compares line counts per `invoice` in `invoice_line` vs. `invoice_line_vr`.
   - Reports differences.

4. **Missing Invoices** (`check_missing_invoice`):
   - Checks for at least one invoice per `account` and `month` (Mar-Dec).
   - Reports missing invoices.

5. **Missing VR** (`check_missing_vr`):
   - Ensures ≥2 verification reports per `account` and `month`.
   - Reports missing reports.

## Usage
1. Place SQL files in `sql/` and database in script directory.
2. Run: `python main.py` or `uv run main.py`
3. Outputs discrepancies or confirmation for each check on terminal.

## Output
Prints results for each check, listing mismatches or confirming consistency.

```
----- CHECK 'INVOICE' AGAINST 'UPLOADS' TABLE -----
All invoices match between 'uploads' and 'invoice' table.

----- CHECK 'INVOICE_LINE' AGAINST 'INVOICE' TABLE -----
All amounts match between 'invoice' and 'invoice_line' table.

----- CHECK 'INVOICE_LINE_VR' AGAINST 'INVOICE_LINE' TABLE -----
All lines match between 'invoice_line' and 'invoice_line_vr'.

----- CHECK 'INVOICE' UPLOADS -----
Accounts with missing invoices:
    account  month
0         1      3
50       10      3

----- CHECK 'VERIFICATION_REPORT' UPLOADS -----
Accounts with missing verification reports:
    account  month  count
0         1      3      0
10        3      3      0
20        4      3      0
30        6      3      0
40        7      3      0
50       10      3      0
57       10     10      0
```

Output of 'test_missing.db' with lines deleted on 'invoice' and 'invoice_line':
- Deleted invoice 5 and modified invoice 8 to 10,000 on "test_missing.db"
- Deleted one line from invoice 4 with amount 205 on "inovice_line"
- Added a new line for invoice 140 with amount 968 on "invoice_line_vr"

```
----- CHECK 'INVOICE' AGAINST 'UPLOADS' TABLE -----
The following invoices do not match:
    account  month  invoice  amount_inv  amount_upl  variance
10        1      9        8     10000.0     23716.0   13716.0
34        4      9        5         NaN    114568.0       NaN

----- CHECK 'INVOICE_LINE' AGAINST 'INVOICE' TABLE -----
Invoice lines that do not match:
   account  month  invoice         amount    amount_line      variance
0      3.0    9.0        4  114294.382812  114089.093750    205.289062
1      NaN    NaN        5            NaN  114567.500000           NaN
3      1.0    9.0        8   10000.000000   23715.779297  13715.779297

----- CHECK 'INVOICE_LINE_VR' AGAINST 'INVOICE_LINE' TABLE -----
Invoices with different number of lines:
    invoice  count_vr  count  variance
0         4        67     66         1
75      140        65     64         1

----- CHECK 'INVOICE' UPLOADS -----
Accounts with missing invoices:
    account  month
0         1      3
50       10      3

----- CHECK 'VERIFICATION_REPORT' UPLOADS -----
Accounts with missing verification reports:
    account  month  count
0         1      3      0
10        3      3      0
20        4      3      0
30        6      3      0
40        7      3      0
50       10      3      0
57       10     10      0
```

## Limitations
- Hardcoded months, years and database paths.

## Future Improvements
- Add error handling.
- Parameterize months, years and database.
- Export results in markdown/pdf format for easier sharing.