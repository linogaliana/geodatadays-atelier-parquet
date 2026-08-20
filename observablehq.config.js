// See https://observablehq.com/framework/config for documentation.
export default {
  title: "Pas-de-Calais 2024 — RPG & OCS",

  pages: [
    {name: "Carte brute (MapLibre)", path: "/index"},
    {name: "Dashboard par commune (RPG)", path: "/side"},
    {name: "Occupation du sol (OCS)", path: "/occupation-sol"}
  ],

  head: `
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌾</text></svg>">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
    <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.css" integrity="sha256-qx5w1Z7EBGW65+cDDaLzzPKBM/1QLmK9WY7vut/XpzI=" crossorigin="">
  `,

  root: "src",

  // Pinned to the light theme: the crop-family color scale below is tuned
  // for a light surface, and Framework has no theme-detection hook to swap
  // JS-side color scales when the OS/user switches to dark mode.
  theme: ["air", "alt", "wide"],
  header: "",
  footer:
    'Données : <a href="https://www.data.gouv.fr/fr/datasets/registre-parcellaire-graphique-rpg/">RPG 2024</a> et OCS 2D (Pas-de-Calais), traitées avec <a href="https://duckdb.org/">DuckDB</a> · Atelier Parquet — Geodata Days',
  sidebar: true,
  toc: true,
  pager: false,
};
