Run the **designer** agent to author or update the clickable `html-prototype/`
prototype for a requirement batch.

## Usage

`/design REQ-SB-01 REQ-SB-02`

Always pass explicit requirement IDs. Scoped batches; bare invocation not supported
(design without context produces inconsistent output).

## What this does

1. Read `Implementation/Pipeline.md`.
2. Invoke the designer agent (subagent_type: designer).
3. The designer reads the scoped PRD sections + existing prototype + design system.
4. Authors/updates `html-prototype/` screens for the requirement batch.
5. ALWAYS adds a `REVIEW-QUEUE.md` entry for human browser sign-off.
6. Never auto-advances.

**This is a design-first precursor — run BEFORE `/spec` on the same requirements.**
The analyst will reconcile each story against the approved prototype screens.
