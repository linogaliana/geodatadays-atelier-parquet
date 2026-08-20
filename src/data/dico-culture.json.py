import duckdb

con = duckdb.connect()

con.sql(
    """
    COPY (
        SELECT
            code_culture,
            nom_culture,
            num_chapitre,
            nom_chapitre,
            categorie_surf_agricole,
            categorie_ecoregime
        FROM read_xlsx('./code_culture_2026.xlsx')
        ORDER BY num_chapitre, code_culture
    ) TO '/dev/stdout' (FORMAT json, ARRAY true)
    """
)
