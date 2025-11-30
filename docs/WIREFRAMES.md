# Speckit Mobile Dashboard - Wireframes

**Device:** Mobile (iPhone/Android)
**Orientation:** Portrait
**Theme:** Dark Mode (Dev)

---

## 1. Home / Active Session
*The entry point. Shows current status and quick actions.*

```text
+---------------------------------------+
|  [=]  Speckit Dashboard      (Claude)v|  <-- Model Switcher (Dropdown)
+---------------------------------------+
|                                       |
|  CURRENT GOAL                         |
|  "Add a dark mode toggle to navbar"   |
|                                       |
|  +---------------------------------+  |
|  |  PHASE 1: SPECIFICATION         |  |
|  |  [Status: APPROVED]             |  |
|  |  (Tap to view details) >        |  |
|  +---------------------------------+  |
|                                       |
|  +---------------------------------+  |
|  |  PHASE 2: PLANNING              |  |
|  |  [Status: IN PROGRESS...]       |  |
|  |                                 |  |
|  |  > Analyzing codebase...        |  |
|  |  > Identifying styled-components|  |
|  |                                 |  |
|  |  [ Stop ]      [ View Live ]    |  |
|  +---------------------------------+  |
|                                       |
|  +---------------------------------+  |
|  |  PHASE 3: TASKS                 |  |
|  |  [Status: PENDING]              |  |
|  +---------------------------------+  |
|                                       |
+---------------------------------------+
|  [+] New Goal      [#] History        |
+---------------------------------------+
```

---

## 2. The "Phase Card" (Detail View) - PLANNING
*What happens when you tap "View Live" or interact with a phase. This is the "Scoped Interaction".*

```text
+---------------------------------------+
|  < Back       PLANNING       (Claude)v| <-- Switcher LOCKED (Busy)
+---------------------------------------+
|                                       |
|  PROPOSED PLAN:                       |
|                                       |
|  1. Modify `static/css/base.css`      |
|     - Add CSS variables for colors    |
|                                       |
|  2. Edit `templates/navbar.html`      |
|     - Add toggle button icon          |
|                                       |
|  3. Create `static/js/theme.js`       |
|     - Handle click event              |
|     - Persist to localStorage         |
|                                       |
|  +---------------------------------+  |
|  | AI: "I noticed you use Bootstrap|  |
|  | should I use their built-in     |  |
|  | theme toggler classes?"         |  |
|  +---------------------------------+  |
|                                       |
+---------------------------------------+
| [ Yes, use Bootstrap ] [ No, custom ] | <-- Quick Actions (Bubbles)
| [ Chat Input...                     ] | <-- Refine manually
+---------------------------------------+
```

---

## 3. The "Execution View" (IMPLEMENTATION)
*When the AI is writing code. Needs to be readable on a small screen.*

```text
+---------------------------------------+
|  < Back      IMPLEMENTING    (Claude)v| <-- Switcher LOCKED
+---------------------------------------+
|                                       |
|  PROGRESS: [|||||||||||......] 65%    |
|                                       |
|  CURRENT TASK:                        |
|  > Editing `static/js/theme.js`       |
|                                       |
|  +---------------------------------+  |
|  | LOG STREAM                      |  |
|  | $ sed -i 's/light/dark/g'...    |  |
|  | $ git add static/js/theme.js    |  |
|  | > Running lint check...         |  |
|  | < Lint passed.                  |  |
|  +---------------------------------+  |
|                                       |
|  PENDING TASKS:                       |
|  [ ] Update base.html                 |
|  [ ] Verify persistence               |
|                                       |
+---------------------------------------+
|          [ PAUSE ]   [ ABORT ]        |
+---------------------------------------+
```

---

## 4. The "Safe Swap" Scenario
*How switching models works between phases.*

**Screen:** Plan Phase Completed.

```text
+---------------------------------------+
|  < Back       PLANNING       (Claude)v| <-- Switcher ACTIVE (Safe Point)
+---------------------------------------+
|                                       |
|  PLAN STATUS: FINALIZED               |
|                                       |
|  [ File List Summary... ]             |
|                                       |
|  NOTE: You can switch models now.     |
|  The plan is saved to disk.           |
|  The next model will read `PLAN.md`.  |
|                                       |
+---------------------------------------+
| User Taps Dropdown -> Selects Gemini  |
+---------------------------------------+
|                                       |
|  < Back       PLANNING       (Gemini)v|
|                                       |
|  > Gemini initializing...             |
|  > Reading context from PLAN.md...    |
|  > Ready to generate tasks.           |
|                                       |
+---------------------------------------+
|        [ PROCEED TO TASKS ]           |
+---------------------------------------+
```
