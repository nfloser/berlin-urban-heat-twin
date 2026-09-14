from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StateType(StrEnum):
    OBSERVED = "observed"
    OFFICIAL_MODELLED = "official_modelled"
    DERIVED = "derived"
    SCENARIO = "scenario"


class QualityFlag(StrEnum):
    VERIFIED = "verified"
    PROVISIONAL = "provisional"
    STALE = "stale"
    MISSING = "missing"
    INVALID = "invalid"


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    dataset: str
    source_url: str
    state_type: StateType
    license: str | None = None
    retrieved_at: datetime | None = None
    methodology: str | None = None

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_at_must_be_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")
        return value


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class UrbanClimateLayer(BaseModel):
    source_key: str
    type_name: str
    title: str | None = None
    default_crs: str | None = None
    provenance: Provenance


class ClimateZone(BaseModel):
    zone_id: str
    source_key: str | None = None
    layer_type: str | None = None
    geometry: dict[str, Any]
    crs: str
    attributes: dict[str, Any]
    provenance: Provenance
    geometry_valid: bool = True


class MeteorologicalStation(BaseModel):
    station_id: str
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def validate_period(self) -> MeteorologicalStation:
        for value in (self.valid_from, self.valid_to):
            if value is not None and value.tzinfo is None:
                raise ValueError("station validity timestamps must be timezone-aware")
        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            raise ValueError("valid_from must not be after valid_to")
        return self

    def active_at(self, when: datetime) -> bool:
        if when.tzinfo is None:
            raise ValueError("when must be timezone-aware")
        return (self.valid_from is None or self.valid_from <= when) and (
            self.valid_to is None or when <= self.valid_to
        )


class MeteorologicalObservation(BaseModel):
    station_id: str
    timestamp: datetime
    air_temperature_c: float | None = Field(default=None, ge=-80, le=60)
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    wind_speed_m_s: float | None = Field(default=None, ge=0)
    precipitation_mm: float | None = Field(default=None, ge=0)
    solar_radiation_w_m2: float | None = Field(default=None, ge=0)
    quality: QualityFlag = QualityFlag.VERIFIED
    provenance: Provenance

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(UTC)


class ThermalIndicator(BaseModel):
    name: str
    value: float | str
    unit: str
    state_type: StateType
    method: str
    provenance: Provenance


class HeatState(BaseModel):
    timestamp: datetime
    latest_observation_at: datetime | None
    observation_count: int
    official_feature_count: int
    indicators: list[ThermalIndicator]
    quality: QualityFlag
    limitations: list[str]


class HeatSnapshot(BaseModel):
    schema_version: str = "1.0"
    timestamp: datetime
    crs: str = "EPSG:4326"
    state: HeatState
    stations: list[MeteorologicalStation]
    observations: list[MeteorologicalObservation]
    official_areas: list[ClimateZone]
    freshness_hours: float | None = None
    spatial_coverage: str
    uncertainty: list[str]


class ThermalArea(BaseModel):
    schema_version: str = "1.0"
    timestamp: datetime
    area_id: str
    geometry: dict[str, Any]
    crs: str = "EPSG:4326"
    indicators: list[ThermalIndicator]
    state_type: StateType
    source: str
    official_classification: str | None = None
    provenance: Provenance
    freshness_hours: float | None = Field(default=None, ge=0)
    quality: QualityFlag
    uncertainty: list[str] = Field(default_factory=list)

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(UTC)


class AreaCategoryStatistic(BaseModel):
    category: str
    feature_count: int = Field(ge=0)
    area_m2: float = Field(ge=0)
    fraction_of_analysed_area: float = Field(ge=0, le=1)


class AreaSummary(BaseModel):
    schema_version: str = "1.0"
    generated_at: datetime
    state_type: StateType = StateType.DERIVED
    source_key: str | None = None
    layer_type: str | None = None
    attribute: str
    analysed_feature_count: int = Field(ge=0)
    skipped_invalid_geometries: int = Field(ge=0)
    skipped_missing_attribute: int = Field(ge=0)
    total_area_m2: float = Field(ge=0)
    categories: list[AreaCategoryStatistic]
    methodology: str
    provenance: Provenance
    uncertainty: list[str] = Field(default_factory=list)


class AreaGroupSummary(BaseModel):
    group: str
    summary: AreaSummary


class GroupedAreaSummary(BaseModel):
    schema_version: str = "1.0"
    generated_at: datetime
    state_type: StateType = StateType.DERIVED
    classification_attribute: str
    group_attribute: str
    groups: list[AreaGroupSummary]
    methodology: str
    uncertainty: list[str] = Field(default_factory=list)


class NumericAttributeSummary(BaseModel):
    schema_version: str = "1.0"
    generated_at: datetime
    state_type: StateType = StateType.DERIVED
    source_key: str | None = None
    layer_type: str | None = None
    attribute: str
    unit: str
    count: int = Field(ge=0)
    skipped_missing_or_non_numeric: int = Field(ge=0)
    minimum: float | None = None
    median: float | None = None
    maximum: float | None = None
    methodology: str
    provenance: Provenance
    uncertainty: list[str] = Field(default_factory=list)


class MatchedClimateArea(BaseModel):
    area_id: str
    source_key: str | None = None
    layer_type: str | None = None
    classification: str | None = None
    provenance: Provenance


class StationClimateOverlap(BaseModel):
    schema_version: str = "1.0"
    timestamp: datetime
    station_id: str
    station_name: str
    longitude: float
    latitude: float
    air_temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    observation_quality: QualityFlag
    observation_provenance: Provenance
    matched_areas: list[MatchedClimateArea]
    methodology: str = (
        "Point-in-polygon overlap between latest measured station observations and official climate areas; "
        "no spatial interpolation is performed."
    )


class SpatialQueryRequest(BaseModel):
    geometry: dict[str, Any]
    crs: str = "EPSG:4326"
    source_key: str | None = None
    layer_type: str | None = None


class ScenarioRequest(BaseModel):
    temperature_delta_c: float = Field(ge=-15, le=15)
    label: str = "caller-defined temperature stress test"


class ScenarioResult(BaseModel):
    schema_version: str = "1.0"
    state_type: StateType = StateType.SCENARIO
    generated_at: datetime
    base_snapshot_timestamp: datetime
    parameter: ScenarioRequest
    indicators: list[ThermalIndicator]
    statement: str = "Hypothetical scenario; not an observation or forecast."
