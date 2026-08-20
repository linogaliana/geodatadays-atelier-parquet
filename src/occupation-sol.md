---
title: Occupation du sol
toc: true
---

# 🗺️ Occupation du sol (OCS 2D) — Pas-de-Calais 2024

Exploration de la couche d'occupation du sol à deux dimensions (OCS 2D, millésime 2024) : **981 272 polygones** couvrant l'intégralité du département (bâti, cultures, forêts, eau, réseaux…), pas seulement les parcelles agricoles du RPG. Même principe de représentation que le [dashboard RPG](./side) : agrégats calculés avec DuckDB, exploration par commune.

<div class="note" label="Codes bruts, sans dictionnaire officiel vérifié">

Contrairement au RPG (dictionnaire <code>code_culture_2026.xlsx</code>), aucune correspondance officielle fiable n'a été trouvée pour les codes <code>cs24</code> (couverture du sol) et <code>us24</code> (usage du sol) exacts de ce jeu de données — la nomenclature OCS GE publique de l'IGN ne va que jusqu'à <code>CS1</code>/<code>CS2</code>, alors que ces données vont jusqu'à <code>CS6</code>. Les codes sont donc affichés **bruts**, regroupés par leur préfixe de premier niveau (<code>CS1</code> à <code>CS6</code>) pour la couleur.

</div>

```js
const statsCs = FileAttachment("data/stats-cs.json").json();
const statsCommuneOcs = FileAttachment("data/stats-commune-ocs.json").json();
```

```js
// Fixed 6-slot categorical palette (first 6 of the validated 8-slot set),
// assigned in rank order by department-wide surface, reused everywhere.
const PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"];
const csTopTotals = d3.sort(
  d3.rollups(statsCs, (v) => d3.sum(v, (d) => d.surface_ha), (d) => d.cs_top),
  (d) => -d[1]
);
const csTopOrder = csTopTotals.map((d) => d[0]);
const csTopColor = d3.scaleOrdinal(csTopOrder, PALETTE);
```

```js
const totalSurface = d3.sum(statsCs, (d) => d.surface_ha);
const totalPolygones = d3.sum(statsCs, (d) => d.n_polygones);
```

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Polygones</h2>
    <span class="big">${totalPolygones.toLocaleString("fr-FR")}</span>
  </div>
  <div class="card">
    <h2>Surface couverte</h2>
    <span class="big">${Math.round(totalSurface).toLocaleString("fr-FR")} ha</span>
  </div>
  <div class="card">
    <h2>Communes</h2>
    <span class="big">${statsCommuneOcs.length.toLocaleString("fr-FR")}</span>
  </div>
  <div class="card">
    <h2>Codes cs24 distincts</h2>
    <span class="big">${statsCs.length.toLocaleString("fr-FR")}</span>
  </div>
</div>

## Composition par grand type de couverture (CS1 – CS6)

```js
const csTopAgg = csTopOrder.map((cs_top) => {
  const rows = statsCs.filter((d) => d.cs_top === cs_top);
  return {
    cs_top,
    surface_ha: d3.sum(rows, (d) => d.surface_ha),
    n_polygones: d3.sum(rows, (d) => d.n_polygones)
  };
});
```

```js
function csTopBar(data, {width} = {}) {
  return Plot.plot({
    width,
    height: 260,
    marginLeft: 80,
    x: {label: "Surface (ha)", grid: true, tickFormat: (d) => d.toLocaleString("fr-FR")},
    y: {label: null, domain: csTopOrder},
    color: {domain: csTopOrder, range: PALETTE},
    marks: [
      Plot.barX(data, {
        y: "cs_top",
        x: "surface_ha",
        fill: "cs_top",
        sort: {y: null},
        tip: true,
        title: (d) => `${d.cs_top}\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_polygones.toLocaleString("fr-FR")} polygones`
      }),
      Plot.text(data, {
        y: "cs_top",
        x: "surface_ha",
        text: (d) => Math.round(d.surface_ha).toLocaleString("fr-FR"),
        dx: 6,
        textAnchor: "start",
        fill: "var(--theme-foreground)"
      }),
      Plot.ruleX([0])
    ]
  });
}
```

<div class="grid grid-cols-1">
  <div class="card">${resize((width) => csTopBar(csTopAgg, {width}))}</div>
</div>

## Codes détaillés au sein d'un groupe

```js
const csTopSel = view(Inputs.select(csTopOrder, {label: "Groupe (premier niveau)", value: csTopOrder[0]}));
```

```js
const codesInGroup = d3.sort(
  statsCs.filter((d) => d.cs_top === csTopSel),
  (d) => -d.surface_ha
).slice(0, 15);
```

```js
function codeBar(data, {width} = {}) {
  return Plot.plot({
    title: `Codes cs24 principaux — ${csTopSel}`,
    width,
    height: 340,
    marginLeft: 90,
    x: {label: "Surface (ha)", grid: true, tickFormat: (d) => d.toLocaleString("fr-FR")},
    y: {label: null},
    marks: [
      Plot.barX(data, {
        y: "code",
        x: "surface_ha",
        fill: PALETTE[0],
        sort: {y: "-x"},
        tip: true,
        title: (d) => `${d.code}\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_polygones.toLocaleString("fr-FR")} polygones`
      }),
      Plot.text(data, {
        y: "code",
        x: "surface_ha",
        text: (d) => Math.round(d.surface_ha).toLocaleString("fr-FR"),
        dx: 6,
        textAnchor: "start",
        fill: "var(--theme-foreground)"
      }),
      Plot.ruleX([0])
    ]
  });
}
```

<div class="grid grid-cols-1">
  <div class="card">${resize((width) => codeBar(codesInGroup, {width}))}</div>
</div>

## Vue d'ensemble par commune

Taille = surface totale ; couleur = diversité des codes cs24 présents.

```js
const latMean = d3.mean(statsCommuneOcs, (d) => d.lat);
const kx = Math.cos((latMean * Math.PI) / 180);
```

```js
function communeMap(data, {width} = {}) {
  return Plot.plot({
    width,
    height: 560,
    aspectRatio: 1,
    x: {axis: null},
    y: {axis: null},
    r: {range: [1.5, 16]},
    color: {type: "sequential", scheme: "blues", label: "Codes cs24 distincts", legend: true},
    marks: [
      Plot.dot(data, {
        x: (d) => d.lon * kx,
        y: "lat",
        r: "surface_ha",
        fill: "n_codes",
        stroke: "white",
        strokeWidth: 0.5,
        tip: true,
        title: (d) => `${d.commune}\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_polygones.toLocaleString("fr-FR")} polygones\n${d.n_codes} codes cs24 distincts\nDominant : ${d.cs_top_dominant}`
      })
    ]
  });
}
```

<div class="grid grid-cols-1">
  <div class="card">${resize((width) => communeMap(statsCommuneOcs, {width}))}</div>
</div>

## Explorer les polygones d'une commune

```js
const communesByName = new Map(statsCommuneOcs.map((d) => [d.commune, d]));
const communeNames = d3.sort(statsCommuneOcs.map((d) => d.commune), d3.ascending);
const communeSel = view(Inputs.select(communeNames, {label: "Commune", value: "Arras"}));
```

```js
import {communeFiles} from "./data/communes-ocs/index.js";
import maplibregl from "npm:maplibre-gl@5";
```

```js
const communeMeta = communesByName.get(communeSel);
const polysGeo = await communeFiles[communeMeta.slug].json();
```

```js
function csTopOf(code) {
  return code.match(/^CS[0-9]+/)?.[0] ?? code;
}
const fillColorExpr = ["match", ["slice", ["get", "k"], 0, 3], ...csTopOrder.flatMap((t) => [t, csTopColor(t)]), "#999999"];
```

```js
const ocsMapDiv = display(document.createElement("div"));
ocsMapDiv.style.height = "520px";
ocsMapDiv.style.borderRadius = "8px";

const ocsMap = new maplibregl.Map({
  container: ocsMapDiv,
  style: {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "&copy; OpenStreetMap contributors"
      }
    },
    layers: [{id: "osm", type: "raster", source: "osm"}]
  },
  center: [d3.mean(statsCommuneOcs, (d) => d.lon), d3.mean(statsCommuneOcs, (d) => d.lat)],
  zoom: 9
});
ocsMap.addControl(new maplibregl.NavigationControl());

let ocsMapReady;
const ocsMapLoaded = new Promise((resolve) => (ocsMapReady = resolve));
ocsMap.on("load", () => {
  ocsMap.addSource("polys", {type: "geojson", data: {type: "FeatureCollection", features: []}});
  ocsMap.addLayer({id: "polys-fill", type: "fill", source: "polys", paint: {"fill-color": fillColorExpr, "fill-opacity": 0.7}});
  ocsMap.addLayer({id: "polys-line", type: "line", source: "polys", paint: {"line-color": "#20201d", "line-width": 0.2, "line-opacity": 0.4}});

  const popup = new maplibregl.Popup({closeButton: false});
  ocsMap.on("mousemove", "polys-fill", (e) => {
    ocsMap.getCanvas().style.cursor = "pointer";
    const f = e.features[0];
    popup.setLngLat(e.lngLat).setHTML(`<strong>${f.properties.k}</strong> (usage ${f.properties.u})<br>${f.properties.s} ha`).addTo(ocsMap);
  });
  ocsMap.on("mouseleave", "polys-fill", () => {
    ocsMap.getCanvas().style.cursor = "";
    popup.remove();
  });

  ocsMapReady();
});
```

```js
function geometryBounds(geometry, bounds) {
  // Polygon coordinates nest as [ring][point][lng, lat]; MultiPolygon adds
  // one more level. Recurse until we hit a [number, number] pair.
  if (typeof geometry[0] === "number") {
    bounds.extend(geometry);
  } else {
    for (const child of geometry) geometryBounds(child, bounds);
  }
}
```

```js
await ocsMapLoaded;
ocsMap.getSource("polys").setData(polysGeo);
if (polysGeo.features.length) {
  const bounds = new maplibregl.LngLatBounds();
  for (const f of polysGeo.features) geometryBounds(f.geometry.coordinates, bounds);
  ocsMap.fitBounds(bounds, {padding: 16, maxZoom: 15, animate: false});
}
```

<div class="grid grid-cols-1">
  <div class="card">${ocsMapDiv}</div>
</div>

```js
function csLegend() {
  const div = document.createElement("div");
  div.style.cssText = "display:flex;flex-wrap:wrap;gap:0.75rem 1.5rem;font-size:0.85em;";
  for (const cs_top of csTopOrder) {
    const item = document.createElement("span");
    item.style.cssText = "display:inline-flex;align-items:center;gap:0.4em;";
    const swatch = document.createElement("span");
    swatch.style.cssText = `display:inline-block;width:0.85em;height:0.85em;border-radius:2px;background:${csTopColor(cs_top)};border:1px solid var(--theme-foreground-muted);`;
    item.append(swatch, cs_top);
    div.append(item);
  }
  return div;
}
```

<div class="grid grid-cols-1">
  <div class="card">${csLegend()}</div>
</div>

```js
const polyRows = d3.sort(
  polysGeo.features.map((f) => ({
    cs24: f.properties.k,
    us24: f.properties.u,
    surface_ha: f.properties.s
  })),
  (d) => -d.surface_ha
);
```

<div class="grid grid-cols-1">
  <div class="card">
    <h2>${polyRows.length.toLocaleString("fr-FR")} polygones — ${communeSel}</h2>
    ${Inputs.table(polyRows, {
      columns: ["cs24", "us24", "surface_ha"],
      header: {cs24: "Couverture (cs24)", us24: "Usage (us24)", surface_ha: "Surface (ha)"},
      width: {cs24: 130, us24: 130, surface_ha: 110},
      sort: "surface_ha",
      reverse: true
    })}
  </div>
</div>

---

## Méthodologie

Source : fichier Parquet public `ocs2d_2024_62_multidates_comm_v11.parquet` (OCS 2D, millésimes 2005/2015/2021/2024 — seul le millésime 2024 est utilisé ici : champs `cs24` et `us24`), lu et transformé avec DuckDB + `spatial`, selon le même principe que le RPG :

- `src/data/stats-cs.json.py` — surfaces et effectifs agrégés par code `cs24` (département).
- `src/data/stats-commune-ocs.json.py` — agrégats par commune (centroïde, diversité, groupe dominant).
- `scripts/generate_commune_ocs.py` — géométries découpées en un fichier par commune (887 fichiers, ~245 Mo au total plutôt qu'un GeoJSON unique) — exécuté avant `build`/`dev`.

La carte par commune utilise **MapLibre GL** (WebGL) plutôt que Leaflet : certaines communes (Calais, Liévin, Lens…) comptent plus de 8 000 polygones, ce que WebGL encaisse nettement mieux qu'un rendu SVG.
