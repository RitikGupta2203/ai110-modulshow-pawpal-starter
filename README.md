# PawPal+

A smart daily pet-care scheduler built with Python and Streamlit. PawPal+ helps pet owners plan their day by prioritising care tasks, detecting schedule conflicts, and automatically renewing recurring routines.

---

## Features

### Priority-based scheduling
Tasks are ranked **high → medium → low** using a greedy, single-pass algorithm (`Scheduler.build_plan()`). Within each priority tier, shorter tasks are placed first to maximise the number of tasks that fit inside the owner's available-time budget. Tasks that don't fit are listed separately in the UI so nothing is silently dropped.

### Pinned vs. floating time slots
Every task can carry an optional preferred start time (e.g. `08:00`). The scheduler separates tasks into *pinned* (user-set start) and *floating* (auto-assigned). Floating tasks are greedily inserted into gaps between pinned tasks; any remaining floaters are appended after the last pinned task. Pinned start times are stored in `Scheduler._assigned_times` so `Task` objects are never mutated during planning.

### Sort by time
`Scheduler.sort_by_time()` returns the day's plan in ascending start-minute order using each task's *effective* start — either its scheduler-assigned slot or its user-set preference. The schedule table in the UI always reflects this sorted view.

### Recurring tasks with automatic due dates
Tasks can be set to `daily` or `weekly` recurrence. Completing a recurring task via `Pet.mark_task_complete()` immediately creates the next pending occurrence with a calculated due date:

| Recurrence | Next due date |
|---|---|
| `daily` | `date.today() + timedelta(days=1)` |
| `weekly` | `date.today() + timedelta(weeks=1)` |

The original start-time preference is carried forward so the spawned task lands in the same time slot. A "Renew recurring tasks" button handles bulk renewal at end of day.

### Conflict detection and readable warnings
`Scheduler.detect_conflicts()` checks every pair of scheduled tasks using the standard interval-overlap test:

```
A.start < B.end  AND  B.start < A.end
```

Back-to-back tasks (one ends exactly when the next begins) are intentionally **not** flagged. `Scheduler.conflict_warnings()` wraps each conflict into a plain-English string that includes exact time windows, overlap duration in minutes, and a `same pet` / `cross-pet` label. Each warning is surfaced as a `st.warning` banner in the UI.

### Filter by pet or status
The module-level `filter_tasks(tasks, pet_name, status)` utility narrows any task list in a single call. The task table's dropdown filters use this function directly. Passing an unknown pet name safely returns an empty list.

---

## 📸 Demo

> **To add your screenshot:** run `streamlit run app.py`, interact with the app, take a screenshot, save it as `docs/demo.png`, then replace the placeholder below.

```
docs/demo.png  ← place your screenshot here
```

![PawPal+ demo screenshot](docs/demo.png)

---

## Getting started

### Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

### Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project structure

```
pawpal_system.py   — all backend logic (Task, Pet, Owner, Scheduler, filter_tasks)
app.py             — Streamlit UI
tests/
  test_pawpal.py   — 30-test pytest suite
uml_final.mmd      — Mermaid class diagram (paste into mermaid.live to render)
```

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest
```

Verbose output (shows each test name):

```bash
python -m pytest -v
```

### What the tests cover

The suite contains **30 tests** across five areas:

| Area | Tests | What is verified |
|---|---|---|
| **Sorting correctness** | 2 | `sort_by_time()` returns tasks in ascending start-minute order; floating tasks receive sequential slot assignments starting at minute 0 |
| **Recurrence logic** | 8 | Completing a `daily` task spawns a new pending copy with `due_date = today + 1 day`; `weekly` tasks advance by 7 days; completing a one-off task returns `None` and adds nothing; calling `next_occurrence()` on a one-off raises `ValueError` |
| **Conflict detection** | 5 | Overlapping windows flagged; back-to-back tasks not flagged; exact same start-minute produces one conflict; cross-pet conflicts labeled separately |
| **Filtering** | 5 | `filter_tasks()` narrows by pet name, status, or both; unknown pet name returns `[]` without error |
| **Core task/pet behavior** | 10 | `mark_complete()` flips status; `add_task()` stamps pet name; `build_plan()` respects time budget and lists skipped tasks |

### Confidence level

**4 / 5 stars** — all 30 tests pass across happy paths and key edge cases (zero-task pets, exact-boundary times, budget overflow). The missing star reflects the absence of UI-layer integration tests and end-to-end persistence scenarios.

---

## Architecture

The class diagram in [`uml_final.mmd`](uml_final.mmd) shows all classes, attributes, methods, and relationships as built. Paste the file contents into [mermaid.live](https://mermaid.live) to render or export as PNG.

**Class responsibilities at a glance:**

| Class | Responsibility |
|---|---|
| `Task` | Single care activity; knows how to produce its next recurrence |
| `Pet` | Owns a task list; completes tasks and spawns recurring copies |
| `Owner` | Holds pets and the day's time budget |
| `Scheduler` | Builds, sorts, and analyses the daily plan without mutating tasks |
| `filter_tasks` | Module-level utility to slice task lists by pet or status |
