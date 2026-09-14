from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from berlin_heat_twin.domain import (
    Provenance,
    QualityFlag,
    StateType,
    ThermalArea,
    ThermalIndicator,
)


def _provenance() -> Provenance:
    return Provenance(
        source="Berlin Open Data / Umweltatlas",
        dataset="fixture official layer",
        source_url="https://example.test",
        state_type=StateType.OFFICIAL_MODELLED,
    )


def test_thermal_area_contract_preserves_units_state_and_freshness() -> None:
    provenance = _provenance()
    indicator = ThermalIndicator(
        name="official_utci_category",
        value="strong heat stress",
        unit="category",
        state_type=StateType.OFFICIAL_MODELLED,
        method="preserved source attribute; no project reclassification",
        provenance=provenance,
    )
    area = ThermalArea(
        timestamp=datetime(2026, 9, 14, 12, tzinfo=UTC),
        area_id="official.1",
        geometry={"type": "Point", "coordinates": [13.4, 52.5]},
        indicators=[indicator],
        state_type=StateType.OFFICIAL_MODELLED,
        source="Berlin Open Data / Umweltatlas",
        provenance=provenance,
        freshness_hours=None,
        quality=QualityFlag.VERIFIED,
    )
    assert area.crs == "EPSG:4326"
    assert area.indicators[0].unit == "category"
    assert area.state_type == StateType.OFFICIAL_MODELLED
    assert area.source == "Berlin Open Data / Umweltatlas"
    assert area.freshness_hours is None


def test_thermal_area_timestamp_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        ThermalArea(
            timestamp=datetime(2026, 9, 14, 12),
            area_id="official.1",
            geometry={"type": "Point", "coordinates": [13.4, 52.5]},
            indicators=[],
            state_type=StateType.OFFICIAL_MODELLED,
            source="Berlin Open Data / Umweltatlas",
            provenance=_provenance(),
            quality=QualityFlag.VERIFIED,
        )
