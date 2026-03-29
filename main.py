from pawpal_system import Task, Pet, Owner, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=60)

mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")

# --- Tasks for Mochi ---
mochi.add_task(Task(title="Morning walk", duration_minutes=20, priority="high"))
mochi.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
mochi.add_task(Task(title="Playtime", duration_minutes=25, priority="medium"))

# --- Tasks for Luna ---
luna.add_task(Task(title="Litter box clean", duration_minutes=10, priority="high"))
luna.add_task(Task(title="Brush coat", duration_minutes=15, priority="low"))

# --- Register pets with owner ---
owner.add_pet(mochi)
owner.add_pet(luna)

# --- Generate schedule ---
scheduler = Scheduler(owner)
scheduler.build_plan()

# --- Print results ---
print("=" * 40)
print("       TODAY'S SCHEDULE")
print("=" * 40)
print(scheduler.explain_plan())
print("=" * 40)
