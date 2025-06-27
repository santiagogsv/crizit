-- Compare invoice_line and invoice_line_vr to find discrepancies
WITH combined AS (
    SELECT
        invoiceId as invoice,
        lower(trim(description)) as description,
        quantity as quantity_il,
        0 as quantity_vr
    FROM invoice_line
    UNION ALL
    SELECT
        invoiceId as invoice,
        lower(trim(description)) as description,
        0 as quantity_il,
        quantity as quantity_vr
    FROM invoice_line_vr
),
grouped as (
    SELECT
        invoice,
        description,
        sum(quantity_il) as quantity_il,
        sum(quantity_vr) as quantity_vr
    FROM combined
    GROUP BY invoice, description
)
SELECT
    invoice,
    description,
    quantity_il,
    quantity_vr
FROM grouped
WHERE quantity_il <> quantity_vr
