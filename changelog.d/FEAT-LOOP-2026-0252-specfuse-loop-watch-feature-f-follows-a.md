---
class: added
trace: FEAT-LOOP-2026-0252
---
`specfuse-loop --watch [--feature F]` follows a running driver from a second terminal; it only reads the status file, exits 0 when the run stops and 1 when there is no status file
