import test from 'node:test';
import assert from 'node:assert/strict';
import { provenanceLabel, temperatureIndicator } from '../src/model.js';

test('temperatureIndicator selects only the transparent derived station median', () => {
  const snapshot = { state: { indicators: [{ name: 'other' }, { name: 'observed_station_temperature_median', value: 24 }] } };
  assert.equal(temperatureIndicator(snapshot).value, 24);
});

test('provenance labels preserve epistemic state', () => {
  assert.equal(provenanceLabel('observed'), 'MEASURED');
  assert.equal(provenanceLabel('official_modelled'), 'OFFICIALLY MODELLED');
  assert.equal(provenanceLabel('scenario'), 'HYPOTHETICAL');
});
