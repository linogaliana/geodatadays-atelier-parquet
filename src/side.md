---
title: Dashboard par commune
toc: true
---

# 🌾 RPG Pas-de-Calais 2024 — parcelles & cultures

Exploration du [Registre Parcellaire Graphique](https://www.data.gouv.fr/fr/datasets/registre-parcellaire-graphique-rpg/) (déclarations PAC) 2024 pour le département du Pas-de-Calais : **162 705 parcelles agricoles**, réparties sur **886 communes**, classées en **109 cultures**. Les géométries et statistiques sont calculées à la construction du site avec [DuckDB](https://duckdb.org/) (extension `spatial`) directement sur les fichiers Parquet source — voir la note méthodologique en bas de page. Voir aussi la [carte brute de toutes les parcelles](./index), sans filtre.

```js
const dico = FileAttachment("data/dico-culture.json").json();
const statsCulture = FileAttachment("data/stats-culture.json").json();
const statsCommune = FileAttachment("data/stats-commune.json").json();
```

```js
const chapitreByCode = new Map(dico.map((d) => [d.code_culture, d.nom_chapitre]));
const nomCultureByCode = new Map(dico.map((d) => [d.code_culture, d.nom_culture]));
```

```js
// Short display labels for the (sometimes very long) official chapter names.
const SHORT_LABEL = {
  "Céréales et pseudo-céréales": "Céréales",
  "Cultures industrielles et plantes sarclées": "Cultures industrielles",
  "Prairies ou pâturages permanents": "Prairies permanentes",
  "Oléagineux": "Oléagineux",
  "Surfaces herbacées temporaires et mélanges avec graminées": "Surfaces herbacées temp.",
  "Légumes et fruits (sauf légumineuses) – Alimentation humaine ou animale": "Légumes et fruits",
  "Autres surfaces admissibles spécifiques": "Autres surfaces spécifiques",
  "Arboriculture fruitière et viticulture, plantes à parfum, aromatiques et médicinales (PPAM) arbustives et arborées": "Arboriculture / viticulture",
  "Plantes à parfum, aromatiques et médicinales et plantes ornementales (hors espèces arbustives et arborées)": "PPAM / ornementales",
  "Divers – Surfaces non admissibles aux aides 1er pilier": "Divers (non admissible)",
  Autres: "Autres"
};

function shortLabel(name) {
  if (name in SHORT_LABEL) return SHORT_LABEL[name];
  return name.length > 32 ? `${name.slice(0, 30)}…` : name;
}
```

```js
// A fixed, validated 8-slot categorical palette (blue…red), assigned in a
// stable rank order (top-7 chapters by surface + "Autres") and reused as-is
// across the bar chart, the commune overview map and the parcel map.
const PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];

const chapterTotals = d3.sort(
  d3.rollups(statsCulture, (v) => d3.sum(v, (d) => d.surface_ha), (d) => d.nom_chapitre),
  (d) => -d[1]
);
const topChapters = chapterTotals.slice(0, 7).map((d) => d[0]);
const chapterOrder = [...topChapters, "Autres"];
const chapterColor = d3.scaleOrdinal(chapterOrder, PALETTE);

function chapterCategory(nomChapitre) {
  return topChapters.includes(nomChapitre) ? nomChapitre : "Autres";
}
```

```js
const totalSurface = d3.sum(statsCulture, (d) => d.surface_ha);
const totalParcelles = d3.sum(statsCulture, (d) => d.n_parcelles);
```

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Parcelles</h2>
    <span class="big">${totalParcelles.toLocaleString("fr-FR")}</span>
  </div>
  <div class="card">
    <h2>Surface agricole</h2>
    <span class="big">${Math.round(totalSurface).toLocaleString("fr-FR")} ha</span>
  </div>
  <div class="card">
    <h2>Communes</h2>
    <span class="big">${statsCommune.length.toLocaleString("fr-FR")}</span>
  </div>
  <div class="card">
    <h2>Cultures déclarées</h2>
    <span class="big">${statsCulture.length.toLocaleString("fr-FR")}</span>
  </div>
</div>

## Composition des surfaces agricoles

Les 12 chapitres de culture du RPG regroupés ici en 8 catégories (les 4 plus petits chapitres sont fondus dans « Autres »).

```js
const chapterAgg = chapterOrder.map((chapitre) => {
  const rows = statsCulture.filter((d) => chapterCategory(d.nom_chapitre) === chapitre);
  return {
    chapitre,
    surface_ha: d3.sum(rows, (d) => d.surface_ha),
    n_parcelles: d3.sum(rows, (d) => d.n_parcelles)
  };
});
```

```js
function chapterBar(data, {width} = {}) {
  return Plot.plot({
    width,
    height: 360,
    marginLeft: 200,
    x: {label: "Surface (ha)", grid: true, tickFormat: (d) => d.toLocaleString("fr-FR")},
    y: {label: null, domain: chapterOrder, tickFormat: shortLabel},
    color: {domain: chapterOrder, range: PALETTE},
    marks: [
      Plot.barX(data, {
        y: "chapitre",
        x: "surface_ha",
        fill: "chapitre",
        sort: {y: null},
        tip: true,
        title: (d) => `${d.chapitre}\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_parcelles.toLocaleString("fr-FR")} parcelles`
      }),
      Plot.text(data, {
        y: "chapitre",
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
  <div class="card">${resize((width) => chapterBar(chapterAgg, {width}))}</div>
</div>

## Cultures dominantes au sein d'un chapitre

```js
const allChapters = d3.sort(new Set(statsCulture.map((d) => d.nom_chapitre)), (a, b) => d3.descending(
  chapterTotals.find((d) => d[0] === a)?.[1] ?? 0,
  chapterTotals.find((d) => d[0] === b)?.[1] ?? 0
));
const chapitreSel = view(Inputs.select(allChapters, {label: "Chapitre de culture", value: allChapters[0], format: shortLabel}));
```

```js
const culturesInChapitre = d3.sort(
  statsCulture.filter((d) => d.nom_chapitre === chapitreSel),
  (d) => -d.surface_ha
).slice(0, 12);
```

```js
function cultureBar(data, {width} = {}) {
  return Plot.plot({
    title: `Cultures principales — ${shortLabel(chapitreSel)}`,
    width,
    height: 340,
    marginLeft: 260,
    x: {label: "Surface (ha)", grid: true, tickFormat: (d) => d.toLocaleString("fr-FR")},
    y: {label: null},
    marks: [
      Plot.barX(data, {
        y: "nom_culture",
        x: "surface_ha",
        fill: PALETTE[0],
        sort: {y: "-x"},
        tip: true,
        title: (d) => `${d.nom_culture} (${d.code_cultu})\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_parcelles.toLocaleString("fr-FR")} parcelles`
      }),
      Plot.text(data, {
        y: "nom_culture",
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
  <div class="card">${resize((width) => cultureBar(culturesInChapitre, {width}))}</div>
</div>

## Vue d'ensemble par commune

Chaque point est une commune : la taille encode la surface agricole totale, la couleur la diversité des cultures qui y sont déclarées (nombre de codes-culture distincts).

```js
const latMean = d3.mean(statsCommune, (d) => d.lat);
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
    color: {type: "sequential", scheme: "blues", label: "Cultures distinctes", legend: true},
    marks: [
      Plot.dot(data, {
        x: (d) => d.lon * kx,
        y: "lat",
        r: "surface_ha",
        fill: "n_cultures",
        stroke: "white",
        strokeWidth: 0.5,
        tip: true,
        title: (d) => `${d.commune}\n${Math.round(d.surface_ha).toLocaleString("fr-FR")} ha · ${d.n_parcelles.toLocaleString("fr-FR")} parcelles\n${d.n_cultures} cultures distinctes\nDominante : ${shortLabel(d.chapitre_dominant)}`
      })
    ]
  });
}
```

<div class="grid grid-cols-1">
  <div class="card">${resize((width) => communeMap(statsCommune, {width}))}</div>
</div>

## Explorer les parcelles d'une commune

Sélectionnez une commune pour afficher ses parcelles RPG, colorées par chapitre de culture.

```js
const communesByName = new Map(statsCommune.map((d) => [d.commune, d]));
const communeNames = d3.sort(statsCommune.map((d) => d.commune), d3.ascending);
const communeSel = view(Inputs.select(communeNames, {label: "Commune", value: "Arras"}));
```

```js
import {communeFiles} from "./data/communes/index.js";
import * as L from "npm:leaflet@1.9.4";
```

```js
const communeMeta = communesByName.get(communeSel);
const parcelsGeo = await communeFiles[communeMeta.slug].json();
```

```js
// Created once (no dependency on the selected commune) so the map instance
// and its parcel layer persist across selections instead of being rebuilt.
const mapDiv = display(document.createElement("div"));
mapDiv.style.height = "520px";
mapDiv.style.borderRadius = "8px";
mapDiv.style.zIndex = "0";

const map = L.map(mapDiv).setView([d3.mean(statsCommune, (d) => d.lat), d3.mean(statsCommune, (d) => d.lon)], 9);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19
}).addTo(map);

const parcelsLayer = L.geoJSON(null, {
  style: (f) => ({
    fillColor: chapterColor(chapterCategory(chapitreByCode.get(f.properties.k) ?? "Autres")),
    fillOpacity: 0.75,
    color: "#20201d",
    weight: 0.6
  }),
  onEachFeature: (f, layer) => {
    const nom = nomCultureByCode.get(f.properties.k) ?? f.properties.k;
    layer.bindTooltip(`<strong>${nom}</strong> (${f.properties.k})<br>${f.properties.s} ha`);
  }
}).addTo(map);
```

```js
parcelsLayer.clearLayers();
parcelsLayer.addData(parcelsGeo);
if (parcelsLayer.getBounds().isValid()) map.fitBounds(parcelsLayer.getBounds(), {maxZoom: 15, padding: [16, 16]});
```

<div class="grid grid-cols-1">
  <div class="card">${mapDiv}</div>
</div>

```js
function chapterLegend() {
  const div = document.createElement("div");
  div.style.cssText = "display:flex;flex-wrap:wrap;gap:0.75rem 1.5rem;font-size:0.85em;";
  for (const chapitre of chapterOrder) {
    const item = document.createElement("span");
    item.style.cssText = "display:inline-flex;align-items:center;gap:0.4em;";
    const swatch = document.createElement("span");
    swatch.style.cssText = `display:inline-block;width:0.85em;height:0.85em;border-radius:2px;background:${chapterColor(chapitre)};border:1px solid var(--theme-foreground-muted);`;
    item.append(swatch, shortLabel(chapitre));
    div.append(item);
  }
  return div;
}
```

<div class="grid grid-cols-1">
  <div class="card">${chapterLegend()}</div>
</div>

```js
const parcelRows = d3.sort(
  parcelsGeo.features.map((f) => ({
    code_cultu: f.properties.k,
    nom_culture: nomCultureByCode.get(f.properties.k) ?? f.properties.k,
    chapitre: shortLabel(chapitreByCode.get(f.properties.k) ?? "Autres"),
    surface_ha: f.properties.s
  })),
  (d) => -d.surface_ha
);
```

<div class="grid grid-cols-1">
  <div class="card">
    <h2>${parcelRows.length.toLocaleString("fr-FR")} parcelles — ${communeSel}</h2>
    ${Inputs.table(parcelRows, {
      columns: ["code_cultu", "nom_culture", "chapitre", "surface_ha"],
      header: {code_cultu: "Code", nom_culture: "Culture", chapitre: "Chapitre", surface_ha: "Surface (ha)"},
      width: {code_cultu: 70, surface_ha: 110},
      sort: "surface_ha",
      reverse: true
    })}
  </div>
</div>

---

## Méthodologie

Les données sources sont deux fichiers Parquet publics (`rpg_pac_2024_62_comm_v11.parquet` pour le RPG, plus le dictionnaire des cultures `code_culture_2026.xlsx`), lus et transformés avec DuckDB et son extension `spatial` :

- `src/data/dico-culture.json.py` — dictionnaire des 143 codes-culture (chapitre, catégorie).
- `src/data/stats-culture.json.py` — surfaces et effectifs agrégés par culture (département).
- `src/data/stats-commune.json.py` — agrégats par commune (centroïde, diversité, chapitre dominant).
- `scripts/generate_commune_parcels.py` — géométries des parcelles reprojetées en WGS84, simplifiées et **découpées en un fichier par commune** (plutôt qu'un unique GeoJSON de ~40 Mo, chaque commune ne pèse que quelques dizaines de Ko) — exécuté avant `build`/`dev` (voir `package.json`).

Ces requêtes s'inspirent directement des exemples DuckDB du dossier `sql/` du dépôt.
