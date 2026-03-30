# PawPal+ Project Reflection

---

## 1. System Design

**a. Initial design**

The first UML draft included four classes: `Task`, `Pet`, `Owner`, and `Scheduler`. The responsibilities were separated cleanly from the start:

- `Task` was purely a data container with time arithmetic built in. I decided early to store `due_time` as an `"HH:MM"` string rather than a Python `datetime.time` object, because string representation is easier to display and pass through a UI without conversion.
- `Pet` was responsible only for storing and managing its own list of tasks — no scheduling logic belonged there.
- `Owner` served as the top-level aggregator: it holds pets and provides cross-pet task access, but delegates all algorithmic work to `Scheduler`.
- `Scheduler` held a reference to the `Owner` and was responsible for all meaningful logic: sorting, filtering, conflict detection, and schedule generation.

The initial design also included `recurring` and `task_type` attributes on `Task`, because a real pet-care assistant would need to categorise tasks and repeat them daily — those felt essential even in the first sketch.

**b. Design changes**

The most significant design change happened to the `Scheduler.generate_daily_schedule` method. The first version sorted tasks by their preferred `due_time` only, which produced correct (non-overlapping) schedules but violated the priority contract — a low-priority task with an early `due_time` would be placed before a high-priority task with a later one. The fix was to use a two-key sort: **priority rank first** (high=0, medium=1, low=2), then preferred time as a tiebreaker. This change made the algorithm match what the rubric called "priority-based time-blocking."

A smaller change was adding `end_minutes()` alongside `end_time()` on `Task`. Originally only the string version existed, but the schedule generator and test suite both needed the integer form for arithmetic — so the static `_to_minutes` / `_from_minutes` helpers were extracted as reusable building blocks.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints, in order of importance:

1. **Priority** — high-priority tasks are placed into the schedule before medium and low ones. A missed feeding or medication is more harmful than a missed play session.
2. **Preferred due time** — within the same priority tier, tasks are placed as close to their stated `due_time` as possible. If a task is marked for 08:00, the scheduler honours that unless a conflict forces it later.
3. **Owner availability** — the scheduler treats the owner as a single resource who can only do one thing at a time. Two tasks, even for different pets, cannot overlap. This is the core constraint that the conflict-detection and schedule-generation algorithms enforce.

Duration (how long a task takes) was prioritised over task type, since the scheduler has no semantic knowledge of whether a "walk" is more important than "grooming" beyond what the owner signals via the `priority` field.

**b. Tradeoffs**

The main tradeoff is **greedy placement vs. global optimality**. The `generate_daily_schedule` algorithm places tasks one at a time in priority order, sliding each forward to the next free slot. This is fast (O(n²) in the number of tasks) and always produces a valid schedule, but it is not globally optimal — a different ordering might fit more total tasks into the day.

For example, if two high-priority tasks both want the 08:00 slot, the second one is bumped to immediately after the first. This could cascade and push lower-priority tasks out of the schedule window entirely, even though a smarter arrangement might have found room for all of them. For a household with two pets and ~10 tasks per day, this greedy approach is perfectly adequate. A combinatorial optimiser (e.g., integer programming) would be overkill and far harder to explain.

---

## 3. AI Collaboration

**a. How AI was used**

AI was used throughout the project in several distinct roles:

- **Design brainstorming** (Phase 1): I described the four-class structure in plain English and asked for a Mermaid class diagram to validate the relationships. The AI correctly flagged that `Scheduler` should hold a reference to `Owner` (not directly to a list of pets) so that adding a pet to the owner after the scheduler is constructed would automatically be visible to the scheduler.
- **Algorithm drafting** (Phases 2 & 4): The initial scan-and-push loop for `next_available_slot` was drafted by prompting "given a sorted list of (start, end) intervals and a required duration, find the first free gap of that length." The generated loop was correct but used a `while True` with a `break`, which I refactored into a more readable `while candidate + duration <= end_mins` loop with a `pushed` flag.
- **Test generation** (Phase 5): Asking "what are the most important edge cases for a scheduling system?" surfaced the "task with `due_time=None` should not be reported as conflicting with anything" case, which I had not written a test for.
- **Docstring generation** (Phase 6): The module-level docstring for `scheduler.py` listing all six algorithmic features was initially generated and then edited to include the concrete design rationale.

The most helpful prompt structure was: `"Given [specific context], do [specific action], and flag any edge cases you notice."` Generic prompts like `"improve this code"` produced unhelpful generic output.

**b. Judgment and verification**

One AI suggestion I rejected was for the `detect_conflicts` method. The AI proposed returning a simple list of strings like `"Task A conflicts with Task B"` for easy display. I replaced this with returning structured 4-tuples `(pet_a, task_a, pet_b, task_b)` instead. The reason: string messages lock in the display format at the logic layer, making it impossible to render the conflict differently in the CLI versus the Streamlit UI without re-parsing the string. Returning structured data lets the presentation layer decide how to format it — a basic OOP principle (separation of concerns).

To verify the conflict detection algorithm, I wrote three targeted tests: a sequential schedule that should produce zero conflicts, a direct single-pet overlap, and a cross-pet overlap. All three passed on the first run, which gave me confidence the logic was correct.

---

## 4. Testing and Verification

**a. What was tested**

The 32-test suite covers:

- **Task mechanics**: `mark_complete`, priority values, time arithmetic (`end_time`, `end_minutes`, `start_minutes`), overlap detection for sequential and overlapping pairs, invalid-input sanitisation (priority defaults, duration minimum).
- **Pet operations**: adding tasks, removing tasks (including case-insensitive match and not-found cases), pending vs. completed filtering.
- **Owner aggregation**: multi-pet task counts, cross-pet pending filtering, name-based pet lookup.
- **Scheduler algorithms**: sort correctness (both priority and time), filter correctness (by type, status, and pet scope), conflict detection (no conflict, single-pet conflict, cross-pet conflict, no-due-time case), next-available slot (return format, correct position after occupied block, `None` when no slot fits), and daily schedule (list of 3-tuples, chronological order, **zero-overlap guarantee** verified by pairwise interval check, completed tasks excluded, high-priority tasks scheduled earlier on average).

**b. Confidence**

Confidence: ⭐⭐⭐⭐⭐. The zero-overlap guarantee is the most critical property and it is verified directly — the test constructs a schedule and then does an O(n²) pairwise check on all generated intervals.

Edge cases I would test with more time: schedules where all tasks share the same priority (tie-breaking by time); tasks whose duration exceeds the entire day window (should be silently skipped); an owner with zero pets; and a pet whose tasks all have `completed=True` (schedule should be empty).

---

## 5. Reflection

**a. What went well**

The clean separation between the data layer (`Task`, `Pet`, `Owner`) and the algorithmic layer (`Scheduler`) made every individual piece easy to test and reason about. When the `generate_daily_schedule` priority bug appeared, the fix was entirely local to the `Scheduler` — no other class needed to change. The Streamlit UI wired up in about an hour specifically because the backend was already solid.

**b. What would be improved**

With another iteration, I would add **data persistence** (JSON save/load on the `Owner` class) so that pets and tasks survive app restarts. I would also refactor `generate_daily_schedule` to return a richer object — perhaps a `ScheduledEntry` dataclass — rather than a bare 3-tuple, so callers don't have to remember index positions.

**c. Key takeaway**

The most important thing I learned is that AI is most valuable as a **design critic and edge-case generator**, not as a code generator. The code it produced was often correct but generic; the value came from asking "what did I miss?" rather than "write this for me." Acting as the lead architect — deciding what to accept, what to reject, and why — produced a more coherent system than blindly applying AI suggestions would have.

---

## AI Model / Prompt Comparison (Stretch)

Two different prompting strategies were compared for implementing `detect_conflicts`:

**Strategy A — Imperative prompt**: "Write a function that takes a list of Task objects and returns all pairs that overlap in time." The AI returned a function that accepted a flat list and returned string messages. This required significant refactoring to fit the class structure and return structured data.

**Strategy B — Design-first prompt**: "I have a `Scheduler` class that holds an `Owner`. The `Owner` has a list of `Pet` objects, each with a list of `Task` objects that have `due_time` (HH:MM string) and `duration_minutes`. Write a `detect_conflicts(pet=None)` method that returns a list of 4-tuples `(pet_a, task_a, pet_b, task_b)` for any pair of tasks whose time windows overlap. Two tasks overlap when `start_a < end_b and start_b < end_a`." The AI returned code that was almost directly usable after adding the optional `pet` scoping parameter.

**Conclusion**: Providing the exact class structure, return type, and mathematical definition of the overlap condition in the prompt eliminated nearly all post-generation editing. Vague prompts produced code that was plausible but misfit the architecture.
