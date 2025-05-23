import pandas as pd
import duckdb
import numpy as np


def read_sql(file_path) -> str:
    with open(file_path, "r") as file:
        return file.read()


def main() -> None:
    # Connect to DuckDB database
    con = duckdb.connect(
        "test.db"
    )  # Comment to connect to the test_missing.db database
    # con = duckdb.connect(
    #     "test_missing.db"
    # )  # Uncomment to connect to the test_missing.db database

    # Read SQL files and load data into DataFrames
    account = con.sql(read_sql("sql/account.sql")).df()
    invoice = con.sql(read_sql("sql/invoice.sql")).df()
    invoice_line = con.sql(read_sql("sql/invoice_line.sql")).df()
    invoice_line_vr = con.sql(read_sql("sql/invoice_line_vr.sql")).df()
    uploads = con.sql(read_sql("sql/uploads.sql")).df()

    # Close the connection
    con.close()

    months = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    BOLD = "\033[1m"
    RESET = "\033[0m"

    # print(account)
    # print(invoice)
    # print(invoice_line)
    # print(invoice_line_vr)
    # print(uploads)

    # Check if at least one invoice is uploaded for each account and month
    def check_missing_invoice() -> None:
        # Filter for invoice uploads and drop irrelevant columns
        check_invoice = uploads[uploads["file"] == "invoice"].drop(
            columns=["file", "vr"]
        )

        # Create a complete index of all possible account-month combinations
        invoice_index = pd.MultiIndex.from_product(
            [account["account"], months], names=["account", "month"]
        )

        # Count invoices per account-month combination
        invoice_counts = (
            check_invoice.groupby(["account", "month"]).size().reset_index(name="count")
        )

        # Merge with complete index to identify missing combinations (count = 0)
        complete_df = (
            invoice_counts.set_index(["account", "month"])
            .reindex(invoice_index, fill_value=0)
            .reset_index()
        )

        # Identify account-months with no invoices
        missing = complete_df[complete_df["count"] == 0].copy()
        missing["error"] = "Missing invoice"

        # Print results
        print(f"\n{BOLD}========== CHECK 'INVOICE' UPLOADS =========={RESET}\n")
        if not missing.empty:
            print("Account-Months with Missing Invoices (Less than 1):\n")
            print(missing[["account", "month", "error"]].to_string(index=False))
        else:
            print("No missing invoices.")

    check_missing_invoice()

    # Check if at least two verification reports are uploaded for each account and month
    def check_missing_vr() -> None:
        # Filter for verification report uploads and drop irrelevant columns
        check_vr = uploads[uploads["file"] == "verification_report"].drop(
            columns=["invoice", "file", "amount", "vr"]
        )

        # Create a complete index of all possible account-month combinations
        full_index = pd.MultiIndex.from_product(
            [account["account"], months], names=["account", "month"]
        )

        # Count verification reports per account-month
        vr_counts = (
            check_vr.groupby(["account", "month"]).size().reset_index(name="count")
        )

        # Merge with complete index to identify missing VRs (count < 2)
        vr_complete = (
            vr_counts.set_index(["account", "month"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )

        # Identify account-months with fewer than 2 verification reports
        missing_vr = vr_complete[vr_complete["count"] < 2].copy()
        missing_vr["error"] = np.where(
            missing_vr["count"] == 0,
            "No verification reports",
            "Insufficient verification reports",
        )

        # Print results
        print(
            f"\n{BOLD}========== CHECK 'VERIFICATION_REPORT' UPLOADS =========={RESET}\n"
        )
        if not missing_vr.empty:
            print("Account-Months with Missing Verification Reports:\n")
            print(
                missing_vr[["account", "month", "count", "error"]].to_string(
                    index=False
                )
            )
        else:
            print("No missing verification reports.")

    check_missing_vr()

    # Check if the "invoice" matches with "uploads", compare the "amount" column, show variance
    # Deleted invoice 5 and modified invoice 8 to 10,000 on "test_missing.db"
    def check_invoice_match() -> None:
        inv = invoice.copy()
        upl = uploads[uploads["file"] == "invoice"].copy()

        # Ensure numeric types for merging
        for col in ["account", "month", "invoice"]:
            inv[col] = pd.to_numeric(inv[col], errors="coerce")
            upl[col] = pd.to_numeric(upl[col], errors="coerce")
        inv["amount"] = pd.to_numeric(inv["amount"], errors="coerce")
        upl["amount"] = pd.to_numeric(upl["amount"], errors="coerce")

        # Merge tables
        merged = pd.merge(
            inv,
            upl,
            on=["account", "month", "invoice"],
            how="outer",
            suffixes=("_inv", "_upl"),
        )
        merged["variance"] = (merged["amount_inv"] - merged["amount_upl"]).abs()

        # Add descriptive column for discrepancy type
        merged["error"] = np.where(
            merged["amount_inv"].isna(),
            "Missing in 'invoice' table",
            np.where(
                merged["amount_upl"].isna(),
                "Missing in 'uploads' table",
                np.where(merged["variance"] > 0.01, "Variance in amount", "Match"),
            ),
        )

        # Filter discrepancies
        mismatches = merged[merged["error"] != "Match"].drop(
            columns=["file", "vr"], errors="ignore"
        )

        # Print results with enhanced output
        print(
            f"\n{BOLD}========== CHECK 'INVOICE' AGAINST 'UPLOADS' TABLE =========={RESET}\n"
        )
        if not mismatches.empty:
            print("The following invoices have discrepancies:\n")
            print(
                mismatches[
                    [
                        "account",
                        "month",
                        "invoice",
                        "amount_inv",
                        "amount_upl",
                        "variance",
                        "error",
                    ]
                ].to_string(index=False, float_format="{:.2f}".format)
            )
        else:
            print("All invoices match between 'uploads' and 'invoice' table.")

    check_invoice_match()

    # Sum "amount" from each "invoice" on "invoice_line" and compare to "amount" from "invoice" table
    def check_invoice_line() -> None:
        inv_line = invoice_line.copy()
        inv = invoice.copy()

        # Ensure consistent numeric types for merging
        inv_line["invoice"] = pd.to_numeric(
            inv_line["invoice"], errors="coerce"
        ).astype("Int64")
        inv["invoice"] = pd.to_numeric(inv["invoice"], errors="coerce").astype("Int64")
        inv["account"] = pd.to_numeric(inv["account"], errors="coerce").astype("Int64")

        # Convert "amount" to numeric for summation and comparison
        inv_line["amount"] = pd.to_numeric(inv_line["amount"], errors="coerce")
        inv["amount"] = pd.to_numeric(inv["amount"], errors="coerce")

        # Sum invoice line amounts by invoice
        inv_line_grouped = inv_line.groupby("invoice")["amount"].sum().reset_index()
        inv_line_grouped = inv_line_grouped.rename(columns={"amount": "amount_line"})

        # Merge invoice and invoice_line tables to compare totals
        merged = pd.merge(inv, inv_line_grouped, on="invoice", how="outer")

        # Calculate absolute variance between totals
        merged["variance"] = (merged["amount"] - merged["amount_line"]).abs()
        merged["error"] = np.where(
            merged["amount"].isna(),
            "Missing in 'invoice' table",
            np.where(
                merged["amount_line"].isna(),
                "Missing in 'invoice_line' table",
                np.where(
                    merged["variance"] > 0.01, "Variance in total amount", "Match"
                ),
            ),
        )

        # Identify mismatches (variance > 0.01 or missing amounts)
        mismatches = merged[merged["error"] != "Match"]

        # Print results
        print(
            f"\n{BOLD}========== CHECK 'INVOICE_LINE' AGAINST 'INVOICE' TABLE =========={RESET}\n"
        )
        if not mismatches.empty:
            print("Invoices with discrepancies in line totals:\n")
            print(
                mismatches[
                    ["invoice", "amount", "amount_line", "variance", "error"]
                ].to_string(index=False, float_format="{:.2f}".format)
            )
        else:
            print("All amounts match between 'invoice' and 'invoice_line' table.")

    check_invoice_line()

    # Check "invoice_line_vr" against "invoice_line", count number of lines of each invoice
    # Deleted one line from invoice 4 with amount 205 on "inovice_line"
    # Added a new line for invoice 140 with amount 968 on "invoice_line_vr"
    def check_invoice_line_vr() -> None:
        inv_line_vr = invoice_line_vr.copy()
        inv_line = invoice_line.copy()

        # Count lines per invoice in both tables
        count_vr = inv_line_vr.groupby("invoice").size().reset_index(name="count_vr")
        count = inv_line.groupby("invoice").size().reset_index(name="count")

        # Merge counts to compare line counts per invoice
        merged = pd.merge(count_vr, count, on="invoice", how="outer")

        # Fill NaNs with 0 for missing invoices in either table
        merged = merged.fillna(0)

        # Calculate absolute variance in line counts
        merged["variance"] = (merged["count_vr"] - merged["count"]).abs()
        merged["error"] = np.where(
            merged["count_vr"] > merged["count"],
            "More lines in VR",
            np.where(
                merged["count_vr"] < merged["count"], "Fewer lines in VR", "Match"
            ),
        )
        mismatches = merged[merged["error"] != "Match"]

        # Print results
        print(
            f"\n{BOLD}========== CHECK 'INVOICE_LINE_VR' AGAINST 'INVOICE_LINE' TABLE =========={RESET}\n"
        )
        if not mismatches.empty:
            print("Invoices with line count discrepancies:\n")
            print(
                mismatches[
                    ["invoice", "count", "count_vr", "variance", "error"]
                ].to_string(index=False)
            )
        else:
            print("All lines match between 'invoice_line' and 'invoice_line_vr'.")

    check_invoice_line_vr()

    def check_invoice_line_vr_quantity(summary_only=False) -> None:
        # Prepare copies of the data
        inv_line_vr = invoice_line_vr.copy()
        inv_line = invoice_line.copy()

        # Ensure numeric types for consistency
        inv_line["invoice"] = pd.to_numeric(
            inv_line["invoice"], errors="coerce"
        ).astype("Int64")
        inv_line_vr["invoice"] = pd.to_numeric(
            inv_line_vr["invoice"], errors="coerce"
        ).astype("Int64")
        inv_line["quantity"] = pd.to_numeric(
            inv_line["quantity"], errors="coerce"
        ).astype("float64")
        inv_line_vr["quantity"] = pd.to_numeric(
            inv_line_vr["quantity"], errors="coerce"
        ).astype("float64")

        # Normalize descriptions for matching
        inv_line["description"] = inv_line["description"].str.strip().str.lower()
        inv_line_vr["description"] = inv_line_vr["description"].str.strip().str.lower()

        # Aggregate quantities by invoice and description
        inv_line_grouped = (
            inv_line.groupby(["invoice", "description"])["quantity"].sum().reset_index()
        )
        inv_line_vr_grouped = (
            inv_line_vr.groupby(["invoice", "description"])["quantity"]
            .sum()
            .reset_index()
        )

        # Merge aggregated tables to find discrepancies
        merged = pd.merge(
            inv_line_grouped,
            inv_line_vr_grouped,
            on=["invoice", "description"],
            how="outer",
            suffixes=("", "_vr"),
        ).fillna({"quantity": 0, "quantity_vr": 0})

        # Calculate variance and categorize errors
        merged["variance"] = (merged["quantity"] - merged["quantity_vr"]).abs()
        merged["error"] = np.where(
            merged["quantity"].isna(),
            "Missing in 'invoice_line'",
            np.where(
                merged["quantity_vr"].isna(),
                "Missing in 'invoice_line_vr'",
                np.where(merged["variance"] > 0, "Quantity mismatch", "Match"),
            ),
        )
        mismatches = merged[merged["error"] != "Match"].copy()

        # Output based on summary_only parameter
        print(
            f"\n{BOLD}========== CHECK 'INVOICE_LINE_VR' QUANTITY AGAINST 'INVOICE_LINE' =========={RESET}\n"
        )
        if summary_only:
            if not mismatches.empty:
                summary = (
                    mismatches.groupby("invoice")
                    .agg(
                        missing_in_inv_line=(
                            "error",
                            lambda x: (x == "Missing in 'invoice_line'").sum(),
                        ),
                        missing_in_inv_line_vr=(
                            "error",
                            lambda x: (x == "Missing in 'invoice_line_vr'").sum(),
                        ),
                        quantity_mismatch=(
                            "error",
                            lambda x: (x == "Quantity mismatch").sum(),
                        ),
                        total_variance=("variance", "sum"),
                    )
                    .reset_index()
                )
                print(
                    "Summary of discrepancies by invoice: (Set 'False' to show full list)\n"
                )
                print(summary.to_string(index=False))
            else:
                print("No discrepancies found.")
        else:
            if not mismatches.empty:
                print("Lines with quantity discrepancies:\n")
                print(
                    mismatches[
                        [
                            "invoice",
                            "description",
                            "quantity",
                            "quantity_vr",
                            "variance",
                            "error",
                        ]
                    ].to_string(index=False)
                )
            else:
                print(
                    "All quantities match between 'invoice_line' and 'invoice_line_vr'."
                )

    check_invoice_line_vr_quantity(summary_only=True)

    def check_missing_extra_lines() -> None:
        inv_line_vr = invoice_line_vr.copy()
        inv_line = invoice_line.copy()

        # Normalize data
        inv_line["invoice"] = pd.to_numeric(
            inv_line["invoice"], errors="coerce"
        ).astype("Int64")
        inv_line_vr["invoice"] = pd.to_numeric(
            inv_line_vr["invoice"], errors="coerce"
        ).astype("Int64")
        inv_line["description"] = inv_line["description"].str.strip().str.lower()
        inv_line_vr["description"] = inv_line_vr["description"].str.strip().str.lower()

        # Merge with indicator
        merged = pd.merge(
            inv_line[["invoice", "description"]],
            inv_line_vr[["invoice", "description"]],
            on=["invoice", "description"],
            how="outer",
            indicator=True,
        )

        # Create a single discrepancies dataframe with status
        discrepancies = merged[merged["_merge"] != "both"].copy()
        discrepancies["error"] = np.where(
            discrepancies["_merge"] == "left_only",
            "Missing in 'invoice_line_vr'",
            "Missing in 'invoice_line'",
        )

        # Print results with enhanced output
        print(
            f"\n{BOLD}========== CHECK MISSING/EXTRA LINES BETWEEN 'INVOICE_LINE' AND 'INVOICE_LINE_VR' =========={RESET}\n"
        )
        if not discrepancies.empty:
            print("Lines with discrepancies:\n")
            print(
                discrepancies[["invoice", "description", "error"]].to_string(
                    index=False
                )
            )
        else:
            print("No missing or extra lines detected.")

    check_missing_extra_lines()

    # This is the most complete check for discrepancies between invoice_line and invoice_line_vr
    def check_discrepancies(limit: int = 3) -> None:
        # Check for discrepancies between invoice_line and invoice_line_vr DataFrames.
        # Uses global invoice_line and invoice_line_vr DataFrames fetched from the database.

        # Copy global DataFrames to avoid modifying originals
        inv_line = invoice_line.copy()
        inv_line_vr = invoice_line_vr.copy()

        # Normalize descriptions
        inv_line["description"] = inv_line["description"].str.strip().str.lower()
        inv_line_vr["description"] = inv_line_vr["description"].str.strip().str.lower()

        # Get all unique invoices
        all_invoices = set(inv_line["invoice"].unique()) | set(
            inv_line_vr["invoice"].unique()
        )

        discrepancies = []
        discrepancy_details = {}

        for invoice in all_invoices:
            # Filter data for the current invoice
            il_subset = inv_line[inv_line["invoice"] == invoice]
            il_vr_subset = inv_line_vr[inv_line_vr["invoice"] == invoice]

            # Group by description and sum quantities
            il_grouped = (
                il_subset.groupby("description")["quantity"].sum().reset_index()
            )
            il_vr_grouped = (
                il_vr_subset.groupby("description")["quantity"].sum().reset_index()
            )

            # Merge dataframes to compare
            merged = pd.merge(
                il_grouped,
                il_vr_grouped,
                on="description",
                how="outer",
                suffixes=("_il", "_vr"),
            ).fillna(0)

            # Identify discrepancies
            missing_in_vr = merged[merged["quantity_vr"] == 0]
            extra_in_vr = merged[merged["quantity_il"] == 0]
            quantity_mismatch = merged[
                (merged["quantity_il"] != 0)
                & (merged["quantity_vr"] != 0)
                & (merged["quantity_il"] != merged["quantity_vr"])
            ]

            # Store results if discrepancies exist
            if not (
                missing_in_vr.empty and extra_in_vr.empty and quantity_mismatch.empty
            ):
                discrepancies.append(invoice)
                discrepancy_details[invoice] = {
                    "missing_in_vr": missing_in_vr[
                        ["description", "quantity_il"]
                    ].to_dict("records"),
                    "extra_in_vr": extra_in_vr[["description", "quantity_vr"]].to_dict(
                        "records"
                    ),
                    "quantity_mismatch": quantity_mismatch[
                        ["description", "quantity_il", "quantity_vr"]
                    ].to_dict("records"),
                }
        print(
            f"\n{BOLD}========== CHECK 'INVOICE_LINE_VR' AND 'INVOICE_LINE' DISCREPANCIES =========={RESET}\n"
        )

        # Output results in table-like structure
        if discrepancies:
            print(
                f"Discrepancies found in {len(discrepancies)} invoices.\nShowing the first {limit} ('limit' parameter default = 3)."
            )
            for inv_id in discrepancies[:limit]:  # Show details for first 3 invoices
                print(f"\nDiscrepancies for Invoice: {inv_id}")
                details = discrepancy_details[inv_id]

                # Collect all unique descriptions for consistent column width
                descriptions = set()
                for item in details["missing_in_vr"]:
                    descriptions.add(item["description"])
                for item in details["extra_in_vr"]:
                    descriptions.add(item["description"])
                for item in details["quantity_mismatch"]:
                    descriptions.add(item["description"])

                # Calculate column widths
                desc_width = (
                    max(len(desc) for desc in descriptions) + 2 if descriptions else 20
                )
                qty_width = 15

                # Section 1: Missing in invoice_line_vr
                if details["missing_in_vr"]:
                    print("\nMissing in invoice_line_vr:")
                    print(
                        f"{'Description':<{desc_width}} {'Quantity (invoice_line)':>{qty_width}}"
                    )
                    print("-" * (desc_width + qty_width))
                    for item in details["missing_in_vr"]:
                        print(
                            f"{item['description']:<{desc_width}} {item['quantity_il']:>{qty_width}}"
                        )

                # Section 2: Extra in invoice_line_vr
                if details["extra_in_vr"]:
                    print("\nExtra in invoice_line_vr:")
                    print(
                        f"{'Description':<{desc_width}} {'Quantity (invoice_line_vr)':>{qty_width}}"
                    )
                    print("-" * (desc_width + qty_width))
                    for item in details["extra_in_vr"]:
                        print(
                            f"{item['description']:<{desc_width}} {item['quantity_vr']:>{qty_width}}"
                        )

                # Section 3: Quantity mismatches
                if details["quantity_mismatch"]:
                    print("\nQuantity mismatches:")
                    print(
                        f"{'Description':<{desc_width}} {'Quantity (invoice_line)':>{qty_width}} {'Quantity (invoice_line_vr)':>{qty_width}}"
                    )
                    print("-" * (desc_width + 2 * qty_width))
                    for item in details["quantity_mismatch"]:
                        print(
                            f"{item['description']:<{desc_width}} {item['quantity_il']:>{qty_width}} {item['quantity_vr']:>{qty_width}}"
                        )
        else:
            print("No discrepancies found. All invoice lines match.")

    check_discrepancies()

    print(f"\n{BOLD}========================================================={RESET}")


if __name__ == "__main__":
    main()
