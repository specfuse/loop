---
class: fixed
trace: #3602
---
A work unit left `in_progress` by a killed run is now reset to `pending` and dispatched by the next `specfuse run`, instead of halting the gate until the operator resets it by hand.
