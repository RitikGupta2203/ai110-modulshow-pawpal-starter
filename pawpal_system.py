"""
pawpal_system.py
Logic layer for PawPal+ — all backend classes live here.
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str          # "low" | "medium" | "high"
    pet_name: str = ""     # which pet this task belongs to
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Set is_completed to True."""
        self.is_completed = True

    def __repr__(self) -> str:
        """Return a formatted string showing priority, pet, title, duration, and status."""
        status = "done" if self.is_completed else "pending"
        owner = f"{self.pet_name}'s " if self.pet_name else ""
        return f"[{self.priority.upper()}] {owner}{self.title} ({self.duration_minutes} min) — {status}"


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
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

# Priority order used for sorting — higher index = scheduled first
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """
    Planning engine.
    Selects and orders tasks that fit within the owner's available time,
    then explains the resulting plan.
    """

    def __init__(self, owner: Owner, available_minutes: int = None) -> None:
        self.owner = owner
        # Allow overriding available_minutes at schedule time for what-if scenarios
        self.available_minutes = available_minutes if available_minutes is not None else owner.available_minutes
        self.plan: List[Task] = []

    def build_plan(self) -> None:
        """Sort all pending tasks by priority (then duration) and fill the plan up to the time budget."""
        self.plan = []
        pending = self.owner.get_all_pending_tasks()
        sorted_tasks = sorted(pending, key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes))
        time_used = 0
        for task in sorted_tasks:
            if time_used + task.duration_minutes <= self.available_minutes:
                self.plan.append(task)
                time_used += task.duration_minutes

    def explain_plan(self) -> str:
        """Return a plain-language summary of the plan, including any tasks that didn't fit."""
        if not self.plan:
            return "No plan has been built yet. Call build_plan() first."
        total = self.get_total_duration()
        lines = [
            f"Plan for {self.owner.name} — {total} of {self.available_minutes} min used:\n"
        ]
        for i, task in enumerate(self.plan, start=1):
            lines.append(f"  {i}. {task.title} ({task.pet_name}, {task.duration_minutes} min, priority: {task.priority})")
        skipped = [t for t in self.owner.get_all_pending_tasks() if t not in self.plan]
        if skipped:
            lines.append("\nNot scheduled (didn't fit in time budget):")
            for task in skipped:
                lines.append(f"  - {task.title} ({task.pet_name}, {task.duration_minutes} min)")
        return "\n".join(lines)

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all tasks in the current plan."""
        return sum(task.duration_minutes for task in self.plan)
