# Domain Docs

This repo uses a single-context domain-doc layout.

## Before exploring, read these

- `CONTEXT.md` at the repo root for current domain language and invariants.
- `PRD.md` for product requirements, user stories, budget categories, and expected output.
- `ARCHITECTURE.md` for system structure, routes, core modules, and data flow.
- Relevant ADRs under `docs/adr/` when architectural decisions exist.

If an expected file does not exist, proceed silently and use the available references.

## Layout

```text
/
├── CONTEXT.md
├── PRD.md
├── ARCHITECTURE.md
├── docs/
│   ├── adr/
│   └── agents/
└── src/
```

Do not use `CONTEXT-MAP.md` unless this repo becomes a multi-context project.

## Vocabulary Rules

Use the terms from `CONTEXT.md` when writing issues, PRDs, refactor plans, tests, or architecture notes. If a needed term is missing, call out the gap instead of inventing competing language.

## ADR Rules

When a proposed change contradicts an ADR in `docs/adr/`, surface the conflict explicitly and explain whether the ADR should be reopened.
