# Validation

## What is validated now

Automated tests validate parsing, timezone handling, units/ranges, missing values, WFS capabilities, GeoJSON geometry validity, CRS transformation, metric-area safeguards, temporal selection, classification boundaries, snapshot contracts and scenario labelling.

## Spatial/dynamic model validation

No city-wide dynamic temperature model is currently fitted, so RMSE, MAE and R² are **not applicable and are not reported**.

If a spatial estimator is introduced later, validation must hold out stations and use spatial and time-based evaluation without leakage. Metrics may only be published from actual runs against real observations.

## Live provider verification

A local execution environment without outbound network access can run all deterministic tests but cannot prove that current WFS and DWD endpoints are reachable. Live ingestion should therefore be exercised in CI or an operator environment with network access and recorded separately from unit-test success.
