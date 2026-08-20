WITH geo_agg AS (
    SELECT COUNT(*) AS n, {var_geo}
    FROM read_parquet('{chemin}')
    WHERE {var_geo} IS NOT NULL
    GROUP BY {var_geo}
)

SELECT
    {var_geo},
    n,
    100 * n / SUM(n) OVER () AS proportion
FROM geo_agg
ORDER BY n DESC