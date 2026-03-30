import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, filter_tasks


# ---------------------------------------------------------------------------
# Existing tests (unchanged)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=20, priority="high")
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting by time
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_tasks_by_start():
    """sort_by_time returns tasks in ascending start-time order."""
    owner = Owner("Jo", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    # Add tasks with explicit preferred start times (out of order)
    t_late = Task("Evening walk", 20, "medium", start_time=1080)   # 18:00
    t_early = Task("Morning feed", 10, "high", start_time=480)      # 08:00
    t_mid = Task("Midday play", 15, "low", start_time=720)          # 12:00
    for t in [t_late, t_early, t_mid]:
        pet.add_task(t)

    scheduler = Scheduler(owner, available_minutes=1200)
    scheduler.build_plan()
    ordered = scheduler.sort_by_time()

    starts = [scheduler._effective_start(t) for t in ordered]
    assert starts == sorted(starts), "Tasks should be sorted by ascending start time"


def test_sort_by_time_floating_tasks_assigned_sequential_starts():
    """Floating tasks (no start_time) get sequential start times from build_plan."""
    owner = Owner("Jo", available_minutes=60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)

    t1 = Task("Feed", 10, "high")
    t2 = Task("Play", 20, "medium")
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = Scheduler(owner)
    scheduler.build_plan()
    ordered = scheduler.sort_by_time()

    # First task starts at 0; second starts right after first ends
    assert scheduler._effective_start(ordered[0]) == 0
    assert scheduler._effective_start(ordered[1]) == ordered[0].duration_minutes


# ---------------------------------------------------------------------------
# Filtering by pet / status
# ---------------------------------------------------------------------------

def test_filter_tasks_by_pet():
    t1 = Task("Walk", 20, "high", pet_name="Mochi")
    t2 = Task("Feed", 10, "high", pet_name="Luna")
    result = filter_tasks([t1, t2], pet_name="Mochi")
    assert len(result) == 1
    assert result[0].pet_name == "Mochi"


def test_filter_tasks_by_status_pending():
    t1 = Task("Walk", 20, "high")
    t2 = Task("Feed", 10, "high")
    t2.mark_complete()
    result = filter_tasks([t1, t2], status="pending")
    assert result == [t1]


def test_filter_tasks_by_status_completed():
    t1 = Task("Walk", 20, "high")
    t2 = Task("Feed", 10, "high")
    t2.mark_complete()
    result = filter_tasks([t1, t2], status="completed")
    assert result == [t2]


def test_filter_tasks_combined():
    t1 = Task("Walk", 20, "high", pet_name="Mochi")
    t2 = Task("Feed", 10, "high", pet_name="Mochi")
    t3 = Task("Litter", 5, "medium", pet_name="Luna")
    t2.mark_complete()
    result = filter_tasks([t1, t2, t3], pet_name="Mochi", status="pending")
    assert result == [t1]


def test_filter_tasks_no_filters_returns_all():
    tasks = [Task("A", 10, "low"), Task("B", 5, "high")]
    assert filter_tasks(tasks) == tasks


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------

def test_next_occurrence_creates_pending_copy():
    original = Task("Daily walk", 20, "high", pet_name="Mochi", recurrence="daily")
    original.mark_complete()
    copy = original.next_occurrence()

    assert copy.is_completed is False
    assert copy.title == original.title
    assert copy.duration_minutes == original.duration_minutes
    assert copy.pet_name == original.pet_name
    assert copy.recurrence == original.recurrence


def test_next_occurrence_daily_sets_due_date_to_tomorrow():
    task = Task("Feed", 10, "high", recurrence="daily")
    nxt = task.next_occurrence()
    assert nxt.due_date == date.today() + timedelta(days=1)


def test_next_occurrence_weekly_sets_due_date_to_next_week():
    task = Task("Bath", 30, "medium", recurrence="weekly")
    nxt = task.next_occurrence()
    assert nxt.due_date == date.today() + timedelta(weeks=1)


def test_next_occurrence_raises_for_non_recurring():
    task = Task("One-off", 10, "low", recurrence="none")
    with pytest.raises(ValueError):
        task.next_occurrence()


# mark_task_complete — auto-spawn on the Pet

def test_mark_task_complete_one_off_returns_none():
    pet = Pet("Mochi", "dog")
    task = Task("Vet visit", 60, "high", recurrence="none")
    pet.add_task(task)
    result = pet.mark_task_complete(task)
    assert result is None
    assert task.is_completed is True
    assert len(pet.tasks) == 1    # no new task added


def test_mark_task_complete_daily_auto_spawns():
    pet = Pet("Mochi", "dog")
    daily = Task("Feed", 10, "high", recurrence="daily")
    pet.add_task(daily)

    next_task = pet.mark_task_complete(daily)

    assert daily.is_completed is True
    assert next_task is not None
    assert next_task.is_completed is False
    assert next_task.recurrence == "daily"
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert len(pet.tasks) == 2   # original + spawned


def test_mark_task_complete_weekly_auto_spawns():
    pet = Pet("Luna", "cat")
    weekly = Task("Bath", 20, "medium", recurrence="weekly")
    pet.add_task(weekly)

    next_task = pet.mark_task_complete(weekly)

    assert next_task.due_date == date.today() + timedelta(weeks=1)
    assert next_task.recurrence == "weekly"


def test_mark_task_complete_spawned_task_appears_in_plan():
    owner = Owner("Jo", available_minutes=60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    daily = Task("Feed", 10, "high", recurrence="daily")
    pet.add_task(daily)
    pet.mark_task_complete(daily)   # auto-spawns next occurrence

    scheduler = Scheduler(owner)
    scheduler.build_plan()
    titles = [t.title for t in scheduler.plan]
    assert "Feed" in titles


def test_spawn_recurring_tasks_adds_new_pending_tasks():
    pet = Pet("Mochi", "dog")
    daily = Task("Feed", 10, "high", recurrence="daily")
    one_off = Task("Vet visit", 60, "high", recurrence="none")
    pet.add_task(daily)
    pet.add_task(one_off)

    daily.mark_complete()
    one_off.mark_complete()

    new_tasks = pet.spawn_recurring_tasks()
    assert len(new_tasks) == 1                       # only daily is recurring
    assert new_tasks[0].title == "Feed"
    assert new_tasks[0].is_completed is False


def test_recurring_task_reappears_in_plan_after_spawn():
    owner = Owner("Jo", available_minutes=60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    daily = Task("Feed", 10, "high", recurrence="daily")
    pet.add_task(daily)
    daily.mark_complete()

    pet.spawn_recurring_tasks()

    scheduler = Scheduler(owner)
    scheduler.build_plan()
    titles = [t.title for t in scheduler.plan]
    assert "Feed" in titles


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """Two tasks whose time windows overlap should be reported as a conflict."""
    owner = Owner("Jo", available_minutes=1440)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    # Walk: 08:00–08:30  |  Feed: 08:15–08:25  → overlap
    walk = Task("Walk", 30, "high", start_time=480)   # 08:00
    feed = Task("Feed", 10, "high", start_time=495)   # 08:15
    pet.add_task(walk)
    pet.add_task(feed)

    scheduler = Scheduler(owner)
    scheduler.build_plan()
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert titles == {"Walk", "Feed"}


def test_detect_conflicts_no_overlap():
    """Back-to-back tasks should not be flagged as conflicts."""
    owner = Owner("Jo", available_minutes=1440)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    walk = Task("Walk", 30, "high", start_time=480)   # 08:00–08:30
    feed = Task("Feed", 10, "high", start_time=510)   # 08:30–08:40 — starts exactly when walk ends
    pet.add_task(walk)
    pet.add_task(feed)

    scheduler = Scheduler(owner)
    scheduler.build_plan()
    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_empty_plan():
    owner = Owner("Jo", available_minutes=30)
    scheduler = Scheduler(owner)
    scheduler.build_plan()
    assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# conflict_warnings — human-readable warning strings
# ---------------------------------------------------------------------------

def _make_scheduler_with_overlap(same_pet: bool) -> Scheduler:
    """Helper: build a scheduler with exactly one conflicting pair."""
    owner = Owner("Jo", available_minutes=1440)
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Task A: 08:00–08:30
    mochi.add_task(Task("Walk", 30, "high", start_time=480))

    if same_pet:
        # Task B overlaps on the same pet: 08:15–08:25
        mochi.add_task(Task("Feed", 10, "high", start_time=495))
    else:
        # Task B overlaps on a different pet: 08:15–08:25
        luna.add_task(Task("Vet check", 10, "high", start_time=495))

    s = Scheduler(owner)
    s.build_plan()
    return s


def test_conflict_warnings_returns_list_of_strings():
    s = _make_scheduler_with_overlap(same_pet=True)
    warnings = s.conflict_warnings()
    assert isinstance(warnings, list)
    assert all(isinstance(w, str) for w in warnings)


def test_conflict_warnings_same_pet_label():
    s = _make_scheduler_with_overlap(same_pet=True)
    warnings = s.conflict_warnings()
    assert len(warnings) == 1
    assert "same pet" in warnings[0]


def test_conflict_warnings_cross_pet_label():
    s = _make_scheduler_with_overlap(same_pet=False)
    warnings = s.conflict_warnings()
    assert len(warnings) == 1
    assert "cross-pet" in warnings[0]


def test_conflict_warnings_includes_overlap_duration():
    """The warning should state how many minutes the tasks overlap."""
    # Walk 08:00–08:30, Feed 08:15–08:25 → 10 min overlap
    s = _make_scheduler_with_overlap(same_pet=True)
    warnings = s.conflict_warnings()
    assert "10 min overlap" in warnings[0]


def test_conflict_warnings_includes_task_titles():
    s = _make_scheduler_with_overlap(same_pet=True)
    w = s.conflict_warnings()[0]
    assert "Walk" in w
    assert "Feed" in w


def test_conflict_warnings_exact_same_start_time():
    """Two tasks starting at exactly the same minute should produce a warning."""
    owner = Owner("Jo", available_minutes=1440)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Feeding",      10, "high", start_time=480))  # 08:00–08:10
    pet.add_task(Task("Morning walk", 20, "high", start_time=480))  # 08:00–08:20 — exact same start

    s = Scheduler(owner)
    s.build_plan()
    warnings = s.conflict_warnings()

    assert len(warnings) == 1
    assert "same pet" in warnings[0]
    assert "10 min overlap" in warnings[0]


def test_conflict_warnings_cross_pet_same_start_time():
    """Tasks on different pets at the same time should be flagged as cross-pet."""
    owner = Owner("Jo", available_minutes=1440)
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Grooming",  45, "medium", start_time=600))  # 10:00–10:45
    luna.add_task(Task("Vet check",  30, "high",   start_time=600))  # 10:00–10:30

    s = Scheduler(owner)
    s.build_plan()
    warnings = s.conflict_warnings()

    assert len(warnings) == 1
    assert "cross-pet" in warnings[0]
    assert "30 min overlap" in warnings[0]


def test_conflict_warnings_empty_when_no_conflicts():
    owner = Owner("Jo", available_minutes=1440)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", start_time=480))  # 08:00–08:30
    pet.add_task(Task("Feed", 10, "high", start_time=510))  # 08:30–08:40 back-to-back

    s = Scheduler(owner)
    s.build_plan()
    assert s.conflict_warnings() == []
