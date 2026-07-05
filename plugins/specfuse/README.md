# specfuse plugin

The Specfuse gate-cycle methodology's Claude Code skills, installed via the
[`specfuse`](../../) marketplace and namespaced under `/specfuse:`.

```
/plugin marketplace add specfuse/specfuse
/plugin install specfuse@specfuse
```

## Skills (by lifecycle phase)

- **Pick** — `/specfuse:pick-feature`, `/specfuse:roadmap-add`
- **Draft** — `/specfuse:draft-feature`, `authoring-work-units` (reference),
  `/specfuse:derive-verification`
- **Arm** — `/specfuse:arm-gate`
- **Diagnose** — `/specfuse:gate-status`, `/specfuse:unblock-wu`,
  `/specfuse:abandon-feature`
- **Wrap** — `/specfuse:wrap-feature`, `/specfuse:roadmap-archive`
- **Cross-cutting** — `verification`, `/specfuse:fix-bug`,
  `/specfuse:feature-conversion`, `/specfuse:learnings-suggest`,
  `/specfuse:learnings-curate`, `/specfuse:adopt-feature`,
  `/specfuse:migrate-to-auto-close`

See [specfuse/loop `docs/skills.md`](https://github.com/specfuse/loop/blob/main/docs/skills.md)
for the full catalog and [`docs/methodology.md`](https://github.com/specfuse/loop/blob/main/docs/methodology.md)
for the contracts these skills manipulate.

## Driver

These skills drive the **specfuse-loop** driver:

```
pip install specfuse-loop
```

## License

Apache License 2.0. See [`../../LICENSE`](../../LICENSE).
