"""Split the RPG parcels into one small GeoJSON file per commune, for the
Quarto/OJS deck (index.qmd).

DuckDB-wasm's browser-side spatial extension loading is currently broken
with the bundled DuckDBClient (see the "Explorer par commune" slide in
index.qmd), so the geometry reprojection (Lambert-93 -> WGS84) has to happen
at render/build time instead of live in the browser. This mirrors
scripts/generate_commune_parcels.py (used by the Observable Framework site
in src/), but writes to data/communes/ at the project root, which is what
the Quarto deck fetches from at runtime (see index.qmd's `resources:` entry
and the `slugify`/`fetch` calls in the "Explorer par commune" slide).

Run manually before `quarto render` / `quarto preview` if the source data
changes: python3 scripts/generate_quarto_commune_data.py
"""

import json
import re
import unicodedata
from pathlib import Path

import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "communes"

# Tolerance for polygon simplification (meters, in the source Lambert-93 CRS)
# and coordinate precision after reprojection to WGS84 (degrees, ~1m).
SIMPLIFY_TOLERANCE_M = 10
COORD_PRECISION_DEG = 0.00001


def slugify(name):
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "commune"


def main():
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    con.sql("SET geometry_always_xy = true;")

    rows = con.sql(
        f"""
        SELECT
            nom_officiel AS commune,
            code_cultu AS k,
            ROUND(area / 10000, 3) AS s,
            ST_AsGeoJSON(
                ST_ReducePrecision(
                    ST_MakeValid(
                        ST_Transform(
                            ST_MakeValid(ST_SimplifyPreserveTopology(geom, {SIMPLIFY_TOLERANCE_M})),
                            'EPSG:2154', 'EPSG:4326', true
                        )
                    ),
                    {COORD_PRECISION_DEG}
                )
            ) AS geom
        FROM read_parquet('{RPG_URL}')
        WHERE geom IS NOT NULL
        ORDER BY nom_officiel
        """
    ).fetchall()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("*.geojson"):
        f.unlink()

    by_commune = {}
    for commune, k, s, geom in rows:
        by_commune.setdefault(commune, []).append((k, s, geom))

    seen_slugs = set()
    slug_by_commune = {}
    for commune, features in by_commune.items():
        slug = slugify(commune)
        if slug in seen_slugs:
            raise RuntimeError(f"slug collision for commune {commune!r} -> {slug!r}")
        seen_slugs.add(slug)
        slug_by_commune[commune] = slug

        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"k": k, "s": s},
                    "geometry": json.loads(geom),
                }
                for k, s, geom in features
            ],
        }
        (OUT_DIR / f"{slug}.geojson").write_text(
            json.dumps(fc, separators=(",", ":"), ensure_ascii=False)
        )

    # Single source of truth for the name -> slug mapping, so the JS side
    # doesn't need to reimplement slugify() and risk drifting from it.
    (OUT_DIR / "index.json").write_text(
        json.dumps(slug_by_commune, separators=(",", ":"), ensure_ascii=False)
    )

    print(f"wrote {len(by_commune)} commune files + index.json to {OUT_DIR}")


if __name__ == "__main__":
    main()
