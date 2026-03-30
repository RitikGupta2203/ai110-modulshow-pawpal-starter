"""
pawpal_system.py
Logic layer for PawPal+ — all backend classes live here.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str                       # "low" | "medium" | "high"
    pet_name: str = ""                  # stamped by Pet.add_task()
    is_completed: bool = False
    start_time: Optional[int] = None    # user's preferred start, minutes from midnight
                                        # e.g. 480 = 08:00, 900 = 15:00
    recurrence: str = "none"            # "none" | "daily" | "weekly"
    due_date: Optional[date] = None     # date this instance is due; None = no deadline

    def mark_complete(self) -> None:
        """Set is_completed to True."""
        self.is_completed = True

    def end_time(self, assigned_start: Optional[int] = None) -> Optional[int]:
        """
        Return the minute-of-day when this task ends.

        Args:
            assigned_start: Override start minute supplied by the Scheduler
                (stored in ``Scheduler._assigned_times``).  When provided it
                takes precedence over ``self.start_time`` so the Task object
                itself is never mutated by the planning engine.

        Returns:
            The end minute (``effective_start + duration_minutes``), or
            ``None`` if neither an override nor a preferred start time is set.
        """
        effective = assigned_start if assigned_start is not None else self.start_time
        if effective is None:
            return None
        return effective + self.duration_minutes

    def next_occurrence(self) -> "Task":
        """
        Return a fresh pending copy of this task for the next recurrence cycle.

        The new task is identical to this one except ``is_completed`` is reset
        to ``False`` and ``due_date`` is calculated from today via
        ``datetime.timedelta``:

        - ``"daily"``  → ``date.today() + timedelta(days=1)``
        - ``"weekly"`` → ``date.today() + timedelta(weeks=1)``

        The preferred ``start_time`` (time-of-day slot) is carried forward so
        the spawned task lands in the same slot on its next run.

        Returns:
            A new ``Task`` instance that is pending and due on the next cycle.

        Raises:
            ValueError: If ``self.recurrence`` is ``"none"`` — one-off tasks
                cannot produce a next occurrence.
        """
        if self.recurrence == "none":
            raise ValueError(f"Task '{self.title}' is not recurring.")

        _next_due: dict[str, date] = {
            "daily":  date.today() + timedelta(days=1),
            "weekly": date.today() + timedelta(weeks=1),
        }

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            recurrence=self.recurrence,
            start_time=self.start_time,      # carry over the preferred time slot
            due_date=_next_due[self.recurrence],
        )

    def __repr__(self) -> str:
        status = "done" if self.is_completed else "pending"
        owner = f"{self.pet_name}'s " if self.pet_name else ""
        time_str = (
            f" @ {self.start_time // 60:02d}:{self.start_time % 60:02d}"
            if self.start_time is not None
            else ""
        )
        recur_str = f" [{self.recurrence}]" if self.recurrence != "none" else ""
        due_str   = f" due {self.due_date}" if self.due_date is not None else ""
        return (
            f"[{self.priority.upper()}] {owner}{self.title} "
            f"({self.duration_minutes} min){time_str}{recur_str}{due_str} — {status}"
        )


# ---------------------------------------------------------------------------
# filter_tasks  — module-level utility
# ---------------------------------------------------------------------------

def filter_tasks(
    tasks: List[Task],
    pet_name: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Task]:
    """
    Filter a list of tasks by pet name and/or completion status.

    Args:
        tasks:    Source list to filter.
        pet_name: If given, keep only tasks belonging to this pet.
        status:   "pending"   → incomplete tasks only;
                  "completed" → completed tasks only;
                  None        → no status filter (return all).
    Returns:
        A new list containing only the matching tasks.
    """
    result = tasks
    if pet_name is not None:
        result = [t for t in result if t.pet_name == pet_name]
    if status == "pending":
        result = [t for t in result if not t.is_completed]
    elif status == "completed":
        result = [t for t in result if t.is_completed]
    return result


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """An animal with a list of care tasks."""

    name: str
    species: str           # "dog" | "cat" | "other"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Stamp the task with this pet's name and append it to the task list."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        """Return all tasks where is_completed is False."""
        return [task for task in self.tasks if not task.is_completed]

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """
        Mark *task* as complete.  If it is a recurring task, automatically
        create the next occurrence (with a due_date calculated via timedelta)
        and append it to this pet's task list.

        Returns the newly created Task for recurring tasks, or None for
        one-off tasks.

        Args:
            task: A Task that belongs to this pet.
        """
        task.mark_complete()
        if task.recurrence == "none":
            return None
        next_task = task.next_occurrence()
        self.tasks.append(next_task)
        return next_task

    def spawn_recurring_tasks(self) -> List[Task]:
        """
        Bulk-renew all completed recurring tasks on this pet.

        Iterates every task in ``self.tasks``.  For each task that is both
        completed and recurring (``recurrence != "none"``), calls
        ``task.next_occurrence()`` to create a fresh pending copy and appends
        it to ``self.tasks``.

        This is a bulk utility for "end of day" renewal.  For completing a
        single task interactively, prefer ``mark_task_complete()``, which
        auto-spawns immediately on completion.

        Returns:
            A list of the newly created ``Task`` objects (may be empty if no
            completed recurring tasks exist).
        """
        new_tasks: List[Task] = []
        for task in list(self.tasks):
            if task.is_completed and task.recurrence != "none":
                new_tasks.append(task.next_occurrence())
        for t in new_tasks:
            self.tasks.append(t)
        return new_tasks


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """The person using PawPal+, with a time budget and a list of pets."""

    def __init__(self, name: str, available_minutes: int) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Append a Pet to this owner's pet list."""
        self.pets.append(pet)

    def get_all_pending_tasks(self) -> List[Task]:
        """Collect and return pending tasks from every pet in a single flat list."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks

    def get_all_tasks(self) -> List[Task]:
        """Collect and return ALL tasks (pending and completed) from every pet."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """
    Planning engine.

    Responsibilities:
      - build_plan()        : select tasks that fit the time budget, assign
                              start times, and store the ordered plan.
      - sort_by_time()      : return plan tasks sorted by their effective start time.
      - detect_conflicts()  : return overlapping task pairs within the plan.
      - explain_plan()      : human-readable schedule summary.
    """

    def __init__(self, owner: Owner, available_minutes: int = None) -> None:
        """
        Initialise the Scheduler for a given owner.

        Args:
            owner: The ``Owner`` whose pets' tasks will be scheduled.
            available_minutes: Time budget for the day in minutes.  Defaults
                to ``owner.available_minutes`` when omitted, but can be
                overridden here for what-if scenarios without modifying the
                owner object.

        Attributes set:
            plan (List[Task]): Populated by ``build_plan()``.  Empty until
                that method is called.
            _assigned_times (Dict[int, int]): Maps ``id(task)`` to the
                scheduler-assigned start minute so ``Task`` objects are never
                mutated during planning.
        """
        self.owner = owner
        self.available_minutes = (
            available_minutes if available_minutes is not None else owner.available_minutes
        )
        self.plan: List[Task] = []
        # Stores scheduler-assigned start times so Task objects are never mutated.
        # Keys are id(task); values are minutes from midnight.
        self._assigned_times: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _effective_start(self, task: Task) -> Optional[int]:
        """Return the effective start time for a task: scheduler-assigned first, then user-preferred."""
        return self._assigned_times.get(id(task), task.start_time)

    # ------------------------------------------------------------------
    # build_plan
    # ------------------------------------------------------------------

    def build_plan(self) -> None:
        """
        Build the daily schedule in three steps:

        1. Separate pending tasks into *pinned* (task.start_time set by user)
           and *floating* (no preferred time).
        2. Sort pinned tasks by start_time; sort floating tasks by priority
           then duration (shortest first within each priority tier).
        3. Walk the timeline: before each pinned task, greedily insert as many
           floating tasks as fit in the gap.  After all pinned tasks, append
           remaining floating tasks sequentially.

        Start times are stored in self._assigned_times (non-mutating).
        """
        self.plan = []
        self._assigned_times = {}

        pending = self.owner.get_all_pending_tasks()

        pinned = sorted(
            [t for t in pending if t.start_time is not None],
            key=lambda t: t.start_time,
        )
        floating = sorted(
            [t for t in pending if t.start_time is None],
            key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes),
        )

        cursor = 0  # current position in the day (minutes used so far)

        for pinned_task in pinned:
            # Skip only if the pinned task itself exceeds the total budget
            if pinned_task.start_time + pinned_task.duration_minutes > self.available_minutes:
                continue

            # Fill the gap [cursor, pinned_task.start_time) with floating tasks
            # only when the pinned task starts at or after the current cursor
            if pinned_task.start_time >= cursor:
                remaining_floats: List[Task] = []
                for ft in floating:
                    if cursor + ft.duration_minutes <= pinned_task.start_time:
                        self._assigned_times[id(ft)] = cursor
                        self.plan.append(ft)
                        cursor += ft.duration_minutes
                    else:
                        remaining_floats.append(ft)
                floating = remaining_floats

            # Always add the pinned task — overlap with a prior task is intentional
            # and will be reported by detect_conflicts()
            self._assigned_times[id(pinned_task)] = pinned_task.start_time
            self.plan.append(pinned_task)
            # Advance cursor to the end of whichever task finishes later
            cursor = max(cursor, pinned_task.start_time + pinned_task.duration_minutes)

        # Append remaining floating tasks after all pinned tasks
        for ft in floating:
            if cursor + ft.duration_minutes <= self.available_minutes:
                self._assigned_times[id(ft)] = cursor
                self.plan.append(ft)
                cursor += ft.duration_minutes

    # ------------------------------------------------------------------
    # sort_by_time
    # ------------------------------------------------------------------

    def sort_by_time(self) -> List[Task]:
        """
        Return the current plan sorted by effective start time (ascending).

        Tasks are ordered by their scheduled start minute.  Any task whose
        start time cannot be determined (should not normally occur after
        build_plan) is placed at the end.

        Returns:
            A new list — self.plan is not mutated.
        """
        def sort_key(task: Task):
            t = self._effective_start(task)
            # None-safe: push unscheduled tasks to the bottom
            return (t is None, t if t is not None else 0)

        return sorted(self.plan, key=sort_key)

    # ------------------------------------------------------------------
    # detect_conflicts
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[Tuple[Task, Task]]:
        """
        Detect all pairs of planned tasks whose time windows overlap.

        Uses the standard interval-overlap test: two half-open intervals
        ``[A.start, A.end)`` and ``[B.start, B.end)`` intersect when::

            A.start < B.end  AND  B.start < A.end

        Back-to-back tasks (one ends exactly when the next begins) are
        *not* considered conflicts.  Only tasks whose effective start time
        can be determined (see ``_effective_start``) are included in the
        check; tasks without a resolvable start time are silently skipped.

        Complexity: O(n²) over the number of timed tasks in the plan.
        Acceptable for typical household pet-care schedules (< 50 tasks).

        Returns:
            A list of ``(task_a, task_b)`` tuples, one per overlapping pair.
            Returns an empty list when the schedule is conflict-free.
            For human-readable descriptions of each conflict, call
            ``conflict_warnings()`` instead.
        """
        conflicts: List[Tuple[Task, Task]] = []
        timed = [t for t in self.plan if self._effective_start(t) is not None]

        for i, a in enumerate(timed):
            a_start = self._effective_start(a)
            a_end = a_start + a.duration_minutes
            for b in timed[i + 1:]:
                b_start = self._effective_start(b)
                b_end = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))

        return conflicts

    # ------------------------------------------------------------------
    # conflict_warnings
    # ------------------------------------------------------------------

    def conflict_warnings(self) -> List[str]:
        """
        Return one human-readable warning string per scheduling conflict.

        Lightweight strategy — never raises; gracefully skips any pair
        whose start time cannot be determined.  Each warning includes:
          - both task titles and pet names
          - the exact time window of each task (HH:MM–HH:MM)
          - the length of the overlap in minutes
          - whether the conflict is within the same pet or across pets

        Returns:
            A (possibly empty) list of warning strings.  An empty list
            means the schedule is conflict-free.
        """
        # Defined once here rather than inside the loop — same behaviour,
        # avoids recreating the function object on every iteration.
        def _fmt(minutes: int) -> str:
            h, m = divmod(minutes, 60)
            return f"{h:02d}:{m:02d}"

        warnings: List[str] = []

        for a, b in self.detect_conflicts():
            a_start = self._effective_start(a)
            b_start = self._effective_start(b)

            # Guard: skip if either start time is unavailable (should not
            # happen after build_plan, but keeps the method non-crashing)
            if a_start is None or b_start is None:
                continue

            a_end = a_start + a.duration_minutes
            b_end = b_start + b.duration_minutes

            # Named variables make the overlap arithmetic easy to follow
            overlap_start = max(a_start, b_start)
            overlap_end   = min(a_end,   b_end)
            overlap_mins  = overlap_end - overlap_start

            scope = "same pet" if a.pet_name == b.pet_name else "cross-pet"

            warnings.append(
                f"WARNING ({scope}): '{a.title}' [{a.pet_name}] "
                f"{_fmt(a_start)}–{_fmt(a_end)} "
                f"overlaps '{b.title}' [{b.pet_name}] "
                f"{_fmt(b_start)}–{_fmt(b_end)} "
                f"— {overlap_mins} min overlap "
                f"({_fmt(overlap_start)}–{_fmt(overlap_end)})"
            )

        return warnings

    # ------------------------------------------------------------------
    # explain_plan
    # ------------------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a plain-language summary of the plan, including conflicts and skipped tasks."""
        if not self.plan:
            return "No plan has been built yet. Call build_plan() first."

        total = self.get_total_duration()
        lines = [
            f"Plan for {self.owner.name} — {total} of {self.available_minutes} min used:\n"
        ]

        for i, task in enumerate(self.sort_by_time(), start=1):
            start = self._effective_start(task)
            time_str = ""
            if start is not None:
                h, m = divmod(start, 60)
                time_str = f" @ {h:02d}:{m:02d}"
            recur_str = f" [{task.recurrence}]" if task.recurrence != "none" else ""
            lines.append(
                f"  {i}. {task.title} ({task.pet_name}, {task.duration_minutes} min,"
                f" priority: {task.priority}){time_str}{recur_str}"
            )

        warnings = self.conflict_warnings()
        if warnings:
            lines.append("\n! Conflicts detected:")
            for w in warnings:
                lines.append(f"  {w}")

        skipped = [t for t in self.owner.get_all_pending_tasks() if t not in self.plan]
        if skipped:
            lines.append("\nNot scheduled (didn't fit in time budget):")
            for task in skipped:
                lines.append(
                    f"  - {task.title} ({task.pet_name}, {task.duration_minutes} min)"
                )

        return "\n".join(lines)

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all tasks in the current plan."""
        return sum(task.duration_minutes for task in self.plan)
