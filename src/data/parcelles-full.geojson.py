"""All 162k RPG parcels for the department, in a single GeoJSON file.

Used only by the home page's raw MapLibre performance test (no commune
filter, no join) - see src/index.md. The per-commune / dashboard view
(src/side.md) uses scripts/generate_commune_parcels.py instead, which is
far lighter since it only ever loads one commune at a time.
"""

import sys
import tempfile
from pathlib import Path

import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"

# Tolerance for polygon simplification (meters, in the source Lambert-93 CRS)
# and coordinate precision after reprojection to WGS84 (degrees, ~1m).
SIMPLIFY_TOLERANCE_M = 10
COORD_PRECISION_DEG = 0.00001

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
con.sql("SET geometry_always_xy = true;")

with tempfile.TemporaryDirectory() as tmp:
    out_path = Path(tmp) / "parcelles-full.geojson"
    con.sql(
        f"""
        COPY (
            SELECT
                r.code_cultu AS k,
                ROUND(r.area / 10000, 3) AS s,
                ST_ReducePrecision(
                    ST_MakeValid(
                        ST_Transform(
                            ST_MakeValid(ST_SimplifyPreserveTopology(r.geom, {SIMPLIFY_TOLERANCE_M})),
                            'EPSG:2154', 'EPSG:4326', true
                        )
                    ),
                    {COORD_PRECISION_DEG}
                ) AS geom
            FROM read_parquet('{RPG_URL}') r
            WHERE r.geom IS NOT NULL
        ) TO '{out_path}' (FORMAT GDAL, DRIVER 'GeoJSON')
        """
    )
    sys.stdout.buffer.write(out_path.read_bytes())
