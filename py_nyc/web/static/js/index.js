import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Initialize the map
const map = L.map("map").setView([40.7128, -74.006], 10);

// Add OpenStreetMap tiles
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

console.log("asdf");
