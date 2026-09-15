# Reference deployment inventory

## Verified platform class

The dated deployment checks used Ubuntu under WSL2 with a Linux Docker Engine,
Docker Compose, NVIDIA container support, and a compatible NVIDIA GPU. Host
memory, storage, GPU capacity, and driver compatibility met the bounded test
gates. Exact host identity, paths, hardware inventory, and capacity figures are
kept in the ignored local machine record.

No application port was listening before deployment, and no disposable test
container remained after the standalone verification.

## Topology and storage

Docker Engine ran inside the Linux environment. Model weights and generated
outputs used Docker named volumes outside the repository and image layers. The
managed application used separate database, broker, and artifact volumes.

Record the following per-host values by copying
[`local-machine.template.md`](../../local-machine.template.md) to the ignored
local documentation area:

- Repository and deployment roots.
- Host connection method and container context.
- Compose project and model-volume names.
- Device selection, local ports, and resource limits.
- Evidence, backup, and recovery locations.

No credentials, tokens, model weights, or generated media belong in tracked
inventory documents.

## Evidence boundary

Tracked evidence retains dates, versions, acceptance outcomes, and capability
limits. Machine identifiers and host-only measurements are retained locally.
The standalone model authors recommend substantial accelerator memory, so the
verified result remains a bounded, single-request feasibility result rather
than a general throughput claim.
