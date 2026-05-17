# Architecture Decision Records

Use this directory for Architecture Decision Records (ADRs): short documents that explain decisions with lasting design impact.

## Naming

Name ADR files with a zero-padded sequence number and a short slug:

```text
0001-use-local-json-categorization-rules.md
0002-keep-flask-routes-thin.md
```

## When to Add an ADR

Add an ADR when a change affects long-term structure, core data flow, persistence format, privacy boundaries, parsing strategy, or public behavior that future contributors should not accidentally reverse.

Small implementation details, routine bug fixes, and one-off UI copy changes do not need ADRs.

## Suggested Format

```markdown
# ADR-0001: Title

## Status

Accepted

## Context

What problem or constraint forced a decision?

## Decision

What did we choose?

## Consequences

What tradeoffs, follow-up work, or constraints come from this decision?
```
