"""PawPal+ — Streamlit UI.

Run with:
    streamlit run app.py
"""

from __future__ import annotations
import streamlit as st
from pawpal import Task, Pet, Owner, Scheduler

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin-right: 4px;
    }
    .badge-high   { background:#ffe0e0; color:#c0392b; }
    .badge-medium { background:#fff3cd; color:#856404; }
    .badge-low    { background:#d4edda; color:#155724; }
    .badge-done   { background:#e2e3e5; color:#495057; }
    .task-card {
        border-left: 4px solid #ccc;
        padding: 6px 12px;
        margin-bottom: 6px;
        border-radius: 4px;
        background: #f8f9fa;
    }
    .task-card.high   { border-left-color: #FF4B4B; }
    .task-card.medium { border-left-color: #FFA500; }
    .task-card.low    { border-left-color: #21c354; }
    .task-card.done   { border-left-color: #adb5bd; opacity: 0.7; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation
# ─────────────────────────────────────────────────────────────────────────────

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", "jordan@example.com")

if "initialized" not in st.session_state:
    mochi = Pet("Mochi", "cat", age=3)
    mochi.add_task(Task("Morning feeding",  "07:30", 10, priority="high",   task_type="feeding",    recurring=True))
    mochi.add_task(Task("Playtime",         "09:00", 20, priority="medium", task_type="play"))
    mochi.add_task(Task("Flea medication",  "08:00",  5, priority="high",   task_type="medication"))
    mochi.add_task(Task("Brush fur",        "15:00", 15, priority="low",    task_type="grooming"))

    biscuit = Pet("Biscuit", "dog", age=5)
    biscuit.add_task(Task("Morning walk",   "08:30", 30, priority="high",   task_type="walk",    recurring=True))
    biscuit.add_task(Task("Breakfast",      "09:15", 10, priority="high",   task_type="feeding", recurring=True))
    biscuit.add_task(Task("Vet check-up",   "11:00", 60, priority="high",   task_type="vet"))
    biscuit.add_task(Task("Afternoon walk", "16:00", 25, priority="medium", task_type="walk",    recurring=True))
    biscuit.add_task(Task("Dinner",         "18:00", 10, priority="high",   task_type="feeding", recurring=True))

    st.session_state.owner.add_pet(mochi)
    st.session_state.owner.add_pet(biscuit)
    st.session_state.initialized = True

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Owner & Pet management
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Pet Care Scheduling Assistant")
    st.divider()

    st.subheader("👤 Owner")
    new_name  = st.text_input("Name",  value=st.session_state.owner.name,  key="owner_name_input")
    new_email = st.text_input("Email", value=st.session_state.owner.email, key="owner_email_input")
    if st.button("Update owner", use_container_width=True):
        st.session_state.owner.name  = new_name
        st.session_state.owner.email = new_email
        st.success("Owner updated!")

    st.divider()

    st.subheader("➕ Add Pet")
    pet_name    = st.text_input("Pet name", key="new_pet_name")
    pet_species = st.selectbox(
        "Species",
        ["dog", "cat", "bird", "rabbit", "fish", "hamster", "other"],
        key="new_pet_species",
    )
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_pet_age")
    if st.button("Add pet", use_container_width=True):
        if pet_name.strip():
            st.session_state.owner.add_pet(Pet(pet_name.strip(), pet_species, pet_age))
            st.success(f"{pet_name} added!")
            st.rerun()
        else:
            st.warning("Please enter a pet name.")

    st.divider()
    st.subheader("🐾 Your Pets")
    for pet in st.session_state.owner.list_pets():
        pending_count   = len(pet.get_pending_tasks())
        completed_count = len(pet.get_completed_tasks())
        st.markdown(
            f"{pet.species_emoji} **{pet.name}** ({pet.species}, {pet.age}yr)  \n"
            f"⏳ {pending_count} pending · ✅ {completed_count} done"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────────────────────────

owner     = st.session_state.owner
scheduler = Scheduler(owner)

st.title(f"🐾 PawPal+ — {owner.name}'s Pet Care Planner")

tab_tasks, tab_schedule, tab_conflicts = st.tabs(
    ["📋 Tasks", "📅 Daily Schedule", "⚠️ Conflicts & Slots"]
)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Task manager
# ═════════════════════════════════════════════════════════════════════════════

with tab_tasks:
    if not owner.list_pets():
        st.info("Add a pet in the sidebar to get started.")
    else:
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.subheader("➕ Add a Task")
            t_pet  = st.selectbox("For pet", [p.name for p in owner.list_pets()], key="t_pet")
            t_desc = st.text_input("Description", placeholder="e.g. Afternoon walk", key="t_desc")

            tc1, tc2 = st.columns(2)
            with tc1:
                t_type     = st.selectbox("Task type",
                    ["feeding", "walk", "medication", "grooming", "play", "vet", "other"],
                    key="t_type")
                t_priority = st.selectbox("Priority", ["high", "medium", "low"],
                    index=1, key="t_priority")
            with tc2:
                t_time = st.text_input("Due time (HH:MM)", value="08:00", key="t_time")
                t_dur  = st.number_input("Duration (min)", min_value=1, max_value=480,
                    value=20, key="t_dur")

            t_recurring = st.checkbox("Recurring (daily)", key="t_recurring")

            if st.button("➕ Add Task", use_container_width=True, type="primary"):
                pet_obj = owner.get_pet_by_name(t_pet)
                if pet_obj and t_desc.strip():
                    try:
                        Task._to_minutes(t_time)
                        valid_time: str | None = t_time
                    except Exception:
                        valid_time = None
                        st.warning("Invalid time — task added without a due time.")
                    pet_obj.add_task(
                        Task(t_desc.strip(), valid_time, t_dur,
                             priority=t_priority, task_type=t_type, recurring=t_recurring)
                    )
                    st.success(f"Task '{t_desc}' added to {t_pet}!")
                    st.rerun()
                else:
                    st.warning("Please fill in the task description.")

        with col_right:
            st.subheader("🔍 Filter")
            f_pet    = st.selectbox("Pet",
                ["All pets"] + [p.name for p in owner.list_pets()], key="f_pet")
            f_status = st.selectbox("Status",
                ["all", "pending", "completed"], key="f_status")
            f_type   = st.selectbox("Task type",
                ["all", "feeding", "walk", "medication", "grooming", "play", "vet", "other"],
                key="f_type")
            f_sort   = st.radio("Sort by", ["Priority", "Due time"], horizontal=True, key="f_sort")

        st.divider()

        pet_scope  = owner.get_pet_by_name(f_pet) if f_pet != "All pets" else None
        status_arg = None if f_status == "all" else f_status
        type_arg   = None if f_type   == "all" else f_type

        pairs = scheduler.filter_tasks(status=status_arg, task_type=type_arg, pet=pet_scope)
        if f_sort == "Priority":
            pairs = sorted(pairs, key=lambda pt: {"high": 0, "medium": 1, "low": 2}.get(pt[1].priority, 1))
        else:
            pairs = sorted(pairs, key=lambda pt: pt[1].start_minutes() if pt[1].due_time else 9999)

        st.subheader(f"📝 Task List ({len(pairs)} task(s))")

        if not pairs:
            st.info("No tasks match your filters.")
        else:
            for pet, task in pairs:
                css_class   = "done" if task.completed else task.priority
                badge_class = "badge-done" if task.completed else f"badge-{task.priority}"
                badge_label = "✅ done"    if task.completed else f"{task.priority_icon} {task.priority}"

                st.markdown(
                    f'<div class="task-card {css_class}">'
                    f'{task.type_emoji} <strong>{task.description}</strong> '
                    f'<span class="badge {badge_class}">{badge_label}</span>'
                    f'<br><small>{pet.species_emoji} {pet.name} &nbsp;|&nbsp; '
                    f'⏰ {task.due_time or "—"} → {task.end_time() or "—"} '
                    f'({task.duration_minutes} min)'
                    f'{"&nbsp; 🔁" if task.recurring else ""}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if not task.completed:
                    btn_key = f"complete_{pet.name}_{task.description}_{id(task)}"
                    if st.button("✅ Mark done", key=btn_key):
                        task.mark_complete()
                        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Daily schedule
# ═════════════════════════════════════════════════════════════════════════════

with tab_schedule:
    st.subheader("📅 Generate Daily Schedule")
    st.markdown(
        "Collects all **pending tasks**, respects priorities, and assigns conflict-free "
        "time blocks so you never have to be two places at once."
    )

    sc1, sc2 = st.columns(2)
    with sc1:
        sched_start = st.text_input("Start time", value="08:00", key="sched_start")
    with sc2:
        sched_end   = st.text_input("End time",   value="20:00", key="sched_end")

    if st.button("🗓️ Generate Schedule", type="primary", use_container_width=True):
        try:
            schedule = scheduler.generate_daily_schedule(
                start_time=sched_start, end_time=sched_end
            )
            st.session_state.last_schedule = schedule
        except Exception as e:
            st.error(f"Error: {e}")

    schedule = st.session_state.get("last_schedule", None)

    if schedule is None:
        st.info("Press **Generate Schedule** to build today's plan.")
    elif not schedule:
        st.warning("No pending tasks fit within the selected window.")
    else:
        st.success(f"✅ Scheduled {len(schedule)} task(s) with zero overlaps!")
        st.divider()

        priority_colors = {"high": "#FF4B4B", "medium": "#FFA500", "low": "#21c354"}

        for i, (pet, task, assigned_time) in enumerate(schedule, 1):
            end_mins = Task._to_minutes(assigned_time) + task.duration_minutes
            end_str  = Task._from_minutes(end_mins)
            color    = priority_colors.get(task.priority, "#888")

            st.markdown(
                f"""
                <div style="
                    border-left: 5px solid {color};
                    padding: 10px 16px; margin-bottom: 8px;
                    border-radius: 6px; background: #f9f9f9;
                ">
                    <span style="font-size:1.05em; font-weight:bold;">
                        {i}. {task.type_emoji} {task.description}
                    </span>
                    &nbsp;
                    <span class="badge badge-{task.priority}">{task.priority_icon} {task.priority}</span>
                    {"<span class='badge' style='background:#e8f4f8;color:#0c5460'>🔁</span>" if task.recurring else ""}
                    <br>
                    <small>
                        {pet.species_emoji} <strong>{pet.name}</strong>
                        &nbsp;|&nbsp; ⏰ <strong>{assigned_time}</strong> → <strong>{end_str}</strong>
                        &nbsp;({task.duration_minutes} min)
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        total_min = sum(t.duration_minutes for _, t, _ in schedule)
        h, m = divmod(total_min, 60)
        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Tasks scheduled", len(schedule))
        sm2.metric("Total care time", f"{h}h {m:02d}m")
        sm3.metric("🔴 High priority", sum(1 for _, t, _ in schedule if t.priority == "high"))
        sm4.metric("🟡 Med · 🟢 Low",
                   f"{sum(1 for _, t, _ in schedule if t.priority=='medium')} · "
                   f"{sum(1 for _, t, _ in schedule if t.priority=='low')}")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — Conflicts & next available slot
# ═════════════════════════════════════════════════════════════════════════════

with tab_conflicts:
    st.subheader("⚠️ Scheduling Conflicts")
    st.markdown(
        "Finds tasks with overlapping time windows. Because the owner can only do one "
        "thing at a time, overlaps across **any** pet count as conflicts."
    )

    scope_name = st.selectbox(
        "Check conflicts for",
        ["All pets"] + [p.name for p in owner.list_pets()],
        key="conflict_scope",
    )
    scope_pet = owner.get_pet_by_name(scope_name) if scope_name != "All pets" else None
    conflicts  = scheduler.detect_conflicts(pet=scope_pet)

    if not conflicts:
        st.success("✅ No scheduling conflicts found!")
    else:
        st.error(f"⛔ {len(conflicts)} conflict(s) detected:")
        for pet_a, task_a, pet_b, task_b in conflicts:
            st.markdown(
                f"""
                <div style="background:#fff0f0;border:1px solid #f5c6cb;
                            border-radius:6px;padding:10px 16px;margin-bottom:8px;">
                    ⛔ <strong>[{pet_a.name}]</strong> {task_a.type_emoji} {task_a.description}
                    &nbsp;<code>{task_a.due_time} – {task_a.end_time()}</code>
                    <br>&nbsp;&nbsp;&nbsp;conflicts with<br>
                    &nbsp;&nbsp;<strong>[{pet_b.name}]</strong> {task_b.type_emoji} {task_b.description}
                    &nbsp;<code>{task_b.due_time} – {task_b.end_time()}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.subheader("🕐 Find Next Available Time Slot")
    st.markdown("Scan existing tasks and find the earliest free window of a given duration.")

    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        slot_dur   = st.number_input("Duration needed (min)", min_value=5, max_value=480,
            value=30, key="slot_dur")
    with nc2:
        slot_start = st.text_input("Start looking from", value="08:00", key="slot_start")
    with nc3:
        slot_end_  = st.text_input("Day ends at", value="22:00", key="slot_end_")

    slot_pet_name = st.selectbox(
        "Scope to pet (optional)",
        ["All pets"] + [p.name for p in owner.list_pets()],
        key="slot_pet",
    )
    slot_pet = owner.get_pet_by_name(slot_pet_name) if slot_pet_name != "All pets" else None

    if st.button("🔍 Find Slot", type="primary"):
        slot = scheduler.next_available_slot(
            slot_dur,
            start_after=slot_start,
            end_before=slot_end_,
            pet=slot_pet,
        )
        if slot:
            end_slot = Task._from_minutes(Task._to_minutes(slot) + slot_dur)
            st.success(
                f"✅ Next free **{slot_dur}-minute** slot: **{slot}** → **{end_slot}**"
            )
        else:
            st.warning(
                f"No free {slot_dur}-minute slot found between {slot_start} and {slot_end_}."
            )
