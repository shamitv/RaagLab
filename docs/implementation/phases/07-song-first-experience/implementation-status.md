# Phase 07 implementation status

- State: completed

The song routes, QR configuration, product README, create-only mode, restart policy, and early port check are implemented. Python unit tests passed 189 with six documented environment skips; frontend tests and build passed; mock generation, persistence across rebuild, QR decode, and desktop/mobile Chromium checks passed.

The portable setup and start entry points now default to the real YuE2 provider. Passing `mock` explicitly creates and starts the isolated mock configuration, even when an existing environment contains real-provider values. Provider-specific logging, stopped creation, and automatic CUDA overlay selection follow the same resolved mode.
