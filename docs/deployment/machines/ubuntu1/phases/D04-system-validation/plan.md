# D04 plan: system validation

After D02 and D03 pass, validate the real provider through the API-served browser:
capabilities/readiness, asynchronous jobs, playback/seek/download, iteration,
refresh/reopen, cancellation, worker loss, restart, artifact persistence, and
resource bounds. Use mock fault injection where it gives stronger repeatable
recovery evidence, and label provider mode for every check.
