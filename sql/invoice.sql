SELECT
    accountId AS account,
    month,
    id AS invoice,
    amount
FROM
    invoice
WHERE
    year = 2024
    AND month > 2
ORDER BY
    account,
    month,
    amount,
    invoice