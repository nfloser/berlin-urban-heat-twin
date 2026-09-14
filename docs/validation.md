# Validation

## Deterministic validation

Automated tests cover:

- DWD station/observation parsing, missing values, ranges and timezone normalization;
- WFS capabilities, `DescribeFeatureType` schema parsing and feature parsing;
- geometry validity, CRS transformation, point and polygon spatial queries;
- projected metric-area safeguards;
- temporal selection and measured-history filtering;
- exact official-class selection and area calculations;
- numeric source-attribute summaries without reclassification;
- station-to-official-area overlap without interpolation;
- integration contracts, scenario labelling and API/OpenAPI routes;
- frontend provenance/state presentation helpers.

Strict Mypy, Ruff linting, Ruff formatting, frontend tests/build, Docker configuration/build and a repository-integrity audit are CI gates.

## Live provider verification

`scripts/live_smoke.py` checks the real configured Berlin WFS services and DWD CDC. It verifies live capabilities, a sample `DescribeFeatureType` schema, multiple sample features, geometry-validity status, `official_modelled` provenance, current DWD station metadata, timezone-aware UTC observations, units/ranges and `observed` provenance.

This external check is separate from deterministic correctness because provider/network availability is outside the repository's control. A failed external check must be reported as `NOT VERIFIED` rather than converted into synthetic data.

## Spatial/dynamic model validation

There is no fitted Berlin-wide dynamic temperature model, so RMSE, MAE and R² are **not applicable and are not reported**. If a spatial estimator is introduced later, stations must be held out with spatial and time-aware validation and metrics may only come from real executed comparisons.

## Scientific interpretation

Passing tests validates software behaviour and source handling; it does not turn official model outputs into ground truth or station measurements into complete spatial coverage. Those limitations remain visible in API responses and UI.