import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"

con = duckdb.connect()

con.sql(
    f"""
    COPY (
        WITH agg AS (
            SELECT
                r.code_cultu,
                COALESCE(d.nom_culture, r.code_cultu) AS nom_culture,
                COALESCE(d.num_chapitre, '0') AS num_chapitre,
                COALESCE(d.nom_chapitre, 'Non classé') AS nom_chapitre,
                COALESCE(d.categorie_surf_agricole, 'NC') AS categorie_surf_agricole,
                COUNT(*) AS n_parcelles,
                SUM(r.area) / 10000 AS surface_ha
            FROM read_parquet('{RPG_URL}') r
            LEFT JOIN read_xlsx('./code_culture_2026.xlsx') d ON r.code_cultu = d.code_culture
            GROUP BY 1, 2, 3, 4, 5
        )
        SELECT
            code_cultu,
            nom_culture,
            num_chapitre,
            nom_chapitre,
            categorie_surf_agricole,
            n_parcelles,
            surface_ha,
            surface_ha / SUM(surface_ha) OVER () AS part_surface
        FROM agg
        ORDER BY surface_ha DESC
    ) TO '/dev/stdout' (FORMAT json, ARRAY true)
    """
)
