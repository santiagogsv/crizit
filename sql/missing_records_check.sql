-- missing_records_check.sql
-- Finds missing records by joining uploads with a complete index.
-- Parameters: ? (file_type), ? (required_count)

SELECT
  ci.account,
  ci.month,
  COALESCE(counts.record_count, 0) AS found_count
FROM complete_index_temp AS ci
LEFT JOIN (
  SELECT
    accountId AS account,
    month,
    COUNT(*) AS record_count
  FROM uploads
  WHERE type_file = ?
  GROUP BY
    account,
    month
) AS counts
ON ci.account = counts.account AND ci.month = counts.month
WHERE COALESCE(counts.record_count, 0) < ?;
