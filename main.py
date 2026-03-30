"""PawPal+ — End-to-end demonstration script.

Run with:
    python main.py

Requires:
    pip install tabulate colorama
"""

from __future__ import annotations

try:
    from tabulate import tabulate
    TABULATE = True
except ImportError:
    TABULATE = False

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    COLORAMA = True
except ImportError:
    COLORAMA = False

from pawpal import Task, Pet, Owner, Scheduler

# ── helpers ──────────────────────────────────────────────────────────────────

def header(text: str) -> None:
    if COLORAMA:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─' * 60}")
        print(f"  {text}")
        print(f"{'─' * 60}{Style.RESET_ALL}")
    else:
        print(f"\n{'─' * 60}")
        print(f"  {text}")
        print(f"{'─' * 60}")


def print_task_table(pairs: list[tuple[Pet, Task]], title: str = "") -> None:
    if title:
        if COLORAMA:
            print(f"\n{Fore.YELLOW}{title}{Style.RESET_ALL}")
        else:
            print(f"\n{title}")

    if not pairs:
        print("  (no tasks)")
        return

    rows = []
    for pet, task in pairs:
        status_color = ""
        if COLORAMA:
            if task.completed:
                status_color = Fore.GREEN
            elif task.priority == "high":
                status_color = Fore.RED
            elif task.priority == "medium":
                status_color = Fore.YELLOW
            else:
                status_color = Fore.WHITE
        rows.append([
            f"{status_color}{task.status_icon}{Style.RESET_ALL if COLORAMA else ''}",
            f"{pet.species_emoji} {pet.name}",
            f"{task.type_emoji} {task.task_type}",
            f"{task.priority_icon} {task.priority}",
            task.description,
            task.due_time or "—",
            task.end_time() or "—",
            f"{task.duration_minutes} min",
            "🔁" if task.recurring else "",
        ])

    headers = ["", "Pet", "Type", "Priority", "Description", "Start", "End", "Duration", "Rec."]
    if TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        # Fallback plain-text table
        col_w = [3, 12, 14, 12, 28, 7, 7, 10, 5]
        fmt = "  ".join(f"{{:<{w}}}" for w in col_w)
        print("  " + fmt.format(*headers))
        print("  " + "  ".join("─" * w for w in col_w))
        for row in rows:
            print("  " + fmt.format(*[str(c)[:w] for c, w in zip(row, col_w)]))


def print_schedule_table(schedule: list[tuple[Pet, Task, str]], title: str = "") -> None:
    if title:
        if COLORAMA:
            print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        else:
            print(f"\n{title}")

    if not schedule:
        print("  (empty schedule — no pending tasks fit within the window)")
        return

    rows = []
    for i, (pet, task, assigned_time) in enumerate(schedule, 1):
        from pawpal.task import Task as T
        end_mins = T._to_minutes(assigned_time) + task.duration_minutes
        end_str = T._from_minutes(end_mins)
        rows.append([
            i,
            assigned_time,
            end_str,
            f"{pet.species_emoji} {pet.name}",
            f"{task.type_emoji} {task.task_type}",
            f"{task.priority_icon} {task.priority}",
            task.description,
            f"{task.duration_minutes} min",
        ])

    headers = ["#", "Start", "End", "Pet", "Type", "Priority", "Task", "Duration"]
    if TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        col_w = [3, 6, 6, 12, 14, 12, 28, 10]
        fmt = "  ".join(f"{{:<{w}}}" for w in col_w)
        print("  " + fmt.format(*headers))
        print("  " + "  ".join("─" * w for w in col_w))
        for row in rows:
            print("  " + fmt.format(*[str(c)[:w] for c, w in zip(row, col_w)]))


# ── demo data setup ───────────────────────────────────────────────────────────

def build_demo() -> tuple[Owner, Scheduler]:
    # Owner
    owner = Owner("Jordan", "jordan@example.com")

    # --- Pet 1: Mochi the cat ---
    mochi = Pet("Mochi", "cat", age=3)
    mochi.add_task(Task("Morning feeding",   "07:30", 10, priority="high",   task_type="feeding",    recurring=True))
    mochi.add_task(Task("Playtime with wand","09:00", 20, priority="medium", task_type="play",       recurring=False))
    mochi.add_task(Task("Flea medication",   "08:00", 5,  priority="high",   task_type="medication", recurring=False))
    mochi.add_task(Task("Brush fur",         "15:00", 15, priority="low",    task_type="grooming",   recurring=False))
    mochi.add_task(Task("Evening feeding",   "18:30", 10, priority="high",   task_type="feeding",    recurring=True))

    # --- Pet 2: Biscuit the dog ---
    biscuit = Pet("Biscuit", "dog", age=5)
    biscuit.add_task(Task("Morning walk",       "08:00", 30, priority="high",   task_type="walk",       recurring=True))
    biscuit.add_task(Task("Breakfast",          "08:45", 10, priority="high",   task_type="feeding",    recurring=True))
    biscuit.add_task(Task("Vet check-up",       "11:00", 60, priority="high",   task_type="vet",        recurring=False))
    biscuit.add_task(Task("Afternoon walk",     "16:00", 25, priority="medium", task_type="walk",       recurring=True))
    biscuit.add_task(Task("Trick training",     "17:00", 20, priority="low",    task_type="play",       recurring=False))
    biscuit.add_task(Task("Dinner",             "18:00", 10, priority="high",   task_type="feeding",    recurring=True))

    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    scheduler = Scheduler(owner)
    return owner, scheduler


# ── main demo ─────────────────────────────────────────────────────────────────

def main() -> None:
    owner, scheduler = build_demo()

    header("🐾 PawPal+ — Pet Care Scheduling System Demo")
    print(f"\n  Owner : {owner}")
    for pet in owner.list_pets():
        print(f"  Pet   : {pet}")

    # ── All tasks ──────────────────────────────────────────────────────
    header("📋 All Tasks (all pets)")
    print_task_table(owner.get_all_tasks())

    # ── Feature 1 — Sort by priority ──────────────────────────────────
    header("🔴 Feature 1: Tasks Sorted by Priority (high → low)")
    sorted_priority = scheduler.sort_tasks_by_priority()
    print_task_table(sorted_priority, "Pending tasks, highest priority first:")

    # ── Feature 2 — Sort by due time ──────────────────────────────────
    header("⏰ Feature 2: Tasks Sorted by Due Time")
    sorted_time = scheduler.sort_tasks_by_due_time()
    print_task_table(sorted_time, "Pending tasks, earliest start first:")

    # ── Feature 3 — Filter tasks ──────────────────────────────────────
    header("🔍 Feature 3: Filter Tasks")
    walk_tasks = scheduler.filter_tasks(task_type="walk")
    print_task_table(walk_tasks, "Filter → task_type = 'walk':")

    feeding_tasks = scheduler.filter_tasks(task_type="feeding")
    print_task_table(feeding_tasks, "Filter → task_type = 'feeding':")

    # ── Feature 4 — Detect conflicts ──────────────────────────────────
    header("⚠️  Feature 4: Conflict Detection")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        if COLORAMA:
            print(f"\n  {Fore.RED}Found {len(conflicts)} scheduling conflict(s):{Style.RESET_ALL}")
        else:
            print(f"\n  Found {len(conflicts)} scheduling conflict(s):")
        for pet_a, task_a, pet_b, task_b in conflicts:
            print(f"    ⛔ [{pet_a.name}] {task_a.description} ({task_a.due_time}–{task_a.end_time()})")
            print(f"       conflicts with")
            print(f"       [{pet_b.name}] {task_b.description} ({task_b.due_time}–{task_b.end_time()})")
    else:
        print("\n  ✅ No scheduling conflicts found.")

    # ── Feature 5 (STRETCH) — Next available slot ─────────────────────
    header("🕐 Feature 5 (Stretch): Next Available Time Slot")
    for duration in [15, 30, 60]:
        slot = scheduler.next_available_slot(duration, start_after="08:00", end_before="22:00")
        if slot:
            print(f"  Next free {duration:3d}-minute slot: {slot}")
        else:
            print(f"  No free {duration:3d}-minute slot found in the day.")

    # ── Feature 6 (STRETCH) — Generate daily schedule ─────────────────
    header("📅 Feature 6 (Stretch): Generate Conflict-Free Daily Schedule")
    print("  Priority-based time-blocking from 08:00 → 20:00:\n")
    schedule = scheduler.generate_daily_schedule(start_time="08:00", end_time="20:00")
    print_schedule_table(schedule)

    # ── Mark some tasks complete and show difference ───────────────────
    header("✅ Completing Tasks and Re-filtering")
    mochi_tasks = owner.get_pet_by_name("Mochi").tasks
    mochi_tasks[0].mark_complete()   # Morning feeding
    mochi_tasks[2].mark_complete()   # Flea medication

    print("\n  Marked 'Morning feeding' and 'Flea medication' as complete.\n")
    completed = scheduler.filter_tasks(status="completed")
    print_task_table(completed, "Completed tasks:")

    pending = scheduler.filter_tasks(status="pending")
    print_task_table(pending, "Remaining pending tasks:")

    if COLORAMA:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}  Demo complete! ✨{Style.RESET_ALL}\n")
    else:
        print("\n  Demo complete! ✨\n")


if __name__ == "__main__":
    main()
