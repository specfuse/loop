---
class: fixed
trace: #3628
---
A pinned driver run started on another branch (with or without --prepare) no longer commits its build-pin record there: the record is written once the run is on the feature branch, and a --prepare-only run records none.
