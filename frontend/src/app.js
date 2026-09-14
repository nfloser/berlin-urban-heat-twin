import { temperatureIndicator, provenanceLabel } from './model.js';

const status = document.querySelector('#status');
const temperature = document.querySelector('#temperature');
const features = document.querySelector('#features');
const freshness = document.querySelector('#freshness');
const limitations = document.querySelector('#limitations');

const map = L.map('map', { zoomControl: false }).setView([52.52, 13.405], 10.5);
L.control.zoom({ position: 'bottomright' }).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19
}).addTo(map);
const stationLayer = L.layerGroup().addTo(map);
const areaLayer = L.geoJSON([], { style: { weight: 1, fillOpacity: 0.22 } }).addTo(map);

document.querySelector('#stationsToggle').addEventListener('change', (event) => event.target.checked ? stationLayer.addTo(map) : map.removeLayer(stationLayer));
document.querySelector('#areasToggle').addEventListener('change', (event) => event.target.checked ? areaLayer.addTo(map) : map.removeLayer(areaLayer));

async function load() {
  try {
    const response = await fetch('/api/v1/heat/snapshot');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const snapshot = await response.json();
    status.textContent = snapshot.state.quality.toUpperCase();
    const indicator = temperatureIndicator(snapshot);
    temperature.textContent = indicator ? `${Number(indicator.value).toFixed(1)} °C` : '—';
    freshness.textContent = snapshot.freshness_hours == null ? 'No cached observation' : `Freshness ${snapshot.freshness_hours.toFixed(1)} h · ${indicator ? provenanceLabel(indicator.state_type) : ''}`;
    features.textContent = String(snapshot.state.official_feature_count);
    limitations.textContent = snapshot.uncertainty.join(' ');
    for (const station of snapshot.stations) {
      const obs = snapshot.observations.find((item) => item.station_id === station.station_id);
      const text = obs?.air_temperature_c == null ? 'No temperature' : `${obs.air_temperature_c.toFixed(1)} °C`;
      L.circleMarker([station.latitude, station.longitude], { radius: 6 }).bindPopup(`<b>${station.name}</b><br>${text}<br>MEASURED`).addTo(stationLayer);
    }
    for (const area of snapshot.official_areas.filter((item) => item.geometry_valid)) {
      areaLayer.addData({ type: 'Feature', geometry: area.geometry, properties: { ...area.attributes, provenance: 'OFFICIALLY MODELLED' } });
    }
  } catch (error) {
    status.textContent = 'OFFLINE';
    limitations.textContent = `Snapshot unavailable: ${error.message}`;
  }
}
load();
