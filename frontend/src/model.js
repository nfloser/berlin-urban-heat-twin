export function temperatureIndicator(snapshot) {
  return snapshot?.state?.indicators?.find((item) => item.name === 'observed_station_temperature_median') ?? null;
}

export function provenanceLabel(stateType) {
  const labels = {
    observed: 'MEASURED',
    official_modelled: 'OFFICIALLY MODELLED',
    derived: 'DERIVED',
    scenario: 'HYPOTHETICAL'
  };
  return labels[stateType] ?? 'UNKNOWN';
}

export function areaDescriptor(area) {
  const parts = [area?.source_key, area?.layer_type].filter(Boolean);
  return parts.length ? parts.join(' · ') : 'official climate feature';
}

export function formatTimestamp(value) {
  if (!value) return 'No timestamp available';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'Invalid timestamp' : parsed.toLocaleString(undefined, { timeZoneName: 'short' });
}
