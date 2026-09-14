from pathlib import Path

from berlin_heat_twin.providers.berlin_wfs import BerlinWFSProvider
from berlin_heat_twin.sources import BERLIN_SOURCES

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_parse_wfs_capabilities_preserves_type_and_crs() -> None:
    xml = (FIXTURES / "wfs_capabilities.xml").read_text()
    layers = BerlinWFSProvider.parse_capabilities(xml, BERLIN_SOURCES["climate_analysis"])
    assert len(layers) == 1
    assert layers[0].type_name == "fis:heat_zone"
    assert layers[0].default_crs == "urn:ogc:def:crs:EPSG::25833"
    assert layers[0].provenance.state_type == "official_modelled"


def test_describe_feature_type_extracts_declared_fields() -> None:
    xml = """<?xml version="1.0"?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="heat_zoneType">
        <xsd:complexContent><xsd:extension base="gml:AbstractFeatureType">
          <xsd:sequence>
            <xsd:element name="geometry" type="gml:MultiSurfacePropertyType" minOccurs="0"/>
            <xsd:element name="pet14h" type="xsd:double" minOccurs="0"/>
            <xsd:element name="phk_gesamt" type="xsd:string" minOccurs="0"/>
          </xsd:sequence>
        </xsd:extension></xsd:complexContent>
      </xsd:complexType>
    </xsd:schema>
    """
    fields = BerlinWFSProvider.parse_feature_schema(xml)
    assert fields["pet14h"] == "xsd:double"
    assert fields["phk_gesamt"] == "xsd:string"
    assert "geometry" in fields


def test_feature_collection_keeps_invalid_geometry_flag() -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "zone.1",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
                },
                "properties": {"official_class": "high"},
            }
        ],
    }
    zones = BerlinWFSProvider.parse_feature_collection(payload, BERLIN_SOURCES["climate_analysis"])
    assert zones[0].zone_id == "zone.1"
    assert zones[0].attributes["official_class"] == "high"
    assert zones[0].geometry_valid is False
