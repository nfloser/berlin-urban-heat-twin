import test from 'node:test';
import assert from 'node:assert/strict';
import { areaDescriptor, formatTimestamp, provenanceLabel, temperatureIndicator } from '../src/model.js';

test('temperatureIndicator selects only the transparent derived station median', () => {
  const snapshot = { state: { indicators: [{ name: 'other' }, { name: 'observed_station_temperature_median', value: 24 }] } };
  assert.equal(temperatureIndicator(snapshot).value, 24);
});

test('provenance labels preserve epistemic state', () => {
  assert.equal(provenanceLabel('observed'), 'MEASURED');
  assert.equal(provenanceLabel('official_modelled'), 'OFFICIALLY MODELLED');
  assert.equal(provenanceLabel('derived'), 'DERIVED');
  assert.equal(provenanceLabel('scenario'), 'HYPOTHETICAL');
});

test('areaDescriptor exposes source and layer instead of inventing a label', () => {
  assert.equal(
    areaDescriptor({ source_key: 'climate_assessment', layer_type: 'ua:test' }),
    'climate_assessment · ua:test'
  );
  assert.equal(areaDescriptor({}), 'official climate feature');
});

test('formatTimestamp is explicit about missing timestamps', () => {
  assert.equal(formatTimestamp(null), 'No timestamp available');
  assert.match(formatTimestamp('2026-09-14T12:00:00Z'), /2026/);
});
