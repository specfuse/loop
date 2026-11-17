---
class: fixed
trace: #3592
---
`specfuse monitor run`: Azure failure signatures no longer carry per-occurrence tokens — a GUID followed by `_` (the Service Bus `TrackingId:<guid>_B4` shape), `TrackingId`/`SystemTracker`/`Reference`/`LockToken` values, HTTP `Date:` headers, and stack traces embedded by Functions host wrapper exceptions are normalized away, so repeat occurrences of one failure land on one issue instead of one each. Existing findings whose signature changes are filed once more under the new signature.
