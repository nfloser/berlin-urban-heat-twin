# Limitations

- DWD observations are sparse point measurements. The project does not produce an unvalidated continuous live Berlin temperature surface.
- Official Berlin climate layers represent the methodology/reference state documented by the Environmental Atlas, not instantaneous observations.
- The initial live DWD adapter covers hourly 2 m temperature and relative humidity. Other variables require separate documented products/adapters.
- Dynamic PET/UTCI are not calculated from incomplete inputs.
- Environmental-justice dimensions must remain separate from thermal burden unless a documented derived index is intentionally constructed.
- The project does not infer causality between heat and energy, mobility or infrastructure outcomes.
- Live provider availability is external and can change; discovery and station metadata are queried rather than assumed permanent.
- Any cache may become stale. `HeatSnapshot` reports observation freshness and quality.
