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

class Scheduler:
    """
    Planning engine.
    Selects and orders tasks that fit within the owner's available time,
    then explains the resulting plan.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: List[Task] = []

    def build_plan(self) -> None:
        """
        Collect all pending tasks from every pet, sort by priority,
        and fill the plan up to the owner's available_minutes budget.
        """
        pass

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of why each task in the plan
        was chosen and in what order.
        """
        pass

    def get_total_duration(self) -> int:
        """Return the sum of duration_minutes for all tasks currently in the plan."""
        pass
