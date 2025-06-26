import pandas as pd
import duckdb
import os
import re


def read_sql(file_path) -> str:
    with open(file_path, "r") as file:
        return file.read()


def check_missing_records(
    df: pd.DataFrame,
    group_cols: list,
    required_count: int,
    complete_index: pd.MultiIndex,
    df_label: str,
) -> str:
    """Checks for missing records using a more performant merge-based approach."""
    complete_df = complete_index.to_frame(index=False)
    counts = df.groupby(group_cols).size().reset_index(name="count")
    merged = pd.merge(complete_df, counts, on=group_cols, how="left").fillna(0)
    missing = merged[merged["count"] < required_count].copy()
    missing["error"] = f"Missing in {df_label}"

    if not missing.empty:
        missing["count"] = missing["count"].astype(int)
        missing_table = missing.to_markdown(index=False)
        return f"### Discrepancies in {df_label}\n\n{missing_table}\n\n"
    else:
        return f"### Discrepancies in {df_label}\n\nNo missing records found.\n\n"


def check_discrepancies(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Check for discrepancies by executing a dedicated SQL query.
    """
    discrepancy_query = read_sql("sql/discrepancy_check.sql")
    discrepancies_df = con.sql(discrepancy_query).df()

    if discrepancies_df.empty:
        return {}

    discrepancy_details = {}
    for invoice, group in discrepancies_df.groupby("invoice"):
        content = [f"# Discrepancies for Invoice: {invoice}\n"]

        missing_in_vr = group[group["quantity_vr"] == 0]
        if not missing_in_vr.empty:
            content.append(
                f"## Missing in invoice_line_vr\n\n{missing_in_vr[['description', 'quantity_il']].to_markdown(index=False)}\n"
            )

        extra_in_vr = group[group["quantity_il"] == 0]
        if not extra_in_vr.empty:
            content.append(
                f"## Extra in invoice_line_vr\n\n{extra_in_vr[['description', 'quantity_vr']].to_markdown(index=False)}\n"
            )

        quantity_mismatch = group[
            (group["quantity_il"] != 0) & (group["quantity_vr"] != 0)
        ]
        if not quantity_mismatch.empty:
            content.append(
                f"## Quantity mismatches\n\n{quantity_mismatch[['description', 'quantity_il', 'quantity_vr']].to_markdown(index=False)}\n"
            )

        discrepancy_details[invoice] = ("\n".join(content), len(group))

    return discrepancy_details



def sanitize_filename(name) -> str:
    """
    Convert an invoice ID to a safe filename by replacing non-alphanumeric characters
    (except underscores and hyphens) with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(name))


def main() -> None:
    # Connect to database and load data
    con = duckdb.connect("test.db")
    account = con.sql(read_sql("sql/account.sql")).df()
    uploads = con.sql(read_sql("sql/uploads.sql")).df()

    # Prepare complete index for missing records check
    months = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    unique_accounts = account["account"].unique().tolist()
    complete_index = pd.MultiIndex.from_product(
        [unique_accounts, months], names=["account", "month"]
    )

    # Check for missing uploads
    invoice_uploads = uploads[uploads["file"] == "invoice"].copy()
    vr_uploads = uploads[uploads["file"] == "verification_report"].copy()
    invoice_missing = check_missing_records(
        invoice_uploads, ["account", "month"], 1, complete_index, "invoice_uploads"
    )
    vr_missing = check_missing_records(
        vr_uploads, ["account", "month"], 2, complete_index, "vr_uploads"
    )

    # Get discrepancy details
    discrepancy_details = check_discrepancies(con)
    con.close()

    # Create discrepancies directory
    discrepancies_dir = os.path.join("results", "discrepancies")
    os.makedirs(discrepancies_dir, exist_ok=True)

    # Write individual discrepancy files
    for invoice, (content, _) in discrepancy_details.items():
        safe_invoice = sanitize_filename(invoice)
        filename = f"discrepancy_inv_{safe_invoice}.md"
        filepath = os.path.join(discrepancies_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)

    # Write main results file with summary and discrepancy counts
    with open("results/results.md", "w") as f:
        f.write("# Detailed Report\n\n")
        f.write("## Upload Checks\n\n")
        f.write(invoice_missing)
        f.write(vr_missing)
        f.write("## Discrepancy Checks\n\n")
        if discrepancy_details:
            f.write(f"Discrepancies found in {len(discrepancy_details)} invoices:\n\n")
            for invoice, (_, count) in discrepancy_details.items():
                safe_invoice = sanitize_filename(invoice)
                f.write(
                    f"- [Invoice {invoice}](discrepancies/discrepancy_inv_{safe_invoice}.md) ({count} found)\n"
                )
        else:
            f.write("No discrepancies found.\n\n")


if __name__ == "__main__":
    main()
