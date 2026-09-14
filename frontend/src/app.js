import { areaDescriptor, formatTimestamp, provenanceLabel, temperatureIndicator } from './model.js';

const status = document.querySelector('#status');
const timestamp = document.querySelector('#timestamp');
const temperature = document.querySelector('#temperature');
const features = document.querySelector('#features');
const layerCount = document.querySelector('#layerCount');
const freshness = document.querySelector('#freshness');
const limitations = document.querySelector('#limitations');
const sourceList = document.querySelector('#sourceList');

const map = L.map('map', { zoomControl: false }).setView([52.52, 13.405], 10.5);
L.control.zoom({ position: 'bottomright' }).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19
}).addTo(map);

const stationLayer = L.layerGroup().addTo(map);
const areaLayer = L.geoJSON([], {
  style: { weight: 1, opacity: 0.8, fillOpacity: 0.2 }
}).addTo(map);

document.querySelector('#stationsToggle').addEventListener('change', (event) => {
  if (event.target.checked) stationLayer.addTo(map);
  else map.removeLayer(stationLayer);
});
document.querySelector('#areasToggle').addEventListener('change', (event) => {
  if (event.target.checked) areaLayer.addTo(map);
  else map.removeLayer(areaLayer);
});

function text(value) {
  return document.createTextNode(value == null ? '—' : String(value));
}

function popup(lines) {
  const container = document.createElement('div');
  container.className = 'map-popup';
  for (const [label, value] of lines) {
    const row = document.createElement('p');
    const strong = document.createElement('strong');
    strong.append(text(`${label}: `));
    row.append(strong, text(value));
    container.append(row);
  }
  return container;
}

function renderSources(sources, snapshot) {
  sourceList.replaceChildren();
  const cachedKeys = new Set(snapshot.official_areas.map((area) => area.source_key).filter(Boolean));
  for (const source of sources) {
    const row = document.createElement('div');
    row.className = 'source-row';
    const title = document.createElement('strong');
    title.append(text(source.title));
    const metadata = document.createElement('span');
    const state = provenanceLabel(source.state_type);
    const cacheStatus = source.state_type === 'observed' ? 'station cache' : (cachedKeys.has(source.key) ? 'cached features' : 'not cached');
    metadata.append(text(`${state} · ${cacheStatus}`));
    row.append(title, metadata);
    sourceList.append(row);
  }
}

function renderSnapshot(snapshot) {
  status.textContent = snapshot.state.quality.toUpperCase();
  timestamp.textContent = `Snapshot ${formatTimestamp(snapshot.timestamp)}`;

  const indicator = temperatureIndicator(snapshot);
  temperature.textContent = indicator ? `${Number(indicator.value).toFixed(1)} °C` : '—';
  freshness.textContent = snapshot.freshness_hours == null
    ? 'No cached observation'
    : `Latest observation age ${snapshot.freshness_hours.toFixed(1)} h · ${indicator ? provenanceLabel(indicator.state_type) : ''}`;
  features.textContent = String(snapshot.state.official_feature_count);

  const layerKeys = new Set(
    snapshot.official_areas.map((area) => `${area.source_key ?? 'unknown'}:${area.layer_type ?? 'unknown'}`)
  );
  layerCount.textContent = `${layerKeys.size} cached source/layer combination${layerKeys.size === 1 ? '' : 's'}`;
  limitations.textContent = snapshot.uncertainty.length
    ? snapshot.uncertainty.join(' ')
    : 'No additional limitations reported by the current snapshot.';

  stationLayer.clearLayers();
  areaLayer.clearLayers();

  for (const station of snapshot.stations) {
    const observation = snapshot.observations.find((item) => item.station_id === station.station_id);
    const marker = L.circleMarker([station.latitude, station.longitude], { radius: 6, weight: 2, fillOpacity: 0.9 });
    marker.bindPopup(popup([
      ['Station', station.name],
      ['Station ID', station.station_id],
      ['State', 'MEASURED'],
      ['Observation time', formatTimestamp(observation?.timestamp)],
      ['Air temperature', observation?.air_temperature_c == null ? 'not available' : `${observation.air_temperature_c.toFixed(1)} °C`],
      ['Relative humidity', observation?.relative_humidity_pct == null ? 'not available' : `${observation.relative_humidity_pct.toFixed(0)} %`],
      ['Quality', observation?.quality ?? 'no observation']
    ]));
    marker.addTo(stationLayer);
  }

  for (const area of snapshot.official_areas.filter((item) => item.geometry_valid)) {
    const feature = {
      type: 'Feature',
      geometry: area.geometry,
      properties: {}
    };
    const rendered = L.geoJSON(feature, { style: { weight: 1, opacity: 0.8, fillOpacity: 0.2 } });
    rendered.bindPopup(popup([
      ['Area ID', area.zone_id],
      ['State', 'OFFICIALLY MODELLED'],
      ['Source/layer', areaDescriptor(area)],
      ['CRS', area.crs],
      ['Source', area.provenance?.source ?? 'Berlin official source'],
      ['Dataset', area.provenance?.dataset ?? 'not available']
    ]));
    rendered.eachLayer((layer) => areaLayer.addLayer(layer));
  }
}

async function load() {
  try {
    const [snapshotResponse, sourcesResponse] = await Promise.all([
      fetch('/api/v1/heat/snapshot'),
      fetch('/api/v1/sources')
    ]);
    if (!snapshotResponse.ok) throw new Error(`snapshot HTTP ${snapshotResponse.status}`);
    if (!sourcesResponse.ok) throw new Error(`sources HTTP ${sourcesResponse.status}`);
    const [snapshot, sources] = await Promise.all([snapshotResponse.json(), sourcesResponse.json()]);
    renderSnapshot(snapshot);
    renderSources(sources, snapshot);
  } catch (error) {
    status.textContent = 'OFFLINE';
    limitations.textContent = `Snapshot unavailable: ${error.message}`;
    sourceList.textContent = 'Primary-source metadata could not be loaded from the API.';
  }
}

load();
