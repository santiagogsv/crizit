SELECT
    accountId AS account,
    month,
    invoiceId AS invoice,
    type_file AS file,
    type_vr AS vr,
    invoiceCost AS amount
FROM
    uploads
WHERE
    year = 2024
    AND month > 2
ORDER BY
    account,
    month,
    invoice,
    file,
    amount