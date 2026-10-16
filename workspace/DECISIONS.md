# Decisions

A log of the decisions made across the sessions: what was chosen, why, what else was considered, and whether the decision still stands. The state at the end of each session is in `CHECKPOINTS.md`; the tool-by-tool record is in `TRANSCRIPT.md`.

**Status values:** **Active** (still how the project works), **Superseded** (replaced by a later decision, which is named), **Process** (a working rule, not a code choice).
**Provenance:** decisions from Sessions 1, 5, 6, 7, 8, 9, and 10 are *Direct* (made by the agent that did that session; Sessions 7 and 9 were first logged here from `TRANSCRIPT.md` by the Session 10 agent and were reviewed and re-marked by Agent B, who performed them). Decisions from Sessions 2-4 are *Reconstructed* and thinner, because only the logs survive. D34-D41 are *Direct* decisions from the Session 9 conversation after the session itself ended.

---

## Session 1: Scaffold

### D1. A static page filled by a script, no framework (Direct) - Active
Plain HTML with an empty `<ul id='items'>` that JavaScript populates. No build step, no libraries. *Why:* the whole project is built through a file-writing connector, so anything that needs installing or compiling would be hard to build and hard for the user to run. Opening `index.html` is enough.

### D2. Three markdown files as the memory between sessions (Direct) - Process, Active
`PROJECT_STATE.md` (what exists now), `PLAN_LOG.md` (what is done and what is next), and later `TRANSCRIPT.md` (how and why). *Why:* each session starts with no memory of the others, so the files are the only continuity. Every session reads them first and updates them last.

## Sessions 2-4: List, interaction, README (Reconstructed)

### D3. Fill the list from JavaScript, with the script at the end of `<body>` (Reconstructed) - Active
`app.js` creates the `<li>` elements and the script tag sits just before `</body>`. *Why:* the list exists in the DOM by the time the script runs, so no load-event handling is needed.

### D4. Click toggles an inline `line-through` (Reconstructed) - **Superseded** by D28
The Session 3 strike-through was written directly onto each element's style. *Why then:* simplest working approach. *Why replaced:* inline styles outrank stylesheet rules and forced `!important` later (see D16, D28).

### D5. Write the README for a reader with no technical background, and label what is not verified (Reconstructed) - Process, Active
Sections are tagged **[Verified]** or **[Reconstructed]**, and `server.py` is flagged as rebuilt. *Why:* the original `server.py` is not in the workspace, so presenting a rebuilt copy as the original would mislead. The labels let a reader know what to test first.

## Session 5: Transcript and git trouble

### D6. Mark every transcript entry Direct or Reconstructed, and never invent verbatim records (Direct) - Process, Active
Sessions 2-4 were summaries rebuilt from the logs, so they say so. *Why:* a transcript that looked complete but was partly guesswork would be worse than a labeled partial one. *Alternative rejected:* writing plausible prompts and tool calls for the missing sessions.

### D7. Record the git failure as it happened instead of hiding or papering over it (Direct) - Process, Active
Exit status 128 was logged with the number of attempts and the fact that the cause was never found. *Why:* the agent had no shell on the file server, so it could not diagnose the failure, and claiming a fix would have been false. The user was given concrete checks to run instead.

### D8. Leave `test.txt` alone, and tell the user it gets committed anyway (Direct) - Active
`test.txt` was unrelated to the project. `git_commit` stages everything with `git add .`, so it cannot be excluded, and the agent said so rather than deleting a file it did not create. It was later edited only because the user asked.

## Session 6: 100-item catalog (Agent A)

### D9. Hard-coded names with seeded random prices (Direct) - Active
The 100 names are written out per category; prices come from a seeded generator (mulberry32, seed 20261016). *Why:* guarantees 100 distinct, sensible names (no "Item 47"), and the page looks random but is identical every load, which makes it testable. *Alternatives rejected:* `Math.random()` (different every load, untestable) and generated placeholder names.

### D10. Category split and price ranges (Direct) - Active
Produce 15, Dairy 12, Bakery 10, Beverages 12, Pantry 15, Meat 10, Snacks 11, Frozen 8, Household 7 (total 100), each with its own price range. *Why:* a realistic spread; counts were checked by hand and by a runtime self-check that warns if the catalog is not 100 unique items.

### D11. Keep state on the data, and price as a string (Direct) - Active
Each item is an object with `id`, `name`, `category`, `price` (e.g. "$3.49"), `purchased`. A click flips the flag on the object, then updates the card. *Why:* the task specified these fields; keeping state in the data (not only in the page) is what later made filtering safe (D17).

### D12. Build elements with `createElement` and `textContent`, never `innerHTML` (Direct) - Active
*Why:* avoids any chance of markup injection and is simple to reason about. Cards are appended in one `DocumentFragment`.

### D13. Temporary inline styles in `app.js` (Direct) - **Superseded** by D28
No stylesheet existed yet, so minimal inline styles kept the cards readable, marked for removal in Session 7.

## Session 7: Styling (Agent B, Direct)

### D14. Name the file `style.css`, not `styles.css` (Direct) - Active
The Session 6 plan said `styles.css`; the Session 7 instructions said `style.css`. The instructions won and the discrepancy was written into `PLAN_LOG.md`, so the next agent would not look for the wrong name.

### D15. CSS grid with `auto-fill` and a 220px minimum, and `body` as the container (Direct) - Active
`repeat(auto-fill, minmax(220px, 1fr))` adapts the column count with no per-breakpoint rules; one phone breakpoint at 480px lowers the minimum to 160px. `index.html` had no wrapper element and the instructions asked for a centered container, so `body` itself got `max-width: 1200px; margin: 0 auto` rather than editing the markup. Inside each card the name takes the full first row and the badge and price share the second, because three items do not fit in a 220px card. A reduced-motion rule disables the hover animation. Colors, shadows, and radius are CSS variables so a later change is one edit.

### D16. Use `!important` to beat the inline styles, rather than touch `app.js` (Direct) - **Superseded** by D28
`app.js` was outside that session's instructions, so the stylesheet overrode the inline styles with `!important` on exactly the colliding properties, with a comment at the top of `style.css` explaining why, and the cause was written into the handoff for Session 8. *Alternative rejected:* editing `app.js` anyway, which would have exceeded the task. *Cost:* fragile CSS, removed in Session 10.

### D42. Category colors as one class per category, with a gray fallback (Direct) - Active
Each of the 9 categories has a `.badge-<name>` rule (light background, dark text of the same hue), and plain `.badge` supplies gray for anything unknown. *Why:* `app.js` already emitted `.badge-<category>` class names, so the stylesheet could target them with no JS change, and a new category degrades to gray instead of unstyled.

## Session 8: Search and filter (Agent A)

### D17. Derive the visible list from the data on every change (Direct) - Active
Filtering never modifies `groceryItems`. `renderList()` filters, builds fresh cards for the matches, and swaps them in with `replaceChildren`. Filtered-out cards are discarded, not hidden. *Why:* there is then one source of truth, so purchased marks cannot be lost. *Alternative rejected:* hiding and showing existing cards (state would live in the page and drift).

### D18. A shared `applyPurchasedState()` helper (Direct) - Active
Both the initial render and the click handler use it, so a card rebuilt after filtering is drawn in the right state. *Why:* one code path instead of two that can disagree.

### D19. Combine search and category with AND, trim and lowercase the query (Direct) - Active
An item shows only if its category matches and its name contains the search text. *Why:* the most expected behavior; an empty search matches everything.

### D20. Edit with targeted `str_replace`, and match the file as it actually is (Direct) - Process, Active
`app.js` was changed in two small replacements instead of a full rewrite, and the toolbar was inserted by matching the file's real single-quoted `<ul id='items'>` rather than the double-quoted form in the instructions. *Why:* a rewrite risks breaking working code; a mismatched match string fails.

### D21. Hand-write the dropdown options, and defer the cleanup (Direct) - Active (limitation)
The 9 `<option>`s are written in `index.html` as the instructions specified, so they must be kept in sync with `app.js` by hand (the Session 10 test checks they match). The inline-style cleanup was left for a later session because that session's instructions covered only search and filtering.

## Session 9: Polish and summary metrics (Agent B, Direct)

### D22. Sum prices in whole cents (Direct) - Active
Prices are strings like "$3.49", so they are converted to integer cents, added, and formatted back. *Why:* avoids floating-point errors such as `$0.30000000000000004`. The Session 10 test confirmed an exact total of $682.50 with all 100 marked.

### D23. Recompute the summary from the data each time (Direct) - Active
`updateSummary()` runs after every render and every click and recalculates from `groceryItems` instead of keeping a running total. *Why:* it cannot drift out of sync with the data. *Alternative rejected:* adding or subtracting on each click (a missed update would leave it wrong for good).

### D24. "Displayed" follows the filter; "Purchased" and the total do not (Direct) - Active
Purchased items hidden by a filter still count. *Why:* the totals describe the whole list, while "Displayed" describes the current view.

### D25. Define "complete" as written and logged, not tested (Direct) - Active (and disclosed)
Session 9 declared the planned milestones 100% done while saying plainly that nothing had been run, and listed the untested items. That honesty is what made the Session 10 follow-up possible.

### D34. Keep the old `#itemCount` and add the summary bar next to it (Direct) - Active
The Session 8 "Showing: N items" count stays in the toolbar, so it and the summary's "Displayed" report the same number. *Why:* the instructions asked for a new bar, not a change to Session 8's markup, and removing a working element risked breaking the filter code that updates it. *Cost:* a small redundancy.

### D35. Mobile and touch choices: stack at 480px, 44px inputs, 16px text (Direct) - Active
At 480px and below the toolbar becomes one column and the summary a vertical list; the existing phone breakpoint was extended instead of adding a new one. Inputs are 44px tall for touch, and 16px text keeps iOS from zooming on focus. *Why:* fewer breakpoints to keep in sync, and these are common touch-usability defaults. Never verified visually (see D27).

### D36. Keep `README.md` honest while rewriting it (Direct) - Process, Active
The Session 9 README labeled what is verified versus reconstructed, carried forward the earlier setup sections, and listed known limitations (inline styles, no empty state, never run in a browser). *Why:* a README that sounded finished would hide that nothing had been tested. This was overwritten later (D38).

## Session 10: Follow-ups, tests, and records

### D26. Audit first, adopt existing work, redo nothing (Direct) - Process, Active
At the start the workspace already held Session 9's work, which the last logs this agent had read did not describe. The agent read the files and git status before editing and built on what was there. *Why:* redoing it would have overwritten another agent's work.

### D27. Test headlessly because no browser is available, and prove the test can fail (Direct) - Active
The real `index.html` and `app.js` were run in jsdom and driven by simulated typing and clicks (50 checks, all passed). Two deliberately broken copies were then confirmed to fail exactly the right tests. *Why:* a test that cannot fail proves nothing. *Limit, stated everywhere:* jsdom does not paint, so appearance is still unverified.

### D28. `app.js` sets class names only; `style.css` owns all styling (Direct) - Active
Replaces D4, D13, and D16. All inline styles and all 20 `!important` flags were removed. The category colors still beat the base `.badge` because they come later with equal specificity. One visual difference: the old inline strike-through also crossed out the badge; the stylesheet crosses out only the name and price and greys the badge, which is what Session 7 designed.

### D29. Empty state uses the `hidden` attribute, with no `display` in its CSS (Direct) - Active
Setting `display` on `.empty-state` would override `hidden` and the message would never disappear.

### D30. Rename the heading and reword the search placeholder (Direct) - Active
"Items" became "Grocery Catalog", and "Search 100 groceries..." became "Search groceries by name...". *Why:* the plan listed both, and the new placeholder does not go stale if the catalog size changes. This replaces the exact placeholder text given in Session 8's instructions.

### D31. Do not trust "Commit complete"; check `git_status` after each commit (Direct) - Process, Active
The commit tool returns no hash, and `git_status` at the start of Session 10 showed Sessions 5-9 staged but uncommitted. Logs and checkpoints therefore describe file state, not confirmed commits, and say so. See "Git history" in `CHECKPOINTS.md`. The cause of the unreliable message was later verified from `server.py` (D40).

### D32. Fill the two reserved files (Direct) - Active
`DECISIONS.md` and `CHECKPOINTS.md` had been empty since Session 4. They now hold the design reasoning and the per-session state, so `TRANSCRIPT.md` can stay a record of tool use.

### D33. Keep the test out of the workspace for now (Direct) - Active, open
The test needs Node and jsdom, which the user did not ask for. It is described in the logs but stays in the agent's sandbox; saving it into the workspace is listed as an open item.

---

## Session 9 conversation, after the session: README, git, layout, and these records (Direct)
Numbers follow the order the decisions were recorded, not strict chronology (D42 sits under Session 7).

### D37. Use the user's README text as supplied; clean only mechanical artifacts (Direct) - Active
The user pasted a course-document README and asked for the author to be changed to Marcky Emmanuelle C. Aranas and sections 8 and 9 to be left out. Only formatting damage was repaired (citation tags, a stray `<FollowUp>` line, broken code fences, a doubled clone link, a web-search URL standing in for the ngrok dashboard). *Alternative rejected:* rewriting the content freely, which would have replaced the user's text with the agent's.

### D38. Replacing the README supersedes the Session 9 grocery documentation (Direct) - Active
The user asked for the README to be updated with the supplied text, so the grocery-catalog sections (features, metric behavior, code map, limitations) were overwritten rather than merged, and the user was told so. This replaces D36's output but not its principle. *Open:* the README is currently missing from the workspace listing.

### D39. Flag false claims, then correct them; never write invented evidence into the project (Direct) - Process, Active
The supplied text contained a `git log` block with invented hashes, "7 categories" (the catalog has 9), a wrong Session 5, "two complete multi-session runs", and testing and deployment claims the logs do not support. The agent first listed them for the user, and corrected them when asked: the fake log became the real commit-message pattern with an accuracy note, the testing row now states what was actually done, and a scope note says the Docker/ngrok/`server.py` material is unverified. *Left as written, but flagged:* "production-grade", "immutable audit trail", rubric-criterion headings, and the Docker/MCP 2.x details, because they cannot be checked from here. *Why:* a document submitted for grading should not contain fabricated evidence, and the user is the one who bears the risk.

### D40. Diagnose git from its own files, and ask before changing configuration or server code (Direct) - Process, Active
The agent read `.git/logs/HEAD` and `.git/config` through the file server and later `server.py`. Findings: one commit only (`initialize files`), no `user.name`/`user.email`, `origin` at GitHub, and a `git_commit` that returns "Commit complete." whenever stdout is empty, which hides failures. The agent reported the verified cause of the misleading message, labeled the missing identity as an unconfirmed hypothesis, and offered to write the identity into `.git/config` instead of doing it. For the rejected push it advised fetch, inspect, `pull --rebase`, and no force-push. *Why:* editing git's settings or the server code changes how every later commit behaves and is the user's call; a force-push could destroy remote work.

### D41. When told to "fix everything", inspect first and take no destructive action (Direct) - Process, Active
The file server's view had changed (see `CHECKPOINTS.md`, Checkpoint 11d): duplicate files with different contents (two `test.txt` files, root and `workspace/` copies of the stylesheet and transcript) and tracked files in two layouts. Moving, merging, or deleting them, or rewriting `server.py`, could not be undone from the file server and might have discarded a newer version. The agent made no changes before the user redirected. *Alternative rejected:* copying the root files into `workspace/` and deleting the originals on a guess about which was newest.

### D43. Write only `CHECKPOINTS.md` and `DECISIONS.md` in this review, and say what is left stale (Direct) - Process, Active
The user limited the review to those two files. The agent read everything it needed but wrote only to them, and recorded in the open items that `PROJECT_STATE.md`, `PLAN_LOG.md`, `TRANSCRIPT.md`, and `README.md` do not yet reflect Checkpoint 11 or the git root cause. Existing Session 10 text was edited only where it was wrong (provenance of Sessions 7 and 9) or incomplete (Sessions 7 and 9 detail, the git root cause, open items); nothing else was removed.

### D44. Re-mark Sessions 7 and 9 as Direct (Direct) - Process, Active
The Session 10 agent could only see the logs, so it labeled those two sessions *Logged*. The agent that performed them can vouch for the tool calls and results, so the entries were upgraded and filled in with details from the actual session. *Limit:* the Session 7 and 9 verification is still inspection only.

---

## Decisions that were reversed
| Original | Replaced by | Reason |
|----------|-------------|--------|
| D4 inline strike-through | D28 class-based styling | Inline styles outrank the stylesheet |
| D13 temporary inline styles | D28 | The stylesheet now exists |
| D16 `!important` overrides | D28 | Their cause was removed |
| Exact placeholder "Search 100 groceries..." (Session 8 instructions) | D30 | Avoids a hard-coded count |
