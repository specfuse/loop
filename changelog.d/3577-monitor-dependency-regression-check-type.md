---
class: added
trace: #3577
---
monitor: `dependency-regression` check type. Within `window_after_deploy` after a deployment, a (dependency type, target) pair with at least `min_failures` failed calls (default 5) and 3x its pre-deploy failure rate files one finding per deployment, read from App Insights `AppDependencies` scoped to the role name and app version. Shares the `deploy_signal` block with `http-status-regression`; `/derive-monitoring` proposes it for components with a version stamp and a data store. Failures only: latency is out of scope by decision.
