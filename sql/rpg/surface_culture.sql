WITH culture_agg AS (
    SELECT
        SUM(ST_Area({var_geom})) AS surface,
        COUNT(*) AS nombre,
        {var_culture}
    FROM read_parquet('{chemin}')
    WHERE {var_culture} IS NOT NULL
    GROUP BY {var_culture}
)

SELECT
    {var_culture},
    surface,
    surface / SUM(surface) OVER () AS proportion_surface,
    nombre,
    nombre / SUM(nombre) OVER () AS proportion_nombre,
FROM culture_agg
ORDER BY surface DESC