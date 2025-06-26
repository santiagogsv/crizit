-- Compare invoice_line and invoice_line_vr to find discrepancies
WITH
  il_grouped AS (
    SELECT
      invoiceId AS invoice,
      lower(trim(description)) AS description,
      sum(quantity) AS quantity_il
    FROM invoice_line
    GROUP BY
      invoiceId,
      description
  ),
  il_vr_grouped AS (
    SELECT
      invoiceId AS invoice,
      lower(trim(description)) AS description,
      sum(quantity) AS quantity_vr
    FROM invoice_line_vr
    GROUP BY
      invoiceId,
      description
  ),
  merged AS (
    SELECT
      coalesce(il.invoice, il_vr.invoice) AS invoice,
      coalesce(il.description, il_vr.description) AS description,
      coalesce(il.quantity_il, 0) AS quantity_il,
      coalesce(il_vr.quantity_vr, 0) AS quantity_vr
    FROM il_grouped AS il
    FULL OUTER JOIN
      il_vr_grouped AS il_vr
      ON il.invoice = il_vr.invoice AND il.description = il_vr.description
  )
SELECT
  invoice,
  description,
  quantity_il,
  quantity_vr
FROM merged
WHERE
  quantity_il <> quantity_vr;
