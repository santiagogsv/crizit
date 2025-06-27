import duckdb
import os
import re


def read_sql(file_path) -> str:
    with open(file_path, "r") as file:
        return file.read()


def check_missing_uploads(con: duckdb.DuckDBPyConnection) -> tuple[str, str]:
    """Checks for missing invoice and verification report uploads."""
    query = read_sql("sql/missing_uploads_check.sql")
    missing_results = con.sql(query).fetchall()

    invoice_missing = []
    vr_missing = []

    for row in missing_results:
        if row[2] < 1:
            invoice_missing.append(row)
        if row[3] < 2:
            vr_missing.append(row)

    def format_missing_section(results: list, label: str, headers: list[str]) -> str:
        if not results:
            return f"### No missing records in {label}\n\n"

        header = " | ".join(headers)
        separator = " | ".join(["---"] * len(headers))
        body = "\n".join([" | ".join(map(str, row)) for row in results])
        return f"### Missing in {label}\n\n{header}\n{separator}\n{body}\n\n"

    invoice_missing_str = format_missing_section(
        invoice_missing, "invoice_uploads", ["Account", "Month", "Found Invoices", "Found VRs"]
    )
    vr_missing_str = format_missing_section(
        vr_missing, "vr_uploads", ["Account", "Month", "Found Invoices", "Found VRs"]
    )

    return invoice_missing_str, vr_missing_str



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
    # Connect to database
    con = duckdb.connect("test.db")

    # Check for missing uploads
    invoice_missing, vr_missing = check_missing_uploads(con)

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
