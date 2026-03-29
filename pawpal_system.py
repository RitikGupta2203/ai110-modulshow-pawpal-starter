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
        """Mark this task as done."""
        pass

    def __repr__(self) -> str:
        """Return a readable string representation of the task."""
        pass


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
        """Add a care task to this pet's task list."""
        pass

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed yet."""
        pass


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
        """Register a pet to this owner."""
        pass


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
        """
        Collect all pending tasks from every pet, sort by priority then by
        shortest duration as a tiebreaker, and fill the plan up to the
        available_minutes budget.
        Resets self.plan on each call so it is safe to call multiple times.
        """
        self.plan = []
        pass

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why each task in the plan
        was chosen and in what order.
        Returns a message if build_plan has not been called yet.
        """
        if not self.plan:
            return "No plan has been built yet. Call build_plan() first."
        pass

    def get_total_duration(self) -> int:
        """Return the sum of duration_minutes for all tasks currently in the plan."""
        pass
