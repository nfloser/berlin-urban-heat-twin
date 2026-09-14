"""Repository-level integrity checks used by CI.

The audit verifies contracts and repository hygiene without requiring external network access.
"""

from __future__ import annotations

from pathlib import Path

from berlin_heat_twin.api import app
from berlin_heat_twin.domain import HeatSnapshot, ThermalArea

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = {
    "README.md",
    "docs/architecture.md",
    "docs/data-sources.md",
    "docs/data-model.md",
    "docs/heat-methodology.md",
    "docs/validation.md",
    "docs/integration.md",
    "docs/testing.md",
    "docs/limitations.md",
}
REQUIRED_API_PATHS = {
    "/api/v1/health",
    "/api/v1/sources",
    "/api/v1/climate/query/point",
    "/api/v1/climate/query/polygon",
    "/api/v1/weather/observations",
    "/api/v1/heat/state",
    "/api/v1/heat/areas",
    "/api/v1/heat/snapshot",
    "/api/v1/analytics/area-summary",
    "/api/v1/analytics/numeric-summary",
    "/api/v1/analytics/grouped-area-summary",
    "/api/v1/analytics/station-climate-overlap",
    "/api/v1/heat/scenario",
}


def audit_required_files() -> None:
    missing = sorted(path for path in REQUIRED_DOCS if not (ROOT / path).is_file())
    if missing:
        raise RuntimeError(f"required documentation missing: {missing}")


def audit_placeholders() -> None:
    markers = ("TO" + "DO", "FIX" + "ME", "PLACE" + "HOLDER")
    findings: list[str] = []
    for root in (ROOT / "src", ROOT / "frontend" / "src", ROOT / "scripts"):
        for path in root.rglob("*"):
            if not path.is_file() or path == Path(__file__).resolve():
                continue
            if path.suffix not in {".py", ".js", ".css", ".html"}:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker in text:
                    findings.append(f"{path.relative_to(ROOT)} contains {marker}")
    if findings:
        raise RuntimeError("production placeholders found: " + "; ".join(findings))


def audit_cache() -> None:
    cache = ROOT / "data" / "cache"
    committed_payloads = [
        path.relative_to(ROOT)
        for path in cache.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    ]
    if committed_payloads:
        raise RuntimeError(f"third-party/cache payloads must not be committed: {committed_payloads}")


def audit_schemas() -> None:
    openapi = app.openapi()
    missing_paths = sorted(REQUIRED_API_PATHS - set(openapi.get("paths", {})))
    if missing_paths:
        raise RuntimeError(f"required API paths missing from OpenAPI: {missing_paths}")

    snapshot_schema = HeatSnapshot.model_json_schema()
    thermal_area_schema = ThermalArea.model_json_schema()
    snapshot_required = set(snapshot_schema.get("required", []))
    area_required = set(thermal_area_schema.get("required", []))
    if not {"timestamp", "state", "spatial_coverage", "uncertainty"} <= snapshot_required:
        raise RuntimeError("HeatSnapshot schema is missing required integration fields")
    if not {
        "timestamp",
        "area_id",
        "geometry",
        "indicators",
        "state_type",
        "source",
        "provenance",
        "quality",
    } <= area_required:
        raise RuntimeError("ThermalArea schema is missing required integration fields")


def main() -> None:
    audit_required_files()
    audit_placeholders()
    audit_cache()
    audit_schemas()
    print("Repository audit: VERIFIED")


if __name__ == "__main__":
    main()
