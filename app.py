import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, filter_tasks

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

# ---------------------------------------------------------------------------
# Owner setup — persisted in session so it survives every rerun
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Available time today (minutes)", min_value=10, max_value=480, value=60
)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
else:
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_minutes = int(available_minutes)

# ---------------------------------------------------------------------------
# Add a pet
# ---------------------------------------------------------------------------
pet_name_input = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    pet = Pet(name=pet_name_input, species=species)
    st.session_state.owner.add_pet(pet)
    st.success(f"{pet_name_input} ({species}) added!")

if st.session_state.owner.pets:
    st.write("Registered pets:", ", ".join(p.name for p in st.session_state.owner.pets))

st.divider()

# ---------------------------------------------------------------------------
# Add a care task
# ---------------------------------------------------------------------------
st.subheader("Add a Care Task")

if not st.session_state.owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        pet_options = [p.name for p in st.session_state.owner.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_options)
    with col5:
        recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])

    start_time_str = st.text_input(
        "Preferred start time (HH:MM, optional — leave blank to auto-schedule)",
        value="",
        placeholder="e.g. 08:00",
    )

    def _parse_start_time(s: str) -> int | None:
        s = s.strip()
        if not s:
            return None
        try:
            h, m = s.split(":")
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            return None

    if st.button("Add task"):
        selected_pet = next(
            p for p in st.session_state.owner.pets if p.name == selected_pet_name
        )
        parsed_start = _parse_start_time(start_time_str)
        if start_time_str.strip() and parsed_start is None:
            st.error("Invalid time format — use HH:MM (e.g. 08:30).")
        else:
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                recurrence=recurrence,
                start_time=parsed_start,
            )
            selected_pet.add_task(task)
            time_label = f" @ {start_time_str}" if parsed_start is not None else ""
            st.success(f"Task '{task_title}' added to {selected_pet_name}{time_label}!")
            # Clear cached schedule — tasks changed
            st.session_state.pop("last_scheduler", None)

    st.divider()

    # -----------------------------------------------------------------------
    # Task table with filters
    # -----------------------------------------------------------------------
    st.subheader("Current Tasks")

    all_tasks = st.session_state.owner.get_all_tasks()

    PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    if all_tasks:
        fc1, fc2 = st.columns(2)
        with fc1:
            pet_filter_options = ["All pets"] + [p.name for p in st.session_state.owner.pets]
            pet_filter = st.selectbox("Filter by pet", pet_filter_options, key="filter_pet")
        with fc2:
            status_filter = st.selectbox(
                "Filter by status", ["All", "pending", "completed"], key="filter_status"
            )

        filtered = filter_tasks(
            all_tasks,
            pet_name=None if pet_filter == "All pets" else pet_filter,
            status=None if status_filter == "All" else status_filter,
        )

        if filtered:
            def _fmt_time(minutes: int | None) -> str:
                if minutes is None:
                    return "—"
                h, m = divmod(minutes, 60)
                return f"{h:02d}:{m:02d}"

            table_rows = [
                {
                    "Priority": f"{PRIORITY_ICON.get(t.priority, '')} {t.priority}",
                    "Task": t.title,
                    "Pet": t.pet_name,
                    "Duration": f"{t.duration_minutes} min",
                    "Start": _fmt_time(t.start_time),
                    "Recurrence": t.recurrence,
                    "Due": str(t.due_date) if t.due_date else "—",
                    "Status": "✅ done" if t.is_completed else "⏳ pending",
                }
                for t in filtered
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)

            # Mark-complete buttons below the table
            pending_filtered = [t for t in filtered if not t.is_completed]
            if pending_filtered:
                st.caption("Mark tasks complete:")
                for task in pending_filtered:
                    label = f"✔ {task.title} ({task.pet_name})"
                    if st.button(label, key=f"done_{id(task)}"):
                        pet_owner = next(
                            p for p in st.session_state.owner.pets if p.name == task.pet_name
                        )
                        next_task = pet_owner.mark_task_complete(task)
                        if next_task:
                            st.success(
                                f"'{task.title}' done! Next {task.recurrence} occurrence "
                                f"added — due {next_task.due_date}."
                            )
                        else:
                            st.success(f"'{task.title}' marked complete.")
                        st.session_state.pop("last_scheduler", None)
                        st.rerun()
        else:
            st.info("No tasks match the current filter.")

        # Spawn recurring tasks
        renewable = [t for t in all_tasks if t.is_completed and t.recurrence != "none"]
        if renewable:
            if st.button("🔄 Renew recurring tasks"):
                count = 0
                for pet in st.session_state.owner.pets:
                    count += len(pet.spawn_recurring_tasks())
                st.success(f"Added {count} new recurring task(s) for the next cycle.")
                st.session_state.pop("last_scheduler", None)
                st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_pending = st.session_state.owner.get_all_pending_tasks()
    if not all_pending:
        st.warning("Add some tasks before generating a schedule.")
    else:
        scheduler = Scheduler(
            st.session_state.owner, available_minutes=int(available_minutes)
        )
        scheduler.build_plan()
        st.session_state["last_scheduler"] = scheduler

# Render persisted schedule (survives reruns caused by other widgets)
scheduler = st.session_state.get("last_scheduler")
if scheduler and scheduler.plan:

    def _fmt_time(minutes: int | None) -> str:
        if minutes is None:
            return "—"
        h, m = divmod(minutes, 60)
        return f"{h:02d}:{m:02d}"

    # ── Summary metrics ──────────────────────────────────────────────────
    total_used = scheduler.get_total_duration()
    total_budget = scheduler.available_minutes
    skipped = [
        t for t in st.session_state.owner.get_all_pending_tasks()
        if t not in scheduler.plan
    ]
    conflicts = scheduler.detect_conflicts()

    m1, m2, m3 = st.columns(3)
    m1.metric("Time used", f"{total_used} min", f"{total_budget - total_used} min free")
    m2.metric("Tasks scheduled", len(scheduler.plan))
    m3.metric("Conflicts", len(conflicts), delta_color="inverse" if conflicts else "off")

    # ── Conflict warnings ────────────────────────────────────────────────
    warnings = scheduler.conflict_warnings()
    if warnings:
        for w in warnings:
            st.warning(w)
    else:
        st.success("No scheduling conflicts — your day is clear!")

    # ── Sorted schedule table ────────────────────────────────────────────
    st.markdown("#### Sorted Schedule")
    sorted_plan = scheduler.sort_by_time()
    plan_rows = [
        {
            "#": i,
            "Start": _fmt_time(scheduler._effective_start(t)),
            "End": _fmt_time(
                (scheduler._effective_start(t) + t.duration_minutes)
                if scheduler._effective_start(t) is not None else None
            ),
            "Priority": f"{PRIORITY_ICON.get(t.priority, '')} {t.priority}",
            "Task": t.title,
            "Pet": t.pet_name,
            "Duration": f"{t.duration_minutes} min",
            "Recurrence": t.recurrence,
        }
        for i, t in enumerate(sorted_plan, start=1)
    ]
    st.dataframe(plan_rows, use_container_width=True, hide_index=True)

    # ── Skipped tasks ────────────────────────────────────────────────────
    if skipped:
        st.markdown("#### Not Scheduled")
        st.caption("These tasks didn't fit within your available time budget:")
        for t in skipped:
            st.warning(
                f"⏭ **{t.title}** ({t.pet_name}) — {t.duration_minutes} min, "
                f"{t.priority} priority"
            )

    # ── Full text plan ───────────────────────────────────────────────────
    with st.expander("Full plan details (text)"):
        st.text(scheduler.explain_plan())
