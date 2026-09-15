# Interrupted final-HEAD rerun

- Run: `phase6-20260915-092521-5d8d8503`
- Candidate: `4b2d42599168925a4771dfc61901c4ad5456abd2`
- Action: the user stopped the second full `--real-cpu` invocation before model startup.
- Cleanup: owned project `museforge-phase6-test-b67a42bbe8` was label-checked and
  removed with its disposable volumes; the external
  `musicgen-yue2-test_weights` volume and both existing deployments were kept.
- Retention: the partial run directory remains under the ignored local
  `test-results/` tree; no generated audio, weights, secrets, or disposable
  Compose state is tracked.

The final browser-profile correction was separately verified by the targeted
browser run documented in [README](README.md), so the expensive model execution
was not repeated after a profile-only change.
