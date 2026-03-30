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

The scheduler considers three constraints: **time budget** (how many minutes the owner has available today), **priority** (high / medium / low), and **time-of-day preferences** (an optional start time the owner can pin a task to).

Priority was treated as the most important constraint because it directly maps to animal welfare — a missed medication or feeding has real consequences, while a missed grooming session does not. Time budget came second because the whole point of the app is to produce a plan that actually fits into a real day. Time-of-day preferences were added last as an optional refinement: most tasks don't need to happen at a specific minute, but some (like a vet appointment) do, and the scheduler needs to respect that without breaking the rest of the plan.

The decision to rank priority above time efficiency was deliberate. An algorithm that maximised task-count at the cost of skipping a high-priority item would be wrong for this domain, even if it looked better on paper.

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

AI tools — primarily VS Code Copilot and Claude Code — were used across every phase of this project, but with a different purpose at each stage.

**Design brainstorming:** Early on, Copilot's chat was used to pressure-test the UML before writing any code. Prompts like "what happens when the scheduler pulls all tasks into a flat list — how does it know which pet each task belongs to?" surfaced the `pet_name` gap in the original design before it became a bug. This kind of pre-implementation interrogation was more valuable than any code suggestion.

**Incremental implementation:** Once classes were stubbed, Copilot's inline completions were useful for filling in repetitive patterns — dataclass field declarations, list comprehensions, f-string formatting. These suggestions were accepted quickly because they involved no design decisions.

**Refactoring and algorithm review:** The most effective prompts were specific and bounded: "Here is `conflict_warnings()`. How could this method be simplified for readability or performance?" A scoped question about one method produced a focused, evaluable answer. Open-ended prompts like "improve my scheduler" produced suggestions that ignored domain context.

**Debugging:** Copilot's inline chat was used to diagnose the `build_plan()` bug where overlapping pinned tasks were silently skipped instead of being included and flagged. The AI correctly identified that the `if pinned_task.start_time < cursor: continue` guard was too aggressive, and the fix — keeping the task in the plan and letting `detect_conflicts()` report it — came from that conversation.

The most helpful prompt pattern was: **state what the method is supposed to do, show the current code, and ask a specific question**. Vague prompts produced generic answers; precise prompts produced useful ones.

**b. Judgment and verification**

**The suggestion that was rejected:** When reviewing `conflict_warnings()`, Copilot suggested collapsing the for-loop into a single list comprehension using Python's walrus operator (`:=`) to handle the `None` guard inline. The suggestion was syntactically correct and arguably more "Pythonic."

It was rejected for two reasons. First, walrus operators inside list comprehension conditions are an uncommon pattern — a reader unfamiliar with them would have to stop and decode the guard before understanding what the comprehension produces. Second, the intermediate variables (`overlap_start`, `overlap_end`, `overlap_mins`, `scope`) were doing real documentation work: they gave names to the interval arithmetic so the algorithm could be read as prose. Inlining those expressions into a single f-string would have made the logic opaque.

The one genuine improvement from the review — `_fmt()` was being redefined as a new function object on every loop iteration — was extracted above the loop. This gave the performance benefit without touching readability.

**How the suggestion was evaluated:** The test for any AI refactoring suggestion was: *can a developer who has never seen this file understand what this code does in under 30 seconds?* The walrus comprehension failed that test. The `_fmt` hoist passed it. Running the full 30-test suite after each change confirmed nothing broke.

**Which Copilot features were most effective:**

| Feature | How it was used |
|---|---|
| **Inline chat on a selected method** | Scoped refactoring and algorithm review — most precise results |
| **Chat sidebar for design questions** | Pre-implementation reasoning about class responsibilities and edge cases |
| **Inline completions** | Repetitive boilerplate (dataclass fields, f-strings, test scaffolding) |
| **"Generate documentation" action** | First-draft docstrings on new methods, then manually tightened for accuracy |

**How separate chat sessions helped:** Each implementation phase — data model, scheduling algorithm, conflict detection, recurring tasks — was handled in its own chat session. This prevented earlier context from polluting later suggestions. When working on `conflict_warnings()`, the session only contained code relevant to that method; Copilot's suggestions were therefore about that method, not about unrelated classes it had seen earlier. Context pollution is a real problem with AI assistants: the more prior conversation exists, the more likely a suggestion will reference something that no longer applies.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers five areas across 30 tests:

- **Sorting** — `sort_by_time()` returns tasks in ascending order; floating tasks get sequential slots starting at minute 0.
- **Recurring tasks** — completing a daily task spawns a copy due tomorrow; weekly advances by 7 days; one-off tasks return `None` and add nothing; calling `next_occurrence()` on a one-off raises `ValueError`.
- **Conflict detection** — overlapping windows are flagged; back-to-back tasks are not; exact same-start produces one conflict; cross-pet conflicts carry the right label.
- **Filtering** — `filter_tasks()` narrows by pet name, status, or both; an unknown pet name returns an empty list cleanly.
- **Core behaviour** — `mark_complete()` flips status; `add_task()` stamps the pet name; `build_plan()` respects the budget and lists skipped tasks separately.

These tests matter because the scheduler's output directly affects animal care decisions. A bug that silently drops a high-priority task or misreports a conflict is a real-world problem, not just a unit-test failure.

**b. Confidence**

**4 / 5.** All 30 tests pass across happy paths and key edge cases (zero-task pets, exact boundary times, budget overflow, cross-pet conflicts). The missing point reflects two gaps: there are no UI-layer integration tests (the Streamlit layer is untested), and there are no persistence tests since the app holds all state in memory per session. If the app were to add user accounts or a database, those areas would need coverage first.

---

## 5. Reflection

**a. What went well**

The scheduling logic turned out cleaner than expected. Separating tasks into *pinned* (user-set start time) and *floating* (auto-assigned) made `build_plan()` easy to reason about, and storing scheduler-assigned times in `_assigned_times` instead of mutating `Task` objects kept the data model honest. The conflict detection also felt satisfying — the interval-overlap formula is simple, the warnings are readable, and the method never crashes regardless of what it's handed.

**b. What you would improve**

The `available_minutes` budget counts from minute 0 (midnight), which means a task pinned at 08:00 uses 480 minutes of budget before a single minute of care is delivered. A `day_start` offset parameter on `Scheduler` would fix this and make the time model match how people actually think about their day. I would also add a proper Enum for `priority` — using raw strings means a typo like `"High"` silently breaks the sort without any error message.

**c. Key takeaway**

The most important thing learned was that **AI is a fast junior developer, not an architect**. It can write correct code quickly, suggest patterns, and catch obvious inefficiencies. But it does not know which tradeoffs matter for your domain. When Copilot suggested the walrus-operator list comprehension, it was technically right — the code was shorter and faster. But it didn't know that this codebase is a teaching project where readability outweighs cleverness, or that the named variables were doing documentation work. Making that call was the architect's job, not the AI's. The skill is knowing when to accept a suggestion, when to take only part of it, and when to reject it entirely — and being able to explain why.

---

## 6. AI Strategy — VS Code Copilot

**Which Copilot features were most effective?**

Inline chat on a selected method was the most useful feature. Highlighting `conflict_warnings()` and asking "how could this be simplified?" gave a focused answer about that specific method. The sidebar chat was better for design questions before writing code. Inline completions saved time on repetitive boilerplate but needed more review for logic-heavy code.

**One AI suggestion that was rejected:**

Copilot suggested replacing the for-loop in `conflict_warnings()` with a list comprehension using walrus operators to filter `None` start times inline. It was rejected because the named intermediate variables (`overlap_start`, `overlap_end`, `overlap_mins`) made the interval arithmetic readable without needing to mentally reconstruct it. The one improvement that was accepted from that session — hoisting `_fmt()` above the loop so it isn't recreated on every iteration — gave a real gain with no readability cost.

**How separate chat sessions helped:**

Each feature phase had its own session. This meant Copilot's suggestions were always about the code in front of it, not about earlier classes or design decisions it had seen in a different context. When the conflict detection session started, it only knew about `Scheduler` and `Task` — not about `Pet.spawn_recurring_tasks()` or the Streamlit UI. The suggestions stayed relevant and specific.

**What being the "lead architect" means when working with AI:**

The AI proposes; you decide. Copilot can generate code faster than you can type it, but it has no stake in whether the design is maintainable, whether the tradeoffs fit the domain, or whether a future developer will understand what it wrote. Every suggestion is an offer, not an instruction. The architect's job is to evaluate each offer against the goals of the system — readability, correctness, testability — and either accept it, modify it, or reject it with a reason. Delegating that judgment to the AI is where projects go wrong.
