SELECT
    invoiceId AS invoice,
    lineNumber AS line,
    description,
    amount,
    quantity,
FROM
    invoice_line
ORDER BY
    invoice,
    line