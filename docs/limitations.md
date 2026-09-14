# Limitations

- DWD observations are sparse point measurements. The project does not render or expose an unvalidated continuous live Berlin temperature surface.
- Official Berlin climate layers represent their documented modelling/reference conditions, not instantaneous observations.
- The current DWD adapter covers the recent hourly 2 m air-temperature and relative-humidity product. Other variables or a climatological history require separate documented adapters.
- Dynamic PET/UTCI are not calculated from incomplete inputs. Official PET/UTCI attributes may be summarized directly when present.
- Long-term temperature anomalies are not computed because no historical baseline adapter/reference period is currently part of this component.
- Area-category totals do not dissolve overlapping source features; overlap can therefore appear in totals when it exists in the source dataset.
- Grouped/district summaries are only as meaningful as the explicit grouping attribute selected from the official source. District membership is never guessed.
- Numeric attribute summaries are feature-based and not automatically area-weighted. The supplied unit must be verified against official source metadata.
- Environmental-justice dimensions remain separate from thermal burden unless a future documented method deliberately combines them.
- The project does not infer causality between heat and energy, mobility, health or infrastructure outcomes.
- Live provider availability is external and can change; WFS layers/schemas and DWD stations are discovered rather than assumed permanent.
- Cached observations can become stale. `HeatSnapshot` reports freshness and quality.
- Software tests validate implementation behaviour; they do not constitute independent scientific validation of Berlin's official climate models.