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
    # Keep owner in sync with the form fields on every rerun
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_minutes = int(available_minutes)

# ---------------------------------------------------------------------------
# Add a pet — calls Pet() and owner.add_pet()
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

    # Optional preferred start time (HH:MM).  Leave blank for no preference.
    start_time_str = st.text_input(
        "Preferred start time (HH:MM, optional — leave blank to auto-schedule)",
        value="",
        placeholder="e.g. 08:00",
    )

    def _parse_start_time(s: str) -> int | None:
        """Parse 'HH:MM' to minutes from midnight.  Returns None on empty/invalid input."""
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

    st.divider()

    # -----------------------------------------------------------------------
    # Task table with filters
    # -----------------------------------------------------------------------
    st.subheader("Current Tasks")

    all_tasks = st.session_state.owner.get_all_tasks()

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
            # Build rows with a mark-complete checkbox per task
            for task in filtered:
                cols = st.columns([3, 1, 1, 1, 1, 1, 1])
                cols[0].write(task.title)
                cols[1].write(task.pet_name)
                cols[2].write(f"{task.duration_minutes} min")
                cols[3].write(task.priority)
                cols[4].write(task.recurrence)
                cols[5].write(str(task.due_date) if task.due_date else "—")
                status_label = "done" if task.is_completed else "pending"
                cols[6].write(status_label)
                if not task.is_completed:
                    if st.button(f"Mark done: {task.title} ({task.pet_name})", key=f"done_{id(task)}"):
                        pet_owner = next(
                            p for p in st.session_state.owner.pets if p.name == task.pet_name
                        )
                        next_task = pet_owner.mark_task_complete(task)
                        if next_task:
                            st.success(
                                f"'{task.title}' done! Next {task.recurrence} occurrence "
                                f"added — due {next_task.due_date}."
                            )
                        st.rerun()
        else:
            st.info("No tasks match the current filter.")

        # Spawn recurring tasks button
        recurring_pending = [
            t for t in all_tasks if t.is_completed and t.recurrence != "none"
        ]
        if recurring_pending:
            if st.button("Renew recurring tasks"):
                count = 0
                for pet in st.session_state.owner.pets:
                    count += len(pet.spawn_recurring_tasks())
                st.success(f"Added {count} new recurring task(s) for the next cycle.")
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

        # Conflicts banner
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            conflict_lines = "\n".join(
                f"• '{a.title}' ({a.pet_name}) overlaps '{b.title}' ({b.pet_name})"
                for a, b in conflicts
            )
            st.warning(f"**Scheduling conflicts detected:**\n{conflict_lines}")

        st.success(
            f"Schedule built — {scheduler.get_total_duration()} of {int(available_minutes)} min used."
        )

        # Render the plan as a table (sorted by time)
        sorted_plan = scheduler.sort_by_time()
        if sorted_plan:
            def _fmt_time(minutes: int | None) -> str:
                if minutes is None:
                    return "—"
                h, m = divmod(minutes, 60)
                return f"{h:02d}:{m:02d}"

            st.table([
                {
                    "#": i,
                    "Start": _fmt_time(scheduler._effective_start(t)),
                    "Task": t.title,
                    "Pet": t.pet_name,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority,
                    "Recurrence": t.recurrence,
                }
                for i, t in enumerate(sorted_plan, start=1)
            ])

        # Full text explanation (includes skipped tasks)
        with st.expander("Full plan details"):
            st.text(scheduler.explain_plan())
