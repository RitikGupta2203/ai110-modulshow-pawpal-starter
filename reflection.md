# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Three Core User Actions:**

1. **Add a pet** — enter your name, your pet's name, and pick their species. Everything else in the app depends on this.

2. **Add care tasks** — describe what needs doing (e.g. "morning walk"), how long it takes, and how urgent it is. You can keep adding tasks until the list reflects a real day.

3. **Generate a schedule** — ask the app to figure out what actually fits today given your available time, get back an ordered list, and see a short explanation for why each task made the cut.


- Briefly describe your initial UML design.

I started with four classes. `Task` is the smallest unit — one thing the pet needs done. `Pet` owns a list of tasks and knows which ones are still pending. `Owner` ties everything together and holds how much time the person actually has today. `Scheduler` is the brain: it looks at all the pending tasks across all the owner's pets, picks the ones that fit in the time budget (highest priority first), and writes up a plain-language explanation of the result.

- What classes did you include, and what responsibilities did you assign to each?

- **`Task`** — stores the task name, duration, priority, and whether it's been done. Can mark itself complete.
- **`Pet`** — holds the pet's name and species, keeps a list of tasks, and can return only the unfinished ones.
- **`Owner`** — stores the person's name, their available minutes for the day, and their list of pets.
- **`Scheduler`** — takes an owner, builds an ordered plan that fits the time budget, and explains the choices.


**b. Design changes**

- Did your design change during implementation?

Yes, a few things changed after I reviewed the skeleton more carefully.

- If yes, describe at least one change and why you made it.

Adding `pet_name` to `Task`. I didn't think about it at first, but once the scheduler pulls all tasks from every pet into one flat list, you lose track of which task belongs to which animal. So if I wanted the explanation to say something like "Mochi's morning walk", there was no way to do that. Adding `pet_name` directly to the task fixed that without overcomplicating anything.

I also moved `available_minutes` into `Scheduler` instead of reading it only from `Owner`. The original design only stored it on the owner, which meant if you wanted to try a different time budget you'd have to rebuild the whole owner object. Letting the scheduler accept it as an optional override made more sense.

Two smaller things: I made `build_plan()` reset the plan list at the start so calling it twice doesn't double up tasks, and I added a check at the top of `explain_plan()` so it gives a clear message if you call it before building a plan, rather than just returning something confusing.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

**Tradeoff: greedy priority-first fill vs. optimal knapsack packing**

The scheduler sorts all pending tasks by priority (high → medium → low) and, within each tier, by duration (shortest first). It then walks the sorted list once and adds each task to the plan if it fits in the remaining time budget — stopping only when the budget is exhausted or all tasks have been considered. This is a greedy, single-pass algorithm.

The consequence is that the plan is not always the most time-efficient combination of tasks. For example, if the budget is 30 minutes and the pending tasks are `[high/25 min, high/20 min, medium/10 min]`, the greedy pass schedules only the 25-minute high-priority task (leaving 5 minutes unused), when the combination of `[20 min + 10 min = 30 min]` would fill the day completely and still cover a high-priority task.

A true 0/1 knapsack solver could find the optimal combination, but its worst-case runtime is O(n × W) where W is the budget in minutes — and for a pet-care app with a full-day budget (1440 minutes) and a realistic number of tasks, that overhead is unnecessary.

**Why this tradeoff is reasonable here:**

For a pet-care schedule, a guaranteed high-priority task (medication, feeding) being completed is worth more than squeezing maximum task-count into the day. A greedy priority-first approach ensures that the most critical care always gets scheduled first, which matches the real-world concern: a missed feeding matters more than five unused minutes. The algorithm is also O(n log n) due to sorting, which keeps the UI responsive even if the task list grows.

**Tradeoff reviewed with AI (readability vs. performance):**

When reviewing `conflict_warnings()`, a Copilot suggestion was to collapse the method into a single list comprehension using Python's walrus operator (`:=`) to filter out `None` start times inline:

```python
# AI-suggested version (more Pythonic)
return [
    f"WARNING ({'same pet' if a.pet_name == b.pet_name else 'cross-pet'}): ..."
    for a, b in self.detect_conflicts()
    if (sa := self._effective_start(a)) is not None
    and (sb := self._effective_start(b)) is not None
]
```

The version kept in the codebase uses a for-loop with named intermediate variables (`overlap_start`, `overlap_end`, `overlap_mins`, `scope`). The decision was to keep the for-loop because:

1. The walrus operator is unfamiliar to many readers and makes the `None` guard harder to spot.
2. The named variables (`overlap_start`, `overlap_end`) make the interval arithmetic self-documenting — removing them forces the reader to mentally re-derive the overlap calculation from inlined expressions.
3. The one genuine improvement from the AI review — that `_fmt()` was being redefined on every loop iteration — was extracted above the loop, giving the performance gain without sacrificing readability.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
