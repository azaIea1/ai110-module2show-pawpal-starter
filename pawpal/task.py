"""Task — a single pet-care action with scheduling metadata."""

from __future__ import annotations


class Task:
    """Represents a pet-care task with a due time, duration, and priority."""

    PRIORITY_ORDER: dict[str, int] = {"high": 3, "medium": 2, "low": 1}

    TASK_EMOJIS: dict[str, str] = {
        "feeding": "🍖",
        "walk": "🦮",
        "medication": "💊",
        "grooming": "✂️",
        "play": "🎾",
        "vet": "🏥",
        "other": "📋",
    }

    PRIORITY_EMOJI: dict[str, str] = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
    }

    def __init__(
        self,
        description: str,
        due_time: str | None,
        duration_minutes: int,
        priority: str = "medium",
        task_type: str = "other",
        recurring: bool = False,
    ) -> None:
        """
        Args:
            description:       Human-readable label for the task.
            due_time:          Scheduled start time as "HH:MM" string, or None.
            duration_minutes:  How long the task takes (≥ 1).
            priority:          One of "low", "medium", "high".
            task_type:         One of the keys in TASK_EMOJIS.
            recurring:         Whether the task repeats daily.
        """
        self.description = description
        self.due_time = due_time
        self.duration_minutes = max(1, duration_minutes)
        self.priority = priority if priority in self.PRIORITY_ORDER else "medium"
        self.task_type = task_type if task_type in self.TASK_EMOJIS else "other"
        self.recurring = recurring
        self.completed: bool = False

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def priority_value(self) -> int:
        """Return numeric priority weight (3 = high, 2 = medium, 1 = low)."""
        return self.PRIORITY_ORDER.get(self.priority, 1)

    # ------------------------------------------------------------------
    # Time helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_minutes(time_str: str) -> int:
        """Convert 'HH:MM' to total minutes since midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    @staticmethod
    def _from_minutes(total: int) -> str:
        """Convert total minutes since midnight to 'HH:MM' string."""
        return f"{total // 60:02d}:{total % 60:02d}"

    def start_minutes(self) -> int | None:
        """Return start time in minutes, or None if no due_time set."""
        return self._to_minutes(self.due_time) if self.due_time else None

    def end_minutes(self) -> int | None:
        """Return end time in minutes, or None if no due_time set."""
        s = self.start_minutes()
        return s + self.duration_minutes if s is not None else None

    def end_time(self) -> str | None:
        """Return end time as 'HH:MM' string, or None if no due_time set."""
        e = self.end_minutes()
        return self._from_minutes(e) if e is not None else None

    def overlaps_with(self, other: "Task") -> bool:
        """Return True if this task's time window overlaps with *other*'s."""
        if self.due_time is None or other.due_time is None:
            return False
        s1, e1 = self._to_minutes(self.due_time), self._to_minutes(self.due_time) + self.duration_minutes
        s2, e2 = self._to_minutes(other.due_time), self._to_minutes(other.due_time) + other.duration_minutes
        return s1 < e2 and s2 < e1

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @property
    def status_icon(self) -> str:
        return "✅" if self.completed else "⏳"

    @property
    def type_emoji(self) -> str:
        return self.TASK_EMOJIS.get(self.task_type, "📋")

    @property
    def priority_icon(self) -> str:
        return self.PRIORITY_EMOJI.get(self.priority, "🟡")

    def __repr__(self) -> str:
        time_part = f"@ {self.due_time}" if self.due_time else "(no time set)"
        recur = " 🔁" if self.recurring else ""
        return (
            f"{self.status_icon} {self.type_emoji} {self.priority_icon} "
            f"[{self.priority.upper()}] {self.description} "
            f"{time_part} ({self.duration_minutes}min){recur}"
        )

    def to_dict(self) -> dict:
        """Serialise task to a plain dict (for display tables)."""
        return {
            "Status": self.status_icon,
            "Type": f"{self.type_emoji} {self.task_type}",
            "Priority": f"{self.priority_icon} {self.priority}",
            "Description": self.description,
            "Due": self.due_time or "—",
            "End": self.end_time() or "—",
            "Duration": f"{self.duration_minutes} min",
            "Recurring": "🔁 yes" if self.recurring else "no",
        }
