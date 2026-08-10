Run the **coder** to build every buildable task across a sprint in dependency order.

## Usage

- `/implement-sprint SPRINT-001` — build the specified sprint
- `/implement-sprint` — build the next `Ready` sprint(s) in `depends_on_sprints`
  order

## What this does

For each target sprint (in `depends_on_sprints` order):

    0. Refuse to start unless all depends_on_sprints are Done.
    1. Set sprint status: In Progress.
    2. Build task queue: all flat-root Tasks whose parent_story is in this sprint,
       topologically ordered by depends_on edges.
    3. Pop the next BUILDABLE task (status: Ready or In Progress, all deps Done).
         - None buildable → go to step 5.
    4. Invoke coder on the task (one task, scope-bounded).
         - Escalates / locked AC fails → mark task Blocked, write escalation +
           REVIEW-QUEUE entry, continue with next buildable task.
         - Succeeds (every locked AC verified) → task Done; update MEMORY/CHANGELOG;
           when all the story's tasks are Done, mark the story Done + update BACKLOG.
         - Go to step 3.
    5. Sprint wrap:
         - All stories Done, nothing blocked → mark sprint Done, draft Retrospective,
           set completed. gate: flagged so the human skims the retro.
         - Anything blocked → sprint stays In Progress; flag with the blocked list.

**Hard rules enforced here:** never halt on a blocked task (route around it); refuse
a sprint whose `depends_on_sprints` are not all `Done`; never edit a `Done` task;
never edit architecture/ADRs/the PRD. The coder may set a sprint `Done` only when
every locked AC across it is verified — and it drafts (does not finalise) the retro;
harvesting patterns into `Implementation/Learnings.md` is the human's step.

**Summary on halt:** tasks Done this run, tasks still Blocked with reasons, an AC
coverage report (every locked AC and whether its tagged step passed), and **explicitly
everything written to `REVIEW-QUEUE.md` / `ESCALATIONS.md`**.
