---
class: changed
trace: #3578
---
Monitoring scope: a component data store is monitored through the component, never directly. The design-for-diagnosis rule and the monitoring schema doc state the boundary, and derive-monitoring audits data-store components for owned signals (data-store-signals) and routes platform health to infrastructure alerting.
