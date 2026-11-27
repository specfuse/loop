---
class: changed
trace: #3620
---
A terminal close whose judge gives no verdict (timed out, could not run, unreadable output, or a defect in its path) no longer finishes the feature on its own met: the terminal flips are withheld and the run halts with judge_unavailable_terminal. The judge timeout is now 30 minutes.
