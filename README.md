# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ goes beyond a simple to-do list. The scheduling engine now includes four algorithmic features:

**Sort by time**
Every task can carry an optional preferred start time (`HH:MM`). The `Scheduler.sort_by_time()` method returns the day's plan ordered by each task's effective start minute — whether that was set by you or assigned automatically by the planner. Tasks with no time preference are filled into gaps between pinned tasks and sorted to the front of any remaining free time.

**Filter by pet or status**
The module-level `filter_tasks(tasks, pet_name, status)` utility lets you slice any task list in one call. Pass a pet name to see only that pet's tasks, `status="pending"` or `status="completed"` to filter by completion, or combine both. The task table in the UI uses the same function behind its filter dropdowns.

**Recurring tasks with automatic due dates**
Tasks can be marked `daily` or `weekly`. When you complete a recurring task via `Pet.mark_task_complete()`, the scheduler immediately creates the next occurrence and calculates its due date using Python's `datetime.timedelta`:
- Daily → `date.today() + timedelta(days=1)`
- Weekly → `date.today() + timedelta(weeks=1)`

The new task is appended to the pet's list automatically — no manual renewal needed.

**Conflict detection with readable warnings**
`Scheduler.detect_conflicts()` checks every pair of scheduled tasks for overlapping time windows using the interval test `A.start < B.end AND B.start < A.end`. `Scheduler.conflict_warnings()` wraps those results into plain-English warning strings that include the exact overlap window, its duration in minutes, and whether the clash is between tasks for the same pet or across different pets. Conflicts are printed in the schedule output and highlighted in the UI — the scheduler never crashes or silently drops a task because of them.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
