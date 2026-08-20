"""Department-wide stats by raw "couverture du sol" (cs24) code.

Unlike the RPG culture codes, there is no verified official dictionary for
these OCS codes available to this project, so the site displays the raw
codes as-is (see the methodology note on the occupation-sol page) rather
than invented labels.
"""

import duckdb

OCS_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/ocs2d_2024_62_multidates_comm_v11.parquet"

con = duckdb.connect()

con.sql(
    f"""
    COPY (
        WITH agg AS (
            SELECT
                cs24 AS code,
                regexp_extract(cs24, '^(CS[0-9]+)') AS cs_top,
                COUNT(*) AS n_polygones,
                SUM(area) / 10000 AS surface_ha
            FROM read_parquet('{OCS_URL}')
            GROUP BY 1, 2
        )
        SELECT
            code,
            cs_top,
            n_polygones,
            surface_ha,
            surface_ha / SUM(surface_ha) OVER () AS part_surface
        FROM agg
        ORDER BY surface_ha DESC
    ) TO '/dev/stdout' (FORMAT json, ARRAY true)
    """
)
