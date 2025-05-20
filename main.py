import pandas as pd
import duckdb


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

    # print(account)
    # print(invoice)
    # print(invoice_line)
    # print(invoice_line_vr)
    # print(uploads)

    print("--------------------CHECKS--------------------")

    # Check if the "invoice" matches with "uploads", compare the "amount" column, show variance
    # Deleted invoice 5 and modified invoice 8 to 10,000 on "test_missing.db"
    def check_invoice_match() -> None:
        inv = invoice.copy()
        upl = uploads[uploads["file"] == "invoice"].copy()

        # Ensure merge keys are of same type
        for col in ["account", "month", "invoice"]:
            inv[col] = pd.to_numeric(inv[col], errors="coerce")
            upl[col] = pd.to_numeric(upl[col], errors="coerce")

        # Convert "amount" to numeric and round
        inv["amount"] = pd.to_numeric(inv["amount"], errors="coerce").round(0)
        upl["amount"] = pd.to_numeric(upl["amount"], errors="coerce").round(0)

        # Merge on account, month, invoice
        merged = pd.merge(
            inv,
            upl,
            on=["account", "month", "invoice"],
            how="outer",
            suffixes=("_inv", "_upl"),
        )

        # Calculate variance
        merged["variance"] = (merged["amount_inv"] - merged["amount_upl"]).abs()

        # Find mismatches
        mismatches = merged[
            (merged["variance"] > 0.01)
            | (merged["amount_inv"].isna())
            | (merged["amount_upl"].isna())
        ]

        # Print results
        if not mismatches.empty:
            print("The following invoices do not match:")
            print(mismatches)
        else:
            print("All invoices match between uploads and invoice table.")

    check_invoice_match()

    # Sum "amount" from each "invoiceId" on "invoice_line" and compare to "amount" from "invoice" table
    def check_invoice_line() -> None:
        inv_line = invoice_line.copy()
        inv = invoice.copy()

        # Ensure consistent types
        inv_line["invoice"] = pd.to_numeric(inv_line["invoice"], errors="coerce")
        inv["invoice"] = pd.to_numeric(inv["invoice"], errors="coerce")

        inv_line["amount"] = pd.to_numeric(inv_line["amount"], errors="coerce")
        inv["amount"] = pd.to_numeric(inv["amount"], errors="coerce")

        # Sum line items by invoice
        inv_line_grouped = inv_line.groupby("invoice")["amount"].sum().reset_index()
        inv_line_grouped = inv_line_grouped.rename(columns={"amount": "amount_line"})

        # Merge invoice table with grouped invoice_line using OUTER join
        merged = pd.merge(
            inv, inv_line_grouped, on="invoice", how="outer", suffixes=("", "_line")
        )

        # Calculate variance safely
        merged["variance"] = (merged["amount"] - merged["amount_line"]).abs()

        # Show mismatches: amount difference or missing on either side
        mismatches = merged[
            (merged["variance"] > 0.01)
            | (merged["amount"].isna())
            | (merged["amount_line"].isna())
        ]

        # Print results
        print("----------------------------------------------")
        if not mismatches.empty:
            print("Invoice lines that do not match:")
            print(mismatches)
        else:
            print("All invoice lines match with the invoice table.")

    check_invoice_line()

    # Check "invoice_line_vr" against "invoice_line", count number of lines of each invoice
    # Deleted one line from invoice 4 with amount 205 on "inovice_line"
    # Added a new line for invoice 140 with amount 968 on "invoice_line_vr"
    def check_invoice_line_vr() -> None:
        inv_line_vr = invoice_line_vr.copy()
        inv_line = invoice_line.copy()

        # Count number of lines per invoice
        count_vr = inv_line_vr.groupby("invoice").size().reset_index(name="count_vr")
        count = inv_line.groupby("invoice").size().reset_index(name="count")

        # Merge the two counts on invoice
        merged = pd.merge(count_vr, count, on="invoice", how="outer")

        # Fill NaNs (in case an invoice is missing from one of the tables)
        merged = merged.fillna(0)

        # Compare counts
        merged["variance"] = (merged["count_vr"] - merged["count"]).abs()
        mismatches = merged[merged["variance"] > 0]

        # Print results
        print("----------------------------------------------")
        if not mismatches.empty:
            print("Invoices with different number of lines:")
            print(mismatches)
        else:
            print("All invoices have the same number of lines in both tables.")

    check_invoice_line_vr()

    # Check if at least one invoice is uploaded for each account and month
    def check_missing_invoice() -> None:
        # Drop unnecessary columns to keep only relevant data
        check_invoice = uploads[uploads["file"] == "invoice"].drop(
            columns=["file", "vr"]
        )

        # Create a complete index of all possible account-month combinations
        invoice_index = pd.MultiIndex.from_product(
            [account["account"], months], names=["account", "month"]
        )

        # Group the filtered data by account and month, keeping only the first entry per group
        grouped = check_invoice.groupby(["account", "month"]).first().reset_index()

        # Merge the grouped data with the complete index to ensure all combinations are present
        complete_df = (
            grouped.set_index(["account", "month"]).reindex(invoice_index).reset_index()
        )

        # Identify rows where the 'invoice' value is missing
        missing = complete_df[complete_df["invoice"].isna()].drop(
            columns=["invoice", "amount"]
        )

        # Print results
        print("----------------------------------------------")
        if not missing.empty:
            print("Accounts with missing invoices:")
            print(missing)
        else:
            print("No missing invoices.")

    check_missing_invoice()

    # Check if at least two verification reports are uploaded for each account and month
    def check_missing_vr() -> None:
        # Filter for verification reports
        check_vr = uploads[uploads["file"] == "verification_report"].drop(
            columns=["invoice", "file", "amount", "vr"]
        )

        # Create a complete index of all possible combinations of accounts and months
        full_index = pd.MultiIndex.from_product(
            [account["account"], months], names=["account", "month"]
        )

        # Count the number of verification reports per account and month
        vr_counts = (
            check_vr.groupby(["account", "month"]).size().reset_index(name="count")
        )

        # Merge the counts with the full index to ensure all combinations are present
        vr_complete = (
            vr_counts.set_index(["account", "month"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )

        # Check if any account-month pair has less than 2 verification reports
        missing_vr = vr_complete[vr_complete["count"] < 2]

        # Print results
        print("----------------------------------------------")
        if not missing_vr.empty:
            print("Accounts with missing verification reports:")
            print(missing_vr)
        else:
            print("No missing verification reports.")

    check_missing_vr()


if __name__ == "__main__":
    main()
