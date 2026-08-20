---
title: Carte brute (toutes les parcelles)
toc: false
---

# 🌾 RPG Pas-de-Calais 2024 — carte brute, sans filtre

Test de fluidité : les **162 705 parcelles** du département sont chargées et affichées **d'un bloc**, sans découpage par commune, avec [MapLibre GL](https://maplibre.org/) (rendu WebGL). À comparer avec la version [par commune](./side), qui ne charge et n'affiche que les ~150 parcelles de la commune sélectionnée, avec Leaflet.

```js
import maplibregl from "npm:maplibre-gl@5";
```

```js
const dico = FileAttachment("data/dico-culture.json").json();
const statsCulture = FileAttachment("data/stats-culture.json").json();
```

```js
// Same fixed 8-slot categorical palette / ranking as the commune dashboard,
// so the two pages read consistently.
const PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const chapitreByCode = new Map(dico.map((d) => [d.code_culture, d.nom_chapitre]));
const chapterTotals = d3.sort(
  d3.rollups(statsCulture, (v) => d3.sum(v, (d) => d.surface_ha), (d) => d.nom_chapitre),
  (d) => -d[1]
);
const topChapters = chapterTotals.slice(0, 7).map((d) => d[0]);
const chapterOrder = [...topChapters, "Autres"];
const chapterColor = d3.scaleOrdinal(chapterOrder, PALETTE);

function colorForCode(code) {
  const chapitre = chapitreByCode.get(code);
  return chapterColor(topChapters.includes(chapitre) ? chapitre : "Autres");
}

// A MapLibre "match" expression built once from the ~109 crop codes present,
// so per-feature coloring runs on the GPU instead of per-feature in JS.
const fillColorExpr = ["match", ["get", "k"], ...dico.flatMap((d) => [d.code_culture, colorForCode(d.code_culture)]), "#999999"];
```

```js
const fetchStart = performance.now();
const parcelsGeo = await FileAttachment("data/parcelles-full.geojson").json();
const fetchMs = performance.now() - fetchStart;
```

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Parcelles chargées</h2>
    <span class="big">${parcelsGeo.features.length.toLocaleString("fr-FR")}</span>
  </div>
  <div class="card">
    <h2>Fetch + parse JSON</h2>
    <span class="big">${Math.round(fetchMs).toLocaleString("fr-FR")} ms</span>
  </div>
  <div class="card">
    <h2>Poids du fichier</h2>
    <span class="big">${(FileAttachment("data/parcelles-full.geojson").size / 1e6).toFixed(0)} Mo</span>
  </div>
  <div id="render-kpi" class="card">
    <h2>Premier rendu WebGL</h2>
    <span class="big">…</span>
  </div>
</div>

```js
const mapDiv = display(document.createElement("div"));
mapDiv.style.height = "80vh";
mapDiv.style.borderRadius = "8px";
mapDiv.style.marginTop = "1rem";

const map = new maplibregl.Map({
  container: mapDiv,
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
  bounds: [
    [1.5629901, 50.0198391],
    [3.188217, 51.0068167]
  ]
});
map.addControl(new maplibregl.NavigationControl());

const renderStart = performance.now();
map.on("load", () => {
  map.addSource("parcels", {type: "geojson", data: parcelsGeo});
  map.addLayer({
    id: "parcels-fill",
    type: "fill",
    source: "parcels",
    paint: {"fill-color": fillColorExpr, "fill-opacity": 0.65}
  });
  map.addLayer({
    id: "parcels-line",
    type: "line",
    source: "parcels",
    paint: {"line-color": "#20201d", "line-width": 0.3, "line-opacity": 0.5}
  });

  const popup = new maplibregl.Popup({closeButton: false});
  map.on("mousemove", "parcels-fill", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const f = e.features[0];
    popup
      .setLngLat(e.lngLat)
      .setHTML(`<strong>${f.properties.k}</strong> — ${f.properties.s} ha`)
      .addTo(map);
  });
  map.on("mouseleave", "parcels-fill", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
  });

  map.once("idle", () => {
    const renderMs = performance.now() - renderStart;
    const kpi = document.querySelector("#render-kpi .big");
    if (kpi) kpi.textContent = `${Math.round(renderMs).toLocaleString("fr-FR")} ms`;
  });
});
```

<div class="grid grid-cols-1">
  <div class="card">${mapDiv}</div>
</div>
