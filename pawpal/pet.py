"""Pet — an animal with a list of care tasks."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .task import Task

SPECIES_EMOJI: dict[str, str] = {
    "dog": "🐶",
    "cat": "🐱",
    "bird": "🐦",
    "rabbit": "🐰",
    "fish": "🐟",
    "hamster": "🐹",
    "other": "🐾",
}


class Pet:
    """Represents a pet belonging to an owner."""

    def __init__(self, name: str, species: str, age: int = 0) -> None:
        """
        Args:
            name:    Pet's name.
            species: e.g. "dog", "cat", "bird" — used for emoji display.
            age:     Age in years (0 = unknown/not set).
        """
        self.name = name
        self.species = species.lower()
        self.age = max(0, age)
        self.tasks: list["Task"] = []

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: "Task") -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task whose description matches (case-insensitive).

        Returns True if a task was removed, False otherwise.
        """
        for i, t in enumerate(self.tasks):
            if t.description.lower() == description.lower():
                self.tasks.pop(i)
                return True
        return False

    def list_tasks(self) -> list["Task"]:
        """Return all tasks (completed and pending)."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list["Task"]:
        """Return only incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list["Task"]:
        """Return only completed tasks."""
        return [t for t in self.tasks if t.completed]

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @property
    def species_emoji(self) -> str:
        return SPECIES_EMOJI.get(self.species, "🐾")

    def __repr__(self) -> str:
        return (
            f"{self.species_emoji} {self.name} ({self.species}, {self.age}yr) "
            f"— {len(self.tasks)} task(s)"
        )
