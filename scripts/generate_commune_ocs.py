"""Split the OCS (land cover) polygons into one small GeoJSON file per commune.

Same rationale as generate_commune_parcels.py, but for the land-cover
dataset - which has ~6x more polygons (981k vs 162k), so it needs it even
more. Outputs go to src/data/communes-ocs/, which is gitignored.
"""

import json
import re
import unicodedata
from pathlib import Path

import duckdb

OCS_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/ocs2d_2024_62_multidates_comm_v11.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "communes-ocs"

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
            cs24 AS k,
            us24 AS u,
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
        FROM read_parquet('{OCS_URL}')
        WHERE geom IS NOT NULL
        ORDER BY nom_officiel
        """
    ).fetchall()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("*.geojson"):
        f.unlink()

    by_commune = {}
    for commune, k, u, s, geom in rows:
        by_commune.setdefault(commune, []).append((k, u, s, geom))

    seen_slugs = set()
    slugs = []
    for commune, features in by_commune.items():
        slug = slugify(commune)
        if slug in seen_slugs:
            raise RuntimeError(f"slug collision for commune {commune!r} -> {slug!r}")
        seen_slugs.add(slug)
        slugs.append(slug)

        fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"k": k, "u": u, "s": s},
                    "geometry": json.loads(geom),
                }
                for k, u, s, geom in features
            ],
        }
        (OUT_DIR / f"{slug}.geojson").write_text(
            json.dumps(fc, separators=(",", ":"), ensure_ascii=False)
        )

    index_js = "".join(
        f'  "{slug}": FileAttachment("{slug}.geojson"),\n' for slug in sorted(slugs)
    )
    (OUT_DIR / "index.js").write_text(
        'import {FileAttachment} from "observablehq:stdlib";\n\n'
        "export const communeFiles = {\n" + index_js + "};\n"
    )

    print(f"wrote {len(by_commune)} commune files + index.js to {OUT_DIR}")


if __name__ == "__main__":
    main()
