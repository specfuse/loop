---
class: fixed
trace: #3579
---
`specfuse monitor run` no longer crashes with `TruncatedListingError` once a repo holds 100+ finding issues: the listing limit is raised to 2000, and a filing error is now reported per component instead of aborting the whole run
