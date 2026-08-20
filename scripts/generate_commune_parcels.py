"""Split the RPG parcels into one small GeoJSON file per commune.

A single department-wide GeoJSON (162k parcels) would be tens of MB, most of
it useless on any given page view since the site only ever displays parcels
for one commune at a time. Splitting ahead of time means the browser fetches
one small file (a few dozen KB) per commune selection instead.

This is not an Observable Framework data loader (a loader produces exactly
one output file) - it runs as a "predev"/"prebuild" npm script instead, see
package.json. Outputs go to src/data/communes/, which is gitignored.
"""

import json
import re
import unicodedata
from pathlib import Path

import duckdb

RPG_URL = "https://minio.lab.sspcloud.fr/lgaliana/data/geodata-days/rpg_pac_2024_62_comm_v11.parquet"
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "communes"

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
                    "properties": {"k": k, "s": s},
                    "geometry": json.loads(geom),
                }
                for k, s, geom in features
            ],
        }
        (OUT_DIR / f"{slug}.geojson").write_text(
            json.dumps(fc, separators=(",", ":"), ensure_ascii=False)
        )

    # Observable Framework's FileAttachment() only recognizes calls with a
    # literal string argument (no runtime-computed paths) - so a lookup table
    # of one literal FileAttachment() call per commune is generated here,
    # instead of building the path from the selected slug at runtime.
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
