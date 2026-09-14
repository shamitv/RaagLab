# D03 plan: real model

Package YuE2-3B in a separate real-worker image with immutable model/VAE revisions,
persistent acquisition, isolated dependencies, and GPU process lifecycle. Keep the
API/mock images light and retain the mock queue for diagnostics. Add a concrete
MuseForge adapter that maps the existing generation contract to YuE2's style and
lyrics request, reports unsupported controls accurately, validates/publishes the
48 kHz stereo result, and persists model provenance.

The standalone checkpoint is a prerequisite and is complete. The D03 exit gate is
stricter: at least one real request from the actual application must cross the
database/outbox, broker, and real worker, then persist and be retrieved through the
API. A standalone model command cannot close D03.
