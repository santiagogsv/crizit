
-- missing_uploads_check.sql
-- Finds missing invoice and verification report uploads for each account and month.

WITH months(month) AS (
    VALUES (3), (4), (5), (6), (7), (8), (9), (10), (11), (12)
),
accounts AS (
    SELECT id AS account FROM account WHERE isActive = 1
),
complete_index AS (
    SELECT
        a.account,
        m.month
    FROM accounts a
    CROSS JOIN months m
)
SELECT
  ci.account,
  ci.month,
  COALESCE(counts.invoice_count, 0) AS found_invoices,
  COALESCE(counts.vr_count, 0) AS found_vrs
FROM complete_index AS ci
LEFT JOIN (
  SELECT
    accountId AS account,
    month,
    COUNT(CASE WHEN type_file = 'invoice' THEN 1 END) AS invoice_count,
    COUNT(CASE WHEN type_file = 'verification_report' THEN 1 END) AS vr_count
  FROM uploads
  WHERE year = 2024 AND month > 2
  GROUP BY
    account,
    month
) AS counts
ON ci.account = counts.account AND ci.month = counts.month
WHERE
  COALESCE(counts.invoice_count, 0) < 1 OR COALESCE(counts.vr_count, 0) < 2;
