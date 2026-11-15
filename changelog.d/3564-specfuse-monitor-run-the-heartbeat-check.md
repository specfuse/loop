---
class: fixed
trace: #3564
---
`specfuse monitor run`: the `heartbeat` check no longer files a `silent-schedule` finding when a timer fires a fraction of a second before its scheduled instant; a heartbeat up to 5 seconds early counts as that firing.
