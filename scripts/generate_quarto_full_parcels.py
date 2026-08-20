"""All 162k RPG parcels for the department, in a single GeoJSON file, for
the Quarto/OJS deck's "Affichage et calculs fluides" slide (index.qmd).

Same reasoning as scripts/generate_quarto_commune_data.py: DuckDB-wasm's
browser-side spatial extension loading is currently broken with the bundled
DuckDBClient, so the geometry reprojection (Lambert-93 -> WGS84) happens
once here instead of live in the browser. Mirrors
src/data/parcelles-full.geojson.py (same simplification tolerance), used by
the Observable Framework site's raw-map performance test.

Run manually before `quarto render` / `quarto preview` if the source data
changes: python3 scripts/generate_quarto_full_parcels.py
"""

import json
from pathlib import Path

import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "parcelles-full.geojson"

# Tolerance for polygon simplification (meters, in the source Lambert-93 CRS)
# and coordinate precision after reprojection to WGS84 (degrees, ~1m).
SIMPLIFY_TOLERANCE_M = 10
COORD_PRECISION_DEG = 0.00001


def main():
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    con.sql("SET geometry_always_xy = true;")

    rows = con.sql(
        f"""
        SELECT
            r.code_cultu AS k,
            ROUND(r.area / 10000, 3) AS s,
            ST_AsGeoJSON(
                ST_ReducePrecision(
                    ST_MakeValid(
                        ST_Transform(
                            ST_MakeValid(ST_SimplifyPreserveTopology(r.geom, {SIMPLIFY_TOLERANCE_M})),
                            'EPSG:2154', 'EPSG:4326', true
                        )
                    ),
                    {COORD_PRECISION_DEG}
                )
            ) AS geom
        FROM read_parquet('{RPG_URL}') r
        WHERE r.geom IS NOT NULL
        """
    ).fetchall()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"k": k, "s": s},
                "geometry": json.loads(geom),
            }
            for k, s, geom in rows
        ],
    }
    OUT_PATH.write_text(json.dumps(fc, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {len(rows)} parcels to {OUT_PATH}")


if __name__ == "__main__":
    main()
