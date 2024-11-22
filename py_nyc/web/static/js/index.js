import L from "leaflet";
import "leaflet/dist/leaflet.css";
import moment from "moment";

document.addEventListener("DOMContentLoaded", async () => {
  function getColor(density) {
    return density > 100
      ? "#800026"
      : density > 50
      ? "#BD0026"
      : density > 20
      ? "#E31A1C"
      : density > 10
      ? "#FC4E2A"
      : "#FFEDA0";
  }

  function style(feature) {
    return {
      fillColor: getColor(feature.properties.density),
      weight: 2,
      opacity: 1,
      color: "white",
      dashArray: "3",
      fillOpacity: 0.7,
    };
  }

  function highlightFeature(e, feature) {
    resetStyle();

    const layer = e.target;
    layer.setStyle({
      weight: 5,
      color: "#666",
      dashArray: "",
      fillOpacity: 0.7,
    });

    const popupMessage = `Trip Count: <b>${feature.properties.density.toString()}</b>`;
    layer.bindPopup(popupMessage).openPopup();

    layer.bringToFront();
  }

  function onEachFeature(feature, layer) {
    layer.on({
      click: (e) => highlightFeature(e, feature),
    });
  }

  function fetchTrips(date, hour_span = 1) {
    const tripsURL = "http://localhost:8000/trips";
    const query = `date=${date.format(
      "YYYY-MM-DDTHH:mm:ss"
    )}&hour_span=${hour_span.toString()}`;
    return fetch(`${tripsURL}?${query}`)
      .then((d) => d.json())
      .then((data) => data);
  }

  // Initialize the map
  const map = L.map("map").setView([40.7831, -73.9712], 12);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  const date = moment();
  date.set("year", 2023);

  let tripsGeoJSON = await fetchTrips(date);
  let geojson = L.geoJSON(tripsGeoJSON, {
    style: style,
    onEachFeature: onEachFeature,
  }).addTo(map);

  function resetStyle() {
    geojson.resetStyle();
  }
});
