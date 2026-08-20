import duckdb

OCS_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/ocs2d_2024_62_multidates_comm_v11.parquet"

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")

con.sql(
    f"""
    COPY (
        WITH r AS (
            SELECT
                nom_officiel,
                regexp_extract(cs24, '^(CS[0-9]+)') AS cs_top,
                cs24,
                area,
                bbox
            FROM read_parquet('{OCS_URL}')
        ),
        top_dominant AS (
            SELECT
                nom_officiel,
                cs_top,
                SUM(area) AS surface_top,
                ROW_NUMBER() OVER (PARTITION BY nom_officiel ORDER BY SUM(area) DESC) AS rk
            FROM r
            GROUP BY nom_officiel, cs_top
        )
        SELECT
            r.nom_officiel AS commune,
            trim(regexp_replace(lower(strip_accents(r.nom_officiel)), '[^a-z0-9]+', '-', 'g'), '-') AS slug,
            COUNT(*) AS n_polygones,
            SUM(r.area) / 10000 AS surface_ha,
            COUNT(DISTINCT r.cs24) AS n_codes,
            td.cs_top AS cs_top_dominant,
            ST_X(
                ST_Transform(
                    ST_Point((AVG(r.bbox.xmin) + AVG(r.bbox.xmax)) / 2, (AVG(r.bbox.ymin) + AVG(r.bbox.ymax)) / 2),
                    'EPSG:2154', 'EPSG:4326', true
                )
            ) AS lon,
            ST_Y(
                ST_Transform(
                    ST_Point((AVG(r.bbox.xmin) + AVG(r.bbox.xmax)) / 2, (AVG(r.bbox.ymin) + AVG(r.bbox.ymax)) / 2),
                    'EPSG:2154', 'EPSG:4326', true
                )
            ) AS lat
        FROM r
        JOIN top_dominant td ON td.nom_officiel = r.nom_officiel AND td.rk = 1
        GROUP BY r.nom_officiel, td.cs_top
        ORDER BY r.nom_officiel
    ) TO '/dev/stdout' (FORMAT json, ARRAY true)
    """
)
