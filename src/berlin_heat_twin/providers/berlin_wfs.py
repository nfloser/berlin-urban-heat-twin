from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from berlin_heat_twin.domain import ClimateZone, Provenance, StateType, UrbanClimateLayer
from berlin_heat_twin.geo import validate_geometry
from berlin_heat_twin.sources import SourceConfig


class BerlinWFSProvider:
    def __init__(self, source: SourceConfig, timeout_seconds: float = 30) -> None:
        self.source = source
        self.timeout_seconds = timeout_seconds

    def _provenance(self) -> Provenance:
        return Provenance(
            source="Berlin Open Data / Umweltatlas",
            dataset=self.source.title,
            source_url=self.source.dataset_page,
            state_type=StateType.OFFICIAL_MODELLED,
            license=self.source.licence,
            retrieved_at=datetime.now(UTC),
        )

    @staticmethod
    def parse_capabilities(xml_text: str, source: SourceConfig) -> list[UrbanClimateLayer]:
        root = ElementTree.fromstring(xml_text)
        namespace = {"wfs": "http://www.opengis.net/wfs/2.0"}
        layers: list[UrbanClimateLayer] = []
        provenance = Provenance(
            source="Berlin Open Data / Umweltatlas",
            dataset=source.title,
            source_url=source.dataset_page,
            state_type=StateType.OFFICIAL_MODELLED,
            license=source.licence,
        )
        for feature_type in root.findall(".//wfs:FeatureType", namespace):
            name_node = feature_type.find("wfs:Name", namespace)
            if name_node is None or not name_node.text:
                continue
            title_node = feature_type.find("wfs:Title", namespace)
            crs_node = feature_type.find("wfs:DefaultCRS", namespace)
            layers.append(
                UrbanClimateLayer(
                    source_key=source.key,
                    type_name=name_node.text.strip(),
                    title=title_node.text.strip()
                    if title_node is not None and title_node.text
                    else None,
                    default_crs=crs_node.text.strip()
                    if crs_node is not None and crs_node.text
                    else None,
                    provenance=provenance,
                )
            )
        return layers

    def discover_layers(self) -> list[UrbanClimateLayer]:
        params = {"service": "WFS", "request": "GetCapabilities", "version": "2.0.0"}
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(self.source.url, params=params)
            response.raise_for_status()
        return self.parse_capabilities(response.text, self.source)

    @staticmethod
    def parse_feature_collection(
        payload: dict[str, Any],
        source: SourceConfig,
        crs: str = "EPSG:4326",
        type_name: str | None = None,
    ) -> list[ClimateZone]:
        if payload.get("type") != "FeatureCollection":
            raise ValueError("expected GeoJSON FeatureCollection")
        zones: list[ClimateZone] = []
        provenance = Provenance(
            source="Berlin Open Data / Umweltatlas",
            dataset=source.title,
            source_url=source.dataset_page,
            state_type=StateType.OFFICIAL_MODELLED,
            license=source.licence,
        )
        features = payload.get("features", [])
        if not isinstance(features, list):
            raise ValueError("GeoJSON features must be a list")
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                raise ValueError("GeoJSON feature must be an object")
            geometry = feature.get("geometry")
            if geometry is None:
                continue
            if not isinstance(geometry, dict):
                raise ValueError("GeoJSON geometry must be an object")
            valid, _ = validate_geometry(geometry)
            properties = dict(feature.get("properties") or {})
            feature_id = str(feature.get("id") or properties.get("gml_id") or index)
            zones.append(
                ClimateZone(
                    zone_id=feature_id,
                    source_key=source.key,
                    layer_type=type_name,
                    geometry=geometry,
                    crs=crs,
                    attributes=properties,
                    provenance=provenance,
                    geometry_valid=valid,
                )
            )
        return zones

    def fetch_features(self, type_name: str, limit: int = 5000) -> list[ClimateZone]:
        if limit < 1:
            raise ValueError("limit must be positive")
        params = {
            "service": "WFS",
            "request": "GetFeature",
            "version": "2.0.0",
            "typeNames": type_name,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "count": str(limit),
        }
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(self.source.url, params=params)
            response.raise_for_status()
            payload = response.json()
        return self.parse_feature_collection(
            payload, self.source, crs="EPSG:4326", type_name=type_name
        )
