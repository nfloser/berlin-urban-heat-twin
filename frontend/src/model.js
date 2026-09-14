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
