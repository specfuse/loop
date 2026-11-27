---
class: fixed
trace: #3616
---
A guard refusal that keeps the tree no longer crashes the driver when the attempt created a file with a non-ASCII name: untracked paths are read NUL-separated, so git no longer receives a quoted name.
