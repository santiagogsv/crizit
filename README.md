# Invoice and Verification Reports Validation Script

## Overview
Validates data from a DuckDB database, checking invoices, invoice lines, verification reports, and uploads for discrepancies and missing records.

1. Retrieve data from DuckDB using SQL and Pandas
2. Validates and checks for missing files.
3. Prints results in terminal with details for easy fix.

## Dependencies
- `pandas`
- `duckdb`
- `numpy`

Install using 'uv' (recommended): `uv run main.py`
or using pip `pip install pandas duckdb numpy`

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
1. **Missing Invoices** (`check_missing_invoice`):
   - Ensures at least one invoice is uploaded for each account and month (March to December).
   - Reports account-months with missing invoices.

2. **Missing Verification Reports** (`check_missing_vr`):
   - Ensures at least two verification reports are uploaded for each account and month.
   - Reports account-months with insufficient verification reports.

3. **Invoice Match** (`check_invoice_match`):
   - Compares the "amount" in the "invoice" table with the "uploads" table for matching invoices.
   - Reports variances in amounts or missing entries.

4. **Invoice Line Totals** (`check_invoice_line`):
   - Compares the sum of "amount" from "invoice_line" with the "amount" in the "invoice" table for each invoice.
   - Reports discrepancies in totals.

5. **Invoice Line VR Line Counts** (`check_invoice_line_vr`):
   - Compares the number of lines per invoice in "invoice_line" and "invoice_line_vr".
   - Reports invoices with differing line counts.

6. **Invoice Line VR Quantities** (`check_invoice_line_vr_quantity`):
   - Compares the total quantities for each description per invoice between "invoice_line" and "invoice_line_vr".
   - Provides a summary of discrepancies by invoice, with an option to show detailed discrepancies by setting `summary_only=False`.

7. **Missing/Extra Lines** (`check_missing_extra_lines`):
   - Checks for descriptions that are present in "invoice_line" but missing in "invoice_line_vr", and vice versa, for each invoice.
   - Reports missing or extra descriptions per invoice.

## Usage
1. Place SQL files in `sql/` and database in script directory.
2. Run: `uv run main.py` or `python main.py`
3. Outputs discrepancies or confirmation for each check on terminal.

## Output
Prints results for each check, listing mismatches or confirming consistency.

```
========== CHECK 'INVOICE' UPLOADS ==========

Account-Months with Missing Invoices (Less than 1):

 account  month           error
       1      3 Missing invoice
      10      3 Missing invoice

========== CHECK 'VERIFICATION_REPORT' UPLOADS ==========

Account-Months with Missing Verification Reports:

 account  month  count                   error
       1      3      0 No verification reports
       3      3      0 No verification reports
       4      3      0 No verification reports
       6      3      0 No verification reports
       7      3      0 No verification reports
      10      3      0 No verification reports
      10     10      0 No verification reports

========== CHECK 'INVOICE' AGAINST 'UPLOADS' TABLE ==========

All invoices match between 'uploads' and 'invoice' table.

========== CHECK 'INVOICE_LINE' AGAINST 'INVOICE' TABLE ==========

All amounts match between 'invoice' and 'invoice_line' table.

========== CHECK 'INVOICE_LINE_VR' AGAINST 'INVOICE_LINE' TABLE ==========

All lines match between 'invoice_line' and 'invoice_line_vr'.

========== CHECK 'INVOICE_LINE_VR' QUANTITY AGAINST 'INVOICE_LINE' ==========

Summary of discrepancies by invoice: (Set 'False' to show full list)

 invoice  missing_in_inv_line  missing_in_inv_line_vr  quantity_mismatch  total_variance
       4                    0                       0                 33       2528809.0
       5                    0                       0                 31          9009.0
       6                    0                       0                 12         35458.0
       8                    0                       0                 18          1817.0
       9                    0                       0                  2           121.0
      10                    0                       0                  9       1859513.0
      13                    0                       0                 31       2765026.0
      14                    0                       0                 32       3064980.0
      15                    0                       0                 72       3509626.0
      16                    0                       0                 34       2845835.0
      17                    0                       0                 35       2695736.0
      18                    0                       0                 35       3252746.0
      19                    0                       0                 12         36097.0
      20                    0                       0                 12         33030.0
      21                    0                       0                 12         35113.0
      22                    0                       0                 12         35405.0
      23                    0                       0                 12         34380.0
      24                    0                       0                 15        131645.0
      25                    0                       0                  8       1429753.0
      26                    0                       0                  8       1800069.0
      27                    0                       0                 13       1255421.0
      28                    0                       0                  9       1458527.0
      29                    0                       0                  8       1391447.0
      30                    0                       0                 28         14162.0
      31                    0                       0                 23          5513.0
      32                    0                       0                 34         10911.0
      33                    0                       0                 25          9593.0
      34                    0                       0                 65         59220.0
      35                    0                       0                 26         12108.0
      50                    0                       0                  2           118.0
      51                    0                       0                  5            86.0
      52                    0                       0                  2           115.0
      53                    0                       0                 22          1813.0
      54                    0                       0                  2           109.0
      55                    0                       0                  4           212.0
      56                    0                       0                 18          1523.0
      57                    0                       0                 19          1778.0
      58                    0                       0                 16          1925.0
      59                    0                       0                 20          2947.0
      60                    0                       0                  8       1242907.0
      67                    0                       0                 37       2412237.0
      68                    0                       0                 32       2233145.0
      69                    0                       0                 13         34936.0
      70                    0                       0                 12         34276.0
      71                    0                       0                 28          8582.0
      72                    0                       0                 26          8306.0
      73                    0                       0                  8       1005699.0
      74                    0                       0                  8       1399874.0
      75                    0                       0                 22          1855.0
      76                    0                       0                  2           121.0
      77                    0                       0                  2           121.0
      78                    0                       0                 23          2043.0
      79                    0                       0                  2           121.0
      80                    0                       0                 32       3140306.0
      81                    0                       0                 20          1744.0
      82                    0                       0                 12         39013.0
      83                    0                       0                 26          5284.0
      84                    0                       0                  8       2128648.0
     123                    0                       0                 20         39016.0
     124                    0                       0                 45        541348.0
     125                    0                       0                 28         55368.0
     126                    0                       0                 53        582826.0
     127                    0                       0                 17         34351.0
     128                    0                       0                 44        492799.0
     129                    0                       0                 20         35456.0
     130                    0                       0                 30        431143.0
     131                    0                       0                 23         34881.0
     132                    0                       0                 33        462314.0
     133                    0                       0                 11         31254.0
     134                    0                       0                 30        437975.0
     135                    0                       0                 27         32032.0
     136                    0                       0                 62        476228.0
     137                    0                       0                 22         26633.0
     138                    0                       0                 26         34111.0
     139                    0                       0                 34        388695.0
     140                    0                       0                 33        426129.0

========== CHECK MISSING/EXTRA LINES BETWEEN 'INVOICE_LINE' AND 'INVOICE_LINE_VR' ==========

No missing or extra lines detected.

=========================================================
```

Output of 'test_missing.db' with lines deleted on 'invoice' and 'invoice_line':
- Deleted invoice 5 and modified invoice 8 to 10,000 on "test_missing.db"
- Deleted one line from invoice 4 with amount 205 on "inovice_line"
- Added a new line for invoice 140 with amount 968 on "invoice_line_vr"

```
========== CHECK 'INVOICE' UPLOADS ==========

Account-Months with Missing Invoices (Less than 1):

 account  month           error
       1      3 Missing invoice
      10      3 Missing invoice

========== CHECK 'VERIFICATION_REPORT' UPLOADS ==========

Account-Months with Missing Verification Reports:

 account  month  count                   error
       1      3      0 No verification reports
       3      3      0 No verification reports
       4      3      0 No verification reports
       6      3      0 No verification reports
       7      3      0 No verification reports
      10      3      0 No verification reports
      10     10      0 No verification reports

========== CHECK 'INVOICE' AGAINST 'UPLOADS' TABLE ==========

The following invoices have discrepancies:

 account  month  invoice  amount_inv  amount_upl  variance                      error
       1      9        8    10000.00    23715.78  13715.78         Variance in amount
       4      9        5         NaN   114567.50       NaN Missing in 'invoice' table

========== CHECK 'INVOICE_LINE' AGAINST 'INVOICE' TABLE ==========

Invoices with discrepancies in line totals:

 invoice    amount  amount_line  variance                      error
       4 114294.38    114089.09    205.29   Variance in total amount
       5       NaN    114567.50       NaN Missing in 'invoice' table
       8  10000.00     23715.78  13715.78   Variance in total amount

========== CHECK 'INVOICE_LINE_VR' AGAINST 'INVOICE_LINE' TABLE ==========

Invoices with line count discrepancies:

 invoice  count  count_vr  variance            error
       4     66        67         1 More lines in VR
     140     64        65         1 More lines in VR

========== CHECK 'INVOICE_LINE_VR' QUANTITY AGAINST 'INVOICE_LINE' ==========

Summary of discrepancies by invoice: (Set 'False' to show full list)

 invoice  missing_in_inv_line  missing_in_inv_line_vr  quantity_mismatch  total_variance
       4                    0                       0                 34       2547472.0
       5                    0                       0                 31          9009.0
       6                    0                       0                 12         35458.0
       8                    0                       0                 18          1817.0
       9                    0                       0                  2           121.0
      10                    0                       0                  9       1859513.0
      13                    0                       0                 31       2765026.0
      14                    0                       0                 32       3064980.0
      15                    0                       0                 72       3509626.0
      16                    0                       0                 34       2845835.0
      17                    0                       0                 35       2695736.0
      18                    0                       0                 35       3252746.0
      19                    0                       0                 12         36097.0
      20                    0                       0                 12         33030.0
      21                    0                       0                 12         35113.0
      22                    0                       0                 12         35405.0
      23                    0                       0                 12         34380.0
      24                    0                       0                 15        131645.0
      25                    0                       0                  8       1429753.0
      26                    0                       0                  8       1800069.0
      27                    0                       0                 13       1255421.0
      28                    0                       0                  9       1458527.0
      29                    0                       0                  8       1391447.0
      30                    0                       0                 28         14162.0
      31                    0                       0                 23          5513.0
      32                    0                       0                 34         10911.0
      33                    0                       0                 25          9593.0
      34                    0                       0                 65         59220.0
      35                    0                       0                 26         12108.0
      50                    0                       0                  2           118.0
      51                    0                       0                  5            86.0
      52                    0                       0                  2           115.0
      53                    0                       0                 22          1813.0
      54                    0                       0                  2           109.0
      55                    0                       0                  4           212.0
      56                    0                       0                 18          1523.0
      57                    0                       0                 19          1778.0
      58                    0                       0                 16          1925.0
      59                    0                       0                 20          2947.0
      60                    0                       0                  8       1242907.0
      67                    0                       0                 37       2412237.0
      68                    0                       0                 32       2233145.0
      69                    0                       0                 13         34936.0
      70                    0                       0                 12         34276.0
      71                    0                       0                 28          8582.0
      72                    0                       0                 26          8306.0
      73                    0                       0                  8       1005699.0
      74                    0                       0                  8       1399874.0
      75                    0                       0                 22          1855.0
      76                    0                       0                  2           121.0
      77                    0                       0                  2           121.0
      78                    0                       0                 23          2043.0
      79                    0                       0                  2           121.0
      80                    0                       0                 32       3140306.0
      81                    0                       0                 20          1744.0
      82                    0                       0                 12         39013.0
      83                    0                       0                 26          5284.0
      84                    0                       0                  8       2128648.0
     123                    0                       0                 20         39016.0
     124                    0                       0                 45        541348.0
     125                    0                       0                 28         55368.0
     126                    0                       0                 53        582826.0
     127                    0                       0                 17         34351.0
     128                    0                       0                 44        492799.0
     129                    0                       0                 20         35456.0
     130                    0                       0                 30        431143.0
     131                    0                       0                 23         34881.0
     132                    0                       0                 33        462314.0
     133                    0                       0                 11         31254.0
     134                    0                       0                 30        437975.0
     135                    0                       0                 27         32032.0
     136                    0                       0                 62        476228.0
     137                    0                       0                 22         26633.0
     138                    0                       0                 26         34111.0
     139                    0                       0                 34        388695.0
     140                    0                       0                 34        427097.0

========== CHECK MISSING/EXTRA LINES BETWEEN 'INVOICE_LINE' AND 'INVOICE_LINE_VR' ==========

Lines with discrepancies:

 invoice            description                     error
       4 (access) funds pxintra Missing in 'invoice_line'

=========================================================
```

## Limitations
- Hardcoded months, years and database paths.

## Future Improvements
- Add error handling.
- Parameterize months, years and database.
- Export results in markdown/pdf format for easier sharing.