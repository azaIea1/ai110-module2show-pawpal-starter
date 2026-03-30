"""Scheduler — algorithmic engine that organises pet-care tasks.

Algorithmic features implemented
---------------------------------
1. sort_tasks_by_priority   – Orders tasks across all pets by priority weight
                               (high → medium → low), with due-time as tiebreaker.
2. sort_tasks_by_due_time   – Orders tasks by their scheduled start time;
                               tasks without a due_time appear last.
3. filter_tasks             – Flexible filter by completion status and/or task type,
                               optionally scoped to a single pet.
4. detect_conflicts         – Finds all pairs of overlapping tasks within the owner's
                               schedule (time-collision detection).
5. next_available_slot      – [STRETCH] Scans existing occupied blocks and returns
                               the earliest free window of a given duration.
6. generate_daily_schedule  – [STRETCH] Assigns every pending task to a conflict-free
                               time block, respecting priority order and time bounds
                               (time-blocking to prevent overlapping tasks).
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .task import Task

if TYPE_CHECKING:
    from .owner import Owner
    from .pet import Pet


class Scheduler:
    """Manages and optimises the task schedule for an owner's pets."""

    _PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: "Owner") -> None:
        """
        Args:
            owner: The Owner whose pets and tasks this scheduler manages.
        """
        self.owner = owner

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _all_pending(self, pet: "Pet | None" = None) -> list[tuple["Pet", Task]]:
        """Return (pet, task) pairs for pending tasks, optionally scoped to *pet*."""
        if pet is not None:
            return [(pet, t) for t in pet.get_pending_tasks()]
        return self.owner.get_all_pending_tasks()

    def _all_tasks(self, pet: "Pet | None" = None) -> list[tuple["Pet", Task]]:
        """Return (pet, task) pairs for *all* tasks, optionally scoped to *pet*."""
        if pet is not None:
            return [(pet, t) for t in pet.list_tasks()]
        return self.owner.get_all_tasks()

    # ------------------------------------------------------------------
    # Algorithmic Feature 1 — Sort by priority
    # ------------------------------------------------------------------

    def sort_tasks_by_priority(
        self, pet: "Pet | None" = None, pending_only: bool = True
    ) -> list[tuple["Pet", Task]]:
        """Return tasks sorted high → medium → low.

        Within the same priority, tasks with earlier due times appear first;
        tasks with no due time go last within their priority bucket.

        Args:
            pet:          Restrict to a single pet. None = all pets.
            pending_only: If True, only include incomplete tasks.
        """
        source = self._all_pending(pet) if pending_only else self._all_tasks(pet)

        def sort_key(pair: tuple["Pet", Task]):
            _, task = pair
            rank = self._PRIORITY_RANK.get(task.priority, 1)
            time_val = task.start_minutes() if task.due_time else 9_999
            return (rank, time_val)

        return sorted(source, key=sort_key)

    # ------------------------------------------------------------------
    # Algorithmic Feature 2 — Sort by due time
    # ------------------------------------------------------------------

    def sort_tasks_by_due_time(
        self, pet: "Pet | None" = None, pending_only: bool = True
    ) -> list[tuple["Pet", Task]]:
        """Return tasks ordered by their scheduled start time (earliest first).

        Tasks with no due_time are placed at the end of the list.

        Args:
            pet:          Restrict to a single pet. None = all pets.
            pending_only: If True, only include incomplete tasks.
        """
        source = self._all_pending(pet) if pending_only else self._all_tasks(pet)

        def sort_key(pair: tuple["Pet", Task]):
            _, task = pair
            return task.start_minutes() if task.due_time else 9_999

        return sorted(source, key=sort_key)

    # ------------------------------------------------------------------
    # Algorithmic Feature 3 — Filter tasks
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        status: str | None = None,
        task_type: str | None = None,
        pet: "Pet | None" = None,
    ) -> list[tuple["Pet", Task]]:
        """Return tasks that match every supplied filter criterion.

        Args:
            status:    "pending" | "completed" | None (no filter).
            task_type: A task_type string (e.g. "walk") | None (no filter).
            pet:       Restrict to a single pet | None (all pets).

        Returns:
            Filtered list of (pet, task) pairs.
        """
        source = self._all_tasks(pet)
        result = []
        for p, task in source:
            if status == "pending" and task.completed:
                continue
            if status == "completed" and not task.completed:
                continue
            if task_type is not None and task.task_type != task_type:
                continue
            result.append((p, task))
        return result

    # ------------------------------------------------------------------
    # Algorithmic Feature 4 — Detect scheduling conflicts
    # ------------------------------------------------------------------

    def detect_conflicts(
        self, pet: "Pet | None" = None
    ) -> list[tuple["Pet", Task, "Pet", Task]]:
        """Find all pairs of tasks whose time windows overlap.

        Since the owner can only do one thing at a time, two tasks that
        overlap in time — even across different pets — constitute a conflict.

        Args:
            pet: Restrict conflict search to a single pet. None = all pets.

        Returns:
            List of 4-tuples (pet_a, task_a, pet_b, task_b) for each conflict.
        """
        source = self._all_tasks(pet)
        conflicts: list[tuple["Pet", Task, "Pet", Task]] = []

        for i in range(len(source)):
            for j in range(i + 1, len(source)):
                p_a, t_a = source[i]
                p_b, t_b = source[j]
                if t_a.overlaps_with(t_b):
                    conflicts.append((p_a, t_a, p_b, t_b))

        return conflicts

    # ------------------------------------------------------------------
    # Algorithmic Feature 5 (STRETCH) — Next available time slot
    # ------------------------------------------------------------------

    def next_available_slot(
        self,
        duration_minutes: int,
        start_after: str = "06:00",
        end_before: str = "22:00",
        pet: "Pet | None" = None,
    ) -> str | None:
        """Find the earliest free block of *duration_minutes* minutes.

        Scans the owner's existing task schedule and identifies the first
        contiguous gap of sufficient length, starting at or after *start_after*.

        Args:
            duration_minutes: Minimum required free time (minutes).
            start_after:      Earliest acceptable start time ("HH:MM").
            end_before:       Hard deadline — slot must end before this ("HH:MM").
            pet:              Restrict search to a single pet's tasks. None = all.

        Returns:
            Start time of the next free slot as "HH:MM", or None if not found.
        """
        start_mins = Task._to_minutes(start_after)
        end_mins = Task._to_minutes(end_before)

        # Build list of occupied blocks from tasks that have a due_time
        occupied: list[tuple[int, int]] = []
        for _, task in self._all_tasks(pet):
            if task.due_time:
                t_start = task.start_minutes()
                t_end = task.end_minutes()
                occupied.append((t_start, t_end))
        occupied.sort()

        candidate = start_mins
        while candidate + duration_minutes <= end_mins:
            slot_end = candidate + duration_minutes
            pushed = False
            for occ_start, occ_end in occupied:
                if candidate < occ_end and occ_start < slot_end:
                    candidate = occ_end  # jump past the occupied block
                    pushed = True
                    break
            if not pushed:
                return Task._from_minutes(candidate)

        return None  # no slot found within the day

    # ------------------------------------------------------------------
    # Algorithmic Feature 6 (STRETCH) — Generate conflict-free daily schedule
    # ------------------------------------------------------------------

    def generate_daily_schedule(
        self,
        start_time: str = "08:00",
        end_time: str = "20:00",
    ) -> list[tuple["Pet", Task, str]]:
        """Build a conflict-free daily schedule using priority-based time-blocking.

        Algorithm:
          1. Collect all pending tasks across every pet.
          2. Sort by priority (high first), then by preferred due_time.
          3. For each task, attempt to place it at its preferred due_time; if
             that slot is occupied, slide it forward to the next free window.
          4. Tasks that cannot fit within [start_time, end_time] are skipped.

        The result is a time-blocked schedule with no overlapping tasks — an
        owner can only be in one place at a time.

        Args:
            start_time: Earliest permitted task start ("HH:MM", default 08:00).
            end_time:   Latest permitted task end   ("HH:MM", default 20:00).

        Returns:
            List of (pet, task, assigned_start_time) tuples, in chronological order.
        """
        start_mins = Task._to_minutes(start_time)
        end_mins = Task._to_minutes(end_time)

        # Gather and sort pending tasks by priority, then preferred time
        all_pending = self._all_pending()
        all_pending.sort(
            key=lambda pt: (
                self._PRIORITY_RANK.get(pt[1].priority, 1),
                pt[1].start_minutes() if pt[1].due_time else 9_999,
            )
        )

        schedule: list[tuple["Pet", Task, str]] = []
        occupied: list[tuple[int, int]] = []  # (start, end) in minutes

        for pet, task in all_pending:
            duration = task.duration_minutes
            # Preferred start: honour due_time if set, else use schedule start
            preferred = task.start_minutes() if task.due_time else start_mins
            candidate = max(preferred, start_mins)

            # Slide forward past any conflicting occupied block
            while candidate + duration <= end_mins:
                slot_end = candidate + duration
                conflict = False
                for occ_start, occ_end in occupied:
                    if candidate < occ_end and occ_start < slot_end:
                        candidate = occ_end
                        conflict = True
                        break
                if not conflict:
                    break

            if candidate + duration > end_mins:
                continue  # task doesn't fit — skip it

            assigned = Task._from_minutes(candidate)
            occupied.append((candidate, candidate + duration))
            occupied.sort()
            schedule.append((pet, task, assigned))

        # Return in chronological order
        schedule.sort(key=lambda tup: Task._to_minutes(tup[2]))
        return schedule
