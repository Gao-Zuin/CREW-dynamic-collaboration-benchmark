# CREW dynamic collaboration benchmark research

This repository preserves the source changes and compact evidence for the CREW-Wildfire dynamic task, scarce worker, and mutable collaboration graph study. It is a source overlay, not a copy of the Unity build or the 11 GB development workspace.

## Layout

- `overlays/ORCH/`: changed or added files relative to the pinned ORCH commit.
- `overlays/WILDFIRE-ORCH/`: changed Unity source relative to its pinned commit.
- `workspace/scripts/`, `workspace/tests/`, `workspace/research/`: study code and notes.
- `workspace/benchmark_runs/`: selected small JSON evidence. Full raw Unity and LLM logs stay in the local workspace.
- `SOURCE_MANIFEST.json`: upstream commits, origins, and SHA-256 for every exported file.

## Recreate the working tree

Clone the upstream repositories at the commits in `SOURCE_MANIFEST.json`, then copy each corresponding overlay into the clone, preserving paths. `workspace/scripts` and `workspace/tests` belong at the root of the assembled CREW workspace. The Unity build, Python environment, and service setup are documented in the workspace notes and are not redistributed here.

To refresh this source repository from the sibling `CREW` workspace:

```bash
python sync_from_workspace.py
git status --short
```

The upstream ORCH and WILDFIRE-ORCH repositories carry the Apache-2.0 license; see `LICENSE.upstream-ORCH`. This export deliberately excludes downloaded papers, model credentials, binaries, environments, and raw run logs.
