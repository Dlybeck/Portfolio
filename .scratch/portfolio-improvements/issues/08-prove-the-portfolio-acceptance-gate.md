---
id: "08"
title: Prove the portfolio acceptance gate
status: ready-for-agent
phase: 2
blocked_by:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
---

# Prove the portfolio acceptance gate

## Context

The two phases converge on one portfolio: a trustworthy, self-guided Board with an inclusive professional discovery layer and a safe development space for visual experimentation. This ticket produces the integrated evidence needed for owner review. It does not publish or deploy the result.

## Requirements

- Verify the canonical experience at representative desktop and phone viewports against the approved baseline.
- Verify pointer and touch navigation has not regressed.
- Verify every Board Neighborhood exposes no more than the Parent, three Children, and centered Section.
- Verify direct content destinations restore the correct Board location and open the intended document.
- Verify visible internal and external links and all Home, Open, Close, Back, and nested controls.
- Verify the complete keyboard focus and Escape behavior defined for the Board hierarchy.
- Verify reduced motion changes behavior only when the visitor has opted into it.
- Validate canonical, page, social, and Person metadata and confirm no private information or excluded performance claims appear there.
- Verify the development theme selector is absent or unusable in a deployment-equivalent build.
- Compare the canonical theme with the alternate experiment without treating the experiment as approved.
- Produce a concise pass/fail receipt with reproducible commands, environment details, and any owner decisions still required.
- Do not commit, push, publish, or deploy as part of this ticket without separate authorization.

## Suggested approach

Run the automated checks contributed by each preceding ticket, then exercise one shared browser matrix that covers the combined state transitions and viewport requirements. Capture only evidence that affects the release decision and distinguish defects from optional theme feedback.

## Done when

- Every requirement above has a recorded pass, an actionable failure, or an explicit owner disposition.
- The canonical experience has no unresolved regression against the approved interaction and visual baseline.
- The experimental theme has a comparison result but remains non-production.
- The owner receives one reproducible acceptance receipt and a clear statement that no deployment occurred.

