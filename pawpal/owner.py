"""Owner — a person who owns one or more pets."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pet import Pet
    from .task import Task


class Owner:
    """Represents a pet owner with a collection of pets."""

    def __init__(self, name: str, email: str = "") -> None:
        """
        Args:
            name:  Owner's display name.
            email: Optional contact e-mail.
        """
        self.name = name
        self.email = email
        self.pets: list["Pet"] = []

    # ------------------------------------------------------------------
    # Pet management
    # ------------------------------------------------------------------

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet to this owner's roster."""
        self.pets.append(pet)

    def get_pet_by_name(self, name: str) -> "Pet | None":
        """Return the first pet whose name matches (case-insensitive), or None."""
        for p in self.pets:
            if p.name.lower() == name.lower():
                return p
        return None

    def list_pets(self) -> list["Pet"]:
        """Return all pets belonging to this owner."""
        return list(self.pets)

    # ------------------------------------------------------------------
    # Cross-pet task access
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[tuple["Pet", "Task"]]:
        """Return (pet, task) pairs for every task across all pets."""
        result: list[tuple["Pet", "Task"]] = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet, task))
        return result

    def get_all_pending_tasks(self) -> list[tuple["Pet", "Task"]]:
        """Return (pet, task) pairs for every *pending* task across all pets."""
        return [(pet, task) for pet, task in self.get_all_tasks() if not task.completed]

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        contact = f" <{self.email}>" if self.email else ""
        return f"👤 {self.name}{contact} — {len(self.pets)} pet(s)"
