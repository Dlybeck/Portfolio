---
id: "04"
title: Honor accessible content and motion preferences
status: ready-for-agent
phase: 1
blocked_by:
  - "03"
---

# Honor accessible content and motion preferences

## Context

The portfolio should retain its default motion and visual personality while supporting visitors who already opt into reduced motion at the operating-system or browser level. Its documents also need useful names and alternatives without adding a separate accessibility mode or visible instructions.

## Requirements

- Give meaningful content images useful text alternatives.
- Give decorative images empty alternatives so they are skipped by assistive technology.
- Give embedded document frames descriptive titles.
- Ensure interactive controls have accurate accessible names that reflect their current action.
- Respect the visitor's reduced-motion preference across Board movement, document transitions, and incidental animation.
- Keep the existing motion and appearance unchanged for visitors who have not requested reduced motion.
- Do not add a separate accessibility toggle or mode.
- Do not replace the self-discovered navigation with explanatory instructions.
- Add repeatable checks for missing image alternatives, frame titles, control names, and reduced-motion behavior.

## Suggested approach

Classify media by purpose before assigning alternatives, then introduce a small shared motion policy used by both the Board and documents. Validate the reduced-motion branch explicitly instead of globally weakening the canonical animation.

## Done when

- Meaningful media, decorative media, frames, and controls pass an accessibility-name audit.
- Reduced-motion preference removes or substantially shortens disorienting transitions without hiding content or breaking navigation.
- Default-preference visual comparison shows no unintended motion or styling regression.
- Keyboard, pointer, and touch interactions continue to pass after the accessibility changes.

