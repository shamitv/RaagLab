# D01 plan: host preparation

Reuse the existing Docker Engine inside the reference host. Configure only the NVIDIA
container runtime needed for GPU containers, preserve the Windows-provided WSL
driver integration, validate host/WSL/container/framework device access, and keep
model/output volumes outside Git. Do not install a second Docker engine or Linux
display driver.

Exit gate: Docker/Compose resolve, GPU passthrough and framework allocation pass,
storage has sufficient space, and the selected image can run its preflight.
