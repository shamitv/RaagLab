# Dependency support and security review — 2026-09-15

This review covers the exact pins used by the Phase 06 candidate. It checks
official support/lifecycle pages and the release notes for the versions visible
in the committed evidence. No dependency pin changed; the existing lockfiles,
image digests, and model manifest remain the reproducibility source of truth.

| Component | Candidate pin / observation | Official review | Decision |
| --- | --- | --- | --- |
| Python | 3.13.15 | Python 3.13 is in the bugfix-support line with end of life in 2029. See [Python version status](https://devguide.python.org/versions/). | Keep pin. |
| Node.js/npm | 24.21.0 / 11.19.0 | Node 24 is listed as LTS; production use is intended for Active or Maintenance LTS releases. See [Node release schedule](https://nodejs.org/en/about/previous-releases). | Keep pin. |
| Docker Engine | 29.8.0 on Ubuntu1 | The official 29.8.0 notes include the current 29.x fixes; the release notes also document security fixes in the 29.x line. See [Docker Engine 29 release notes](https://docs.docker.com/engine/release-notes/29/). | Keep host version for this run; recheck before future release. |
| Docker Compose | 5.5.1 | Compose documentation and [release notes](https://docs.docker.com/compose/release-notes/) remain the authoritative compatibility source. | Keep installed plugin. |
| PostgreSQL | 18.6 image digest | PostgreSQL 18.6 is listed as supported through 2030; minor releases carry bug and security fixes. See [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/). | Keep pinned digest; follow current minor releases. |
| RabbitMQ | 4.3.5 image digest | RabbitMQ 4.3.5 is the current 4.3 patch in the official table, with community support through 2026-11-30. See [RabbitMQ release information](https://www.rabbitmq.com/release-information). | Keep for this release; schedule review before community-support end. |
| PyTorch runtime | frozen in `packaging/yue2/requirements.museforge.lock` | Official install guidance requires Python 3.9 or later, compatible with the pinned Python 3.13 runtime. See [PyTorch Start Locally](https://docs.pytorch.org/get-started/locally/). | Keep lock; CPU/torch-eager acceptance passed. |

## Verification record

- `uv.lock`, `apps/web/package-lock.json`,
  `packaging/yue2/requirements.museforge.lock`, and
  `packaging/yue2/model-lock.json` were hashed in the release summary.
- Docker image IDs/digests, Compose version, container Python 3.13.15, and
  container Node 24.21.0 were captured in the mock release evidence.
- The CPU evidence records model revision `29b3558dd46954a0cd9021dc76d5c91864a0f1c7`,
  decoder revision `9a94e1d0ea9f8087e98f77fa88df4a4068104d2a`, and provider
  revision `yue2-infer-0.1.6`.
- The review found no support or release-note issue that justified changing a
  pin. A future release should repeat this review and update the RabbitMQ pin
  or support decision before 2026-11-30.
