import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

# ---------------------------------------------------------------------------
# Owner setup — persisted in session so it survives every rerun
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=60)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)

# ---------------------------------------------------------------------------
# Add a pet — calls Pet() and owner.add_pet()
# ---------------------------------------------------------------------------
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    pet = Pet(name=pet_name, species=species)
    st.session_state.owner.add_pet(pet)
    st.success(f"{pet_name} ({species}) added!")

# Show registered pets
if st.session_state.owner.pets:
    st.write("Registered pets:", ", ".join(p.name for p in st.session_state.owner.pets))

st.divider()

# ---------------------------------------------------------------------------
# Add a task — calls Task() and pet.add_task()
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

    pet_options = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign to pet", pet_options)

    if st.button("Add task"):
        selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)
        task = Task(title=task_title, duration_minutes=int(duration), priority=priority)
        selected_pet.add_task(task)  # stamps pet_name automatically
        st.success(f"Task '{task_title}' added to {selected_pet_name}!")

    # Show all pending tasks across all pets
    all_pending = st.session_state.owner.get_all_pending_tasks()
    if all_pending:
        st.write("Current tasks:")
        st.table([
            {"pet": t.pet_name, "task": t.title, "duration (min)": t.duration_minutes, "priority": t.priority}
            for t in all_pending
        ])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule — calls Scheduler.build_plan() and explain_plan()
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_tasks = st.session_state.owner.get_all_pending_tasks()
    if not all_tasks:
        st.warning("Add some tasks before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner, available_minutes=int(available_minutes))
        scheduler.build_plan()
        st.success(f"Schedule built — {scheduler.get_total_duration()} of {int(available_minutes)} min used.")
        st.text(scheduler.explain_plan())
