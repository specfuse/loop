---
class: fixed
trace: #3585
---
`scripts/sync-scaffold.sh` now copies the packaged docs into `specfuse/loop/data/docs/`; the docs list lives in `scripts/sync-scaffold-docs.txt`, which the drift test reads too, so editing a doc and running the sync clears the drift guard
