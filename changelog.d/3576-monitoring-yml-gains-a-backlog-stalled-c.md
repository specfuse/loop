---
class: added
trace: #3576
---
monitoring.yml gains a backlog-stalled check type: a component reports each work queue it keeps in its own data store (outbox or job table) as a BacklogSnapshot event, and the App Insights adapter files one finding per backlog when its oldest pending item passes stall_after, or when no snapshot arrives within the optional silent_after. The emission contract is in design-for-diagnosis.md, and /derive-monitoring proposes a target per discovered backlog or flags a missing emission.
