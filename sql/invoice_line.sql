SELECT
    invoiceId AS invoice,
    lineNumber AS line,
    amount
FROM
    invoice_line
ORDER BY
    invoice,
    line