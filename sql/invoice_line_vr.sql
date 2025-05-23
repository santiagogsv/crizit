SELECT
    accountId AS account,
    month,
    invoiceId AS invoice,
    description,
    quantity,
FROM
    invoice_line_vr
WHERE
    year = 2024
    AND month > 2
ORDER BY
    account,
    month,
    invoice,
    quantity