SELECT COUNT(*), culture_d2
FROM read_parquet('{chemin}')
GROUP BY culture_d2