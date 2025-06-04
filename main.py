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
    counts = df.groupby(group_cols).size().reset_index(name="count")
    complete_df = (
        counts.set_index(group_cols).reindex(complete_index, fill_value=0).reset_index()
    )
    missing = complete_df[complete_df["count"] < required_count].copy()
    missing["error"] = f"Missing in {df_label}"
    if not missing.empty:
        missing_table = missing.to_markdown(index=False)
        return f"### Discrepancies in {df_label}\n\n{missing_table}\n\n"
    else:
        return f"### Discrepancies in {df_label}\n\nNo missing records found.\n\n"


def check_discrepancies(
    invoice_line: pd.DataFrame, invoice_line_vr: pd.DataFrame
) -> dict:
    """
    Check for discrepancies between invoice_line and invoice_line_vr,
    returning a dictionary with markdown content and discrepancy count for each invoice with discrepancies.
    """
    inv_line = invoice_line.copy()
    inv_line_vr = invoice_line_vr.copy()
    inv_line["description"] = inv_line["description"].str.strip().str.lower()
    inv_line_vr["description"] = inv_line_vr["description"].str.strip().str.lower()
    all_invoices = set(inv_line["invoice"].unique()) | set(
        inv_line_vr["invoice"].unique()
    )
    discrepancy_details = {}

    for invoice in all_invoices:
        il_subset = inv_line[inv_line["invoice"] == invoice]
        il_vr_subset = inv_line_vr[inv_line_vr["invoice"] == invoice]
        il_grouped = il_subset.groupby("description")["quantity"].sum().reset_index()
        il_vr_grouped = (
            il_vr_subset.groupby("description")["quantity"].sum().reset_index()
        )
        merged = pd.merge(
            il_grouped,
            il_vr_grouped,
            on="description",
            how="outer",
            suffixes=("_il", "_vr"),
        ).fillna(0)

        missing_in_vr = merged[merged["quantity_vr"] == 0][
            ["description", "quantity_il"]
        ]
        extra_in_vr = merged[merged["quantity_il"] == 0][["description", "quantity_vr"]]
        quantity_mismatch = merged[
            (merged["quantity_il"] != 0)
            & (merged["quantity_vr"] != 0)
            & (merged["quantity_il"] != merged["quantity_vr"])
        ][["description", "quantity_il", "quantity_vr"]]

        # Calculate total discrepancies (number of unique descriptions with issues)
        discrepancy_count = (
            len(missing_in_vr) + len(extra_in_vr) + len(quantity_mismatch)
        )

        # Only include invoices with discrepancies
        if discrepancy_count > 0:
            content = f"# Discrepancies for Invoice: {invoice}\n\n"
            if not missing_in_vr.empty:
                missing_table = missing_in_vr.to_markdown(index=False)
                content += f"## Missing in invoice_line_vr\n\n{missing_table}\n\n"
            if not extra_in_vr.empty:
                extra_table = extra_in_vr.to_markdown(index=False)
                content += f"## Extra in invoice_line_vr\n\n{extra_table}\n\n"
            if not quantity_mismatch.empty:
                mismatch_table = quantity_mismatch.to_markdown(index=False)
                content += f"## Quantity mismatches\n\n{mismatch_table}\n\n"
            discrepancy_details[invoice] = (content, discrepancy_count)

    return discrepancy_details


def sanitize_filename(name):
    """
    Convert an invoice ID to a safe filename by replacing non-alphanumeric characters
    (except underscores and hyphens) with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_-]", "_", str(name))


def main() -> None:
    # Connect to database and load data
    con = duckdb.connect("test.db")
    account = con.sql(read_sql("sql/account.sql")).df()
    invoice_line = con.sql(read_sql("sql/invoice_line.sql")).df()
    invoice_line_vr = con.sql(read_sql("sql/invoice_line_vr.sql")).df()
    uploads = con.sql(read_sql("sql/uploads.sql")).df()
    con.close()

    # Prepare complete index for missing records check
    months = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    complete_index = pd.MultiIndex.from_product(
        [account["account"], months], names=["account", "month"]
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
    discrepancy_details = check_discrepancies(invoice_line, invoice_line_vr)

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
