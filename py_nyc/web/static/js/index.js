import L from "leaflet";
import "leaflet/dist/leaflet.css";
import moment from "moment";

// Initialize the map
const map = L.map("map").setView([40.7831, -73.9712], 12);
const date = moment();
date.set("year", 2023);
// Add OpenStreetMap tiles
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

fetch(`http://localhost:8000/trips?date=${date.format("YYYY-MM-DDTHH:mm:ss")}`)
  .then((d) => d.json())
  .then((data) => {
    return L.geoJSON(data).addTo(map);
  });
