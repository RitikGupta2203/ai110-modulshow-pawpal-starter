from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, filter_tasks

# ---------------------------------------------------------------------------
# Setup — 1440 min = full day budget so time-of-day start_times are meaningful
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=1440)

mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

# --- Tasks added intentionally OUT OF ORDER (evening first, morning last) ---
# Mochi
mochi.add_task(Task("Evening walk",  duration_minutes=30, priority="medium", start_time=1020))  # 17:00
mochi.add_task(Task("Playtime",      duration_minutes=25, priority="medium"))                    # floating
mochi.add_task(Task("Feeding",       duration_minutes=10, priority="high",   start_time=480))   # 08:00
mochi.add_task(Task("Morning walk",  duration_minutes=20, priority="high",   start_time=485))   # 08:05 → overlaps Feeding → conflict

# Luna — recurring tasks with due dates set for today
luna.add_task(Task("Brush coat",       duration_minutes=15, priority="low",
                   recurrence="daily",  due_date=date.today()))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="high",
                   recurrence="weekly", due_date=date.today(), start_time=540))  # 09:00

owner.add_pet(mochi)
owner.add_pet(luna)

SEP = "=" * 56

# ---------------------------------------------------------------------------
# 1. Filter by pet name
# ---------------------------------------------------------------------------
all_tasks = owner.get_all_tasks()

print(SEP)
print("  FILTER: Mochi's tasks only")
print(SEP)
for t in filter_tasks(all_tasks, pet_name="Mochi"):
    print(f"  {t}")

print()
print(SEP)
print("  FILTER: Luna's tasks only")
print(SEP)
for t in filter_tasks(all_tasks, pet_name="Luna"):
    print(f"  {t}")

# ---------------------------------------------------------------------------
# 2. Filter by status
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  FILTER: all pending tasks (before any completions)")
print(SEP)
for t in filter_tasks(all_tasks, status="pending"):
    print(f"  {t}")

# ---------------------------------------------------------------------------
# 3. mark_task_complete — daily task auto-spawns tomorrow's copy
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  COMPLETING RECURRING TASKS  (mark_task_complete)")
print(SEP)

brush_task   = luna.tasks[0]   # Brush coat — daily
litter_task  = luna.tasks[1]   # Litter box clean — weekly

next_brush  = luna.mark_task_complete(brush_task)
next_litter = luna.mark_task_complete(litter_task)

print(f"  Marked done : {brush_task.title!r} ({brush_task.recurrence})")
print(f"  Next due    : {next_brush.due_date}  "
      f"(today + timedelta(days=1) = {date.today() + timedelta(days=1)})")

print()
print(f"  Marked done : {litter_task.title!r} ({litter_task.recurrence})")
print(f"  Next due    : {next_litter.due_date}  "
      f"(today + timedelta(weeks=1) = {date.today() + timedelta(weeks=1)})")

# ---------------------------------------------------------------------------
# 4. Filter after completion — completed vs pending
# ---------------------------------------------------------------------------
all_tasks = owner.get_all_tasks()   # refresh after spawning

print()
print(SEP)
print("  FILTER: completed tasks (after marking)")
print(SEP)
for t in filter_tasks(all_tasks, status="completed"):
    print(f"  {t}")

print()
print(SEP)
print("  FILTER: pending tasks (spawned occurrences appear here)")
print(SEP)
for t in filter_tasks(all_tasks, status="pending"):
    print(f"  {t}")

# ---------------------------------------------------------------------------
# 5. Filter combined — Luna's pending only
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  FILTER: Luna's pending tasks only")
print(SEP)
for t in filter_tasks(all_tasks, pet_name="Luna", status="pending"):
    print(f"  {t}")

# ---------------------------------------------------------------------------
# 6. Build schedule → sort_by_time
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner)
scheduler.build_plan()

print()
print(SEP)
print("  SORTED SCHEDULE  (sort_by_time)")
print(SEP)
print(f"  {'#':<4} {'Start':<7} {'Task':<22} {'Pet':<8} {'Dur':>4}  {'Pri':<8} {'Recur':<8} {'Due'}")
print(f"  {'-'*4} {'-'*7} {'-'*22} {'-'*8} {'-'*4}  {'-'*8} {'-'*8} {'-'*12}")
for i, task in enumerate(scheduler.sort_by_time(), start=1):
    start = scheduler._effective_start(task)
    h, m  = divmod(start, 60) if start is not None else (0, 0)
    recur = task.recurrence if task.recurrence != "none" else "—"
    due   = str(task.due_date) if task.due_date else "—"
    print(
        f"  {i:<4} {h:02d}:{m:02d}  "
        f"{task.title:<22} {task.pet_name:<8} {task.duration_minutes:>4}m  "
        f"{task.priority:<8} {recur:<8} {due}"
    )

# ---------------------------------------------------------------------------
# 7a. Conflict detection — existing partial overlap (Feeding vs Morning walk)
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  CONFLICT DETECTION — partial overlap (existing)")
print(SEP)
for w in scheduler.conflict_warnings():
    print(f"  {w}")

# ---------------------------------------------------------------------------
# 7b. Same-time conflicts — same pet AND cross-pet, added to a fresh scheduler
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  CONFLICT DETECTION — exact same-time scenarios")
print(SEP)

conflict_owner = Owner("Jordan", available_minutes=1440)
cp_mochi = Pet("Mochi", "dog")
cp_luna  = Pet("Luna",  "cat")

# Same pet, same start time
cp_mochi.add_task(Task("Feeding",      duration_minutes=10, priority="high",   start_time=480))  # 08:00
cp_mochi.add_task(Task("Morning walk", duration_minutes=20, priority="high",   start_time=480))  # 08:00 — exact same time, same pet

# Different pets, same start time
cp_luna.add_task(Task("Vet check",     duration_minutes=30, priority="high",   start_time=600))  # 10:00
cp_mochi.add_task(Task("Grooming",     duration_minutes=45, priority="medium", start_time=600))  # 10:00 — exact same time, cross-pet

# No conflict — back-to-back, should be clean
cp_luna.add_task(Task("Brush coat",    duration_minutes=15, priority="low",    start_time=660))  # 11:00 starts when Vet check ends

conflict_owner.add_pet(cp_mochi)
conflict_owner.add_pet(cp_luna)

cs = Scheduler(conflict_owner)
cs.build_plan()

warnings = cs.conflict_warnings()
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts found.")

print()
print(f"  (back-to-back Vet check / Brush coat should be clean)")
back_to_back = [
    w for w in warnings
    if "Brush coat" in w or "Vet check" in w
    if "Brush coat" in w and "Vet check" in w
]
print(f"  Brush coat vs Vet check flagged: {bool(back_to_back)}")

# ---------------------------------------------------------------------------
# 8. Full explain_plan (original scheduler)
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  FULL PLAN  (explain_plan — original schedule)")
print(SEP)
print(scheduler.explain_plan())
print(SEP)
