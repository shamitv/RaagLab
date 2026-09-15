# Local machine documentation template

Tracked documentation is machine-neutral. Copy this template to
`.local/docs/machine.md` and fill it in locally; `.local/` is ignored by Git.
Never link tracked documentation to the local file.

## Workspaces and host

- Repository root: `<repository-root>`
- Deployment host or VM alias: `<deployment-host>`
- Host connection method: `<local-shell-or-remote-endpoint>`
- Platform: `<linux-or-wsl2>`
- Container engine/context: `<engine-and-context>`

## Managed deployment values

```bash
export MUSEFORGE_DEPLOY_ROOT="<deployment-root>"
export MUSEFORGE_PROJECT_NAME="<compose-project>"
export MUSEFORGE_EVIDENCE_ROOT="<evidence-root>"
export MUSEFORGE_BACKUP_ROOT="<backup-root>"
export MUSEFORGE_YUE2_WEIGHTS_VOLUME="<weights-volume>"
export MUSEFORGE_YUE2_OUTPUTS_VOLUME="<outputs-volume>"
```

Record local ports, model-volume names, device selection, resource limits,
backup locations, and recovery commands here. Do not commit the completed copy.

## Verification history

Record exact host inventory, generated resource names, evidence paths, and live
deployment state here. Keep tracked reports limited to portable commands,
dated acceptance outcomes, and non-identifying capability limitations.
