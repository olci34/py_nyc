import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Initialize the map
const map = L.map("map").setView([40.7831, -73.9712], 12);

// Add OpenStreetMap tiles
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

fetch("http://localhost:8000/trips?date=2023-01-12T15:30:45")
  .then((d) => d.json())
  .then((data) => {
    console.log("watch test");
    return L.geoJSON(data).addTo(map);
  });
