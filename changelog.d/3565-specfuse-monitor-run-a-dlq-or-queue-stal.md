---
class: fixed
trace: #3565
---
`specfuse monitor run`: a `dlq` or `queue-stalled` target whose Service Bus subscription does not exist is now skipped and reported in the run summary; the check keeps reading the other targets instead of failing as a whole.
