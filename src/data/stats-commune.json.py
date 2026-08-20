import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")

con.sql(
    f"""
    COPY (
        WITH r AS (
            SELECT
                nom_officiel,
                code_insee_du_departement,
                code_cultu,
                area,
                bbox
            FROM read_parquet('{RPG_URL}')
        ),
        joined AS (
            SELECT
                r.*,
                COALESCE(d.nom_chapitre, 'Non classé') AS nom_chapitre
            FROM r
            LEFT JOIN read_xlsx('./code_culture_2026.xlsx') d ON r.code_cultu = d.code_culture
        ),
        chapitre_dominant AS (
            SELECT
                nom_officiel,
                nom_chapitre,
                SUM(area) AS surface_chapitre,
                ROW_NUMBER() OVER (PARTITION BY nom_officiel ORDER BY SUM(area) DESC) AS rk
            FROM joined
            GROUP BY nom_officiel, nom_chapitre
        )
        SELECT
            j.nom_officiel AS commune,
            trim(regexp_replace(lower(strip_accents(j.nom_officiel)), '[^a-z0-9]+', '-', 'g'), '-') AS slug,
            j.code_insee_du_departement AS departement,
            COUNT(*) AS n_parcelles,
            SUM(j.area) / 10000 AS surface_ha,
            COUNT(DISTINCT j.code_cultu) AS n_cultures,
            cd.nom_chapitre AS chapitre_dominant,
            ST_X(
                ST_Transform(
                    ST_Point((AVG(j.bbox.xmin) + AVG(j.bbox.xmax)) / 2, (AVG(j.bbox.ymin) + AVG(j.bbox.ymax)) / 2),
                    'EPSG:2154', 'EPSG:4326', true
                )
            ) AS lon,
            ST_Y(
                ST_Transform(
                    ST_Point((AVG(j.bbox.xmin) + AVG(j.bbox.xmax)) / 2, (AVG(j.bbox.ymin) + AVG(j.bbox.ymax)) / 2),
                    'EPSG:2154', 'EPSG:4326', true
                )
            ) AS lat
        FROM joined j
        JOIN chapitre_dominant cd ON cd.nom_officiel = j.nom_officiel AND cd.rk = 1
        GROUP BY j.nom_officiel, j.code_insee_du_departement, cd.nom_chapitre
        ORDER BY j.nom_officiel
    ) TO '/dev/stdout' (FORMAT json, ARRAY true)
    """
)
