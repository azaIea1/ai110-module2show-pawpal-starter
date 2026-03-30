"""pytest suite for PawPal+.

Run with:
    pytest tests_test_pawpal.py -v
"""

import pytest
from pawpal import Task, Pet, Owner, Scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_task():
    return Task("Morning walk", "08:00", 30, priority="high", task_type="walk")


@pytest.fixture
def two_tasks():
    t1 = Task("Walk",    "08:00", 30, priority="high",   task_type="walk")
    t2 = Task("Feeding", "09:00", 10, priority="medium", task_type="feeding")
    return t1, t2


@pytest.fixture
def pet_with_tasks():
    pet = Pet("Mochi", "cat", age=3)
    pet.add_task(Task("Morning feeding", "07:30", 10, priority="high",   task_type="feeding"))
    pet.add_task(Task("Playtime",        "09:00", 20, priority="medium", task_type="play"))
    pet.add_task(Task("Brush fur",       "15:00", 15, priority="low",    task_type="grooming"))
    return pet


@pytest.fixture
def full_owner():
    owner = Owner("Jordan", "jordan@example.com")
    mochi = Pet("Mochi", "cat", age=3)
    mochi.add_task(Task("Morning feeding", "07:30", 10, priority="high",   task_type="feeding"))
    mochi.add_task(Task("Playtime",        "09:00", 20, priority="medium", task_type="play"))
    mochi.add_task(Task("Flea med",        "08:00", 5,  priority="high",   task_type="medication"))

    biscuit = Pet("Biscuit", "dog", age=5)
    biscuit.add_task(Task("Morning walk",  "08:00", 30, priority="high",   task_type="walk"))
    biscuit.add_task(Task("Vet check",     "11:00", 60, priority="high",   task_type="vet"))
    biscuit.add_task(Task("Afternoon walk","16:00", 25, priority="medium", task_type="walk"))

    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    return owner


# ─────────────────────────────────────────────────────────────────────────────
# Task tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTask:
    def test_default_completed_is_false(self, simple_task):
        assert simple_task.completed is False

    def test_mark_complete(self, simple_task):
        simple_task.mark_complete()
        assert simple_task.completed is True

    def test_priority_value(self):
        assert Task("x", None, 10, priority="high").priority_value() == 3
        assert Task("x", None, 10, priority="medium").priority_value() == 2
        assert Task("x", None, 10, priority="low").priority_value() == 1

    def test_end_time_calculation(self, simple_task):
        # 08:00 + 30 min = 08:30
        assert simple_task.end_time() == "08:30"

    def test_end_time_crosses_hour(self):
        t = Task("x", "09:45", 30)
        assert t.end_time() == "10:15"

    def test_end_time_none_when_no_due_time(self):
        t = Task("x", None, 30)
        assert t.end_time() is None

    def test_no_overlap_when_sequential(self, two_tasks):
        t1, t2 = two_tasks
        # t1: 08:00–08:30 | t2: 09:00–09:10 → no overlap
        assert not t1.overlaps_with(t2)

    def test_overlap_detected(self):
        t1 = Task("A", "08:00", 60)  # 08:00–09:00
        t2 = Task("B", "08:30", 30)  # 08:30–09:00
        assert t1.overlaps_with(t2)
        assert t2.overlaps_with(t1)

    def test_no_overlap_when_no_due_time(self):
        t1 = Task("A", "08:00", 30)
        t2 = Task("B", None,    30)
        assert not t1.overlaps_with(t2)

    def test_invalid_priority_defaults_to_medium(self):
        t = Task("x", None, 10, priority="critical")
        assert t.priority == "medium"

    def test_duration_minimum_one(self):
        t = Task("x", None, 0)
        assert t.duration_minutes == 1

    def test_to_dict_keys(self, simple_task):
        d = simple_task.to_dict()
        for key in ("Status", "Type", "Priority", "Description", "Due", "End", "Duration"):
            assert key in d


# ─────────────────────────────────────────────────────────────────────────────
# Pet tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPet:
    def test_add_and_list_tasks(self, pet_with_tasks):
        assert len(pet_with_tasks.list_tasks()) == 3

    def test_get_pending_tasks(self, pet_with_tasks):
        # None completed yet
        assert len(pet_with_tasks.get_pending_tasks()) == 3

    def test_completed_tasks_excluded_from_pending(self, pet_with_tasks):
        pet_with_tasks.tasks[0].mark_complete()
        assert len(pet_with_tasks.get_pending_tasks()) == 2
        assert len(pet_with_tasks.get_completed_tasks()) == 1

    def test_remove_task_found(self, pet_with_tasks):
        removed = pet_with_tasks.remove_task("Playtime")
        assert removed is True
        assert len(pet_with_tasks.list_tasks()) == 2

    def test_remove_task_case_insensitive(self, pet_with_tasks):
        removed = pet_with_tasks.remove_task("PLAYTIME")
        assert removed is True

    def test_remove_task_not_found(self, pet_with_tasks):
        removed = pet_with_tasks.remove_task("nonexistent task")
        assert removed is False


# ─────────────────────────────────────────────────────────────────────────────
# Owner tests
# ─────────────────────────────────────────────────────────────────────────────

class TestOwner:
    def test_add_and_list_pets(self, full_owner):
        pets = full_owner.list_pets()
        assert len(pets) == 2
        assert any(p.name == "Mochi" for p in pets)
        assert any(p.name == "Biscuit" for p in pets)

    def test_get_all_tasks_count(self, full_owner):
        # Mochi: 3 tasks, Biscuit: 3 tasks → 6 total
        all_tasks = full_owner.get_all_tasks()
        assert len(all_tasks) == 6

    def test_get_all_pending_tasks(self, full_owner):
        # Mark one task complete
        full_owner.pets[0].tasks[0].mark_complete()
        pending = full_owner.get_all_pending_tasks()
        assert len(pending) == 5

    def test_get_pet_by_name(self, full_owner):
        pet = full_owner.get_pet_by_name("Biscuit")
        assert pet is not None
        assert pet.name == "Biscuit"

    def test_get_pet_by_name_case_insensitive(self, full_owner):
        pet = full_owner.get_pet_by_name("mochi")
        assert pet is not None

    def test_get_pet_by_name_not_found(self, full_owner):
        assert full_owner.get_pet_by_name("Rex") is None


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSchedulerSortByPriority:
    def test_high_before_medium_before_low(self, full_owner):
        scheduler = Scheduler(full_owner)
        sorted_tasks = scheduler.sort_tasks_by_priority()
        priorities = [t.priority for _, t in sorted_tasks]
        # High items should come before medium, medium before low
        # Convert to numeric rank and check non-decreasing
        rank = {"high": 0, "medium": 1, "low": 2}
        ranks = [rank[p] for p in priorities]
        assert ranks == sorted(ranks)

    def test_sort_operates_across_multiple_pets(self, full_owner):
        scheduler = Scheduler(full_owner)
        sorted_tasks = scheduler.sort_tasks_by_priority()
        pet_names = {pet.name for pet, _ in sorted_tasks}
        # Both pets should appear in results
        assert "Mochi" in pet_names
        assert "Biscuit" in pet_names


class TestSchedulerSortByDueTime:
    def test_earliest_first(self, full_owner):
        scheduler = Scheduler(full_owner)
        sorted_tasks = scheduler.sort_tasks_by_due_time()
        times = [t.due_time for _, t in sorted_tasks if t.due_time]
        mins = [Task._to_minutes(t) for t in times]
        assert mins == sorted(mins)

    def test_no_due_time_goes_last(self, full_owner):
        full_owner.pets[0].add_task(Task("Unknown time task", None, 20))
        scheduler = Scheduler(full_owner)
        sorted_tasks = scheduler.sort_tasks_by_due_time()
        # Task with None due_time should be last
        assert sorted_tasks[-1][1].due_time is None


class TestSchedulerFilter:
    def test_filter_by_task_type(self, full_owner):
        scheduler = Scheduler(full_owner)
        walks = scheduler.filter_tasks(task_type="walk")
        assert all(t.task_type == "walk" for _, t in walks)
        assert len(walks) >= 2  # Both Mochi's walk-free and Biscuit's walks

    def test_filter_pending(self, full_owner):
        full_owner.pets[0].tasks[0].mark_complete()
        scheduler = Scheduler(full_owner)
        pending = scheduler.filter_tasks(status="pending")
        assert all(not t.completed for _, t in pending)

    def test_filter_completed(self, full_owner):
        full_owner.pets[0].tasks[0].mark_complete()
        scheduler = Scheduler(full_owner)
        done = scheduler.filter_tasks(status="completed")
        assert len(done) == 1
        assert done[0][1].completed

    def test_filter_scoped_to_pet(self, full_owner):
        scheduler = Scheduler(full_owner)
        mochi = full_owner.get_pet_by_name("Mochi")
        results = scheduler.filter_tasks(pet=mochi)
        assert all(p.name == "Mochi" for p, _ in results)


class TestSchedulerConflictDetection:
    def test_no_conflicts_in_sequential_schedule(self):
        owner = Owner("Test")
        pet = Pet("Rex", "dog")
        pet.add_task(Task("Walk",    "08:00", 30))
        pet.add_task(Task("Feeding", "09:00", 10))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []

    def test_conflict_detected_for_overlapping_tasks(self):
        owner = Owner("Test")
        pet = Pet("Rex", "dog")
        pet.add_task(Task("A", "08:00", 60))  # 08:00–09:00
        pet.add_task(Task("B", "08:30", 30))  # 08:30–09:00  ← overlaps
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1

    def test_conflict_detected_across_different_pets(self):
        owner = Owner("Test")
        p1 = Pet("Rex",  "dog")
        p2 = Pet("Mochi","cat")
        p1.add_task(Task("Dog walk",     "08:00", 30))
        p2.add_task(Task("Cat grooming", "08:15", 20))  # overlaps with dog walk
        owner.add_pet(p1)
        owner.add_pet(p2)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1

    def test_no_conflict_when_tasks_have_no_due_time(self):
        owner = Owner("Test")
        pet = Pet("Rex", "dog")
        pet.add_task(Task("A", None, 30))
        pet.add_task(Task("B", None, 30))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []


class TestSchedulerNextAvailableSlot:
    def test_returns_string_format(self, full_owner):
        scheduler = Scheduler(full_owner)
        slot = scheduler.next_available_slot(10, start_after="06:00")
        assert slot is not None
        assert ":" in slot
        h, m = slot.split(":")
        assert 0 <= int(h) <= 23
        assert 0 <= int(m) <= 59

    def test_slot_comes_after_occupied_block(self):
        owner = Owner("Test")
        pet = Pet("Rex", "dog")
        # Task fills 08:00–08:30 exactly
        pet.add_task(Task("Walk", "08:00", 30))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        # 30-minute slot starting from 08:00 should not start at 08:00
        slot = scheduler.next_available_slot(30, start_after="08:00")
        assert slot is not None
        assert Task._to_minutes(slot) >= Task._to_minutes("08:30")

    def test_returns_none_when_no_slot_fits(self):
        owner = Owner("Test")
        pet = Pet("Rex", "dog")
        # Fill 08:00–20:00 with a single giant task
        pet.add_task(Task("All day", "08:00", 720))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        slot = scheduler.next_available_slot(60, start_after="08:00", end_before="20:00")
        # Should return None since the whole window is blocked
        assert slot is None


class TestSchedulerDailySchedule:
    def test_schedule_returns_list_of_tuples(self, full_owner):
        scheduler = Scheduler(full_owner)
        schedule = scheduler.generate_daily_schedule()
        assert isinstance(schedule, list)
        for item in schedule:
            assert len(item) == 3  # (pet, task, assigned_time_str)

    def test_schedule_is_chronologically_ordered(self, full_owner):
        scheduler = Scheduler(full_owner)
        schedule = scheduler.generate_daily_schedule()
        times = [Task._to_minutes(assigned) for _, _, assigned in schedule]
        assert times == sorted(times)

    def test_schedule_has_no_overlapping_time_blocks(self, full_owner):
        scheduler = Scheduler(full_owner)
        schedule = scheduler.generate_daily_schedule()
        # Build intervals and check for overlaps
        intervals = []
        for _, task, assigned in schedule:
            start = Task._to_minutes(assigned)
            end = start + task.duration_minutes
            intervals.append((start, end))
        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                s1, e1 = intervals[i]
                s2, e2 = intervals[j]
                assert not (s1 < e2 and s2 < e1), (
                    f"Overlap detected: {intervals[i]} vs {intervals[j]}"
                )

    def test_only_pending_tasks_in_schedule(self, full_owner):
        # Complete one task before generating schedule
        full_owner.pets[0].tasks[0].mark_complete()
        scheduler = Scheduler(full_owner)
        schedule = scheduler.generate_daily_schedule()
        for _, task, _ in schedule:
            assert not task.completed

    def test_high_priority_tasks_scheduled_earlier_on_average(self, full_owner):
        scheduler = Scheduler(full_owner)
        schedule = scheduler.generate_daily_schedule()
        high_times = [Task._to_minutes(a) for _, t, a in schedule if t.priority == "high"]
        low_times  = [Task._to_minutes(a) for _, t, a in schedule if t.priority == "low"]
        if high_times and low_times:
            assert min(high_times) <= max(low_times)
