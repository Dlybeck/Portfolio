# AgentBridge: Tasks Command

Generate a task list from an implementation plan.

## Instructions

You are creating tasks for feature: **$ARGUMENTS**

1. Read the plan from `.agentbridge/features/{feature-name}/plan.md`

2. Create `tasks.md` in the same directory with this structure:
   - Tasks organized by implementation phase
   - Each task has: `- [ ] T### Description (file path if applicable)`
   - Mark parallelizable tasks with `[P]`
   - Include checkpoints at phase boundaries

3. Task guidelines:
   - Each task should be completable in one focused session
   - Include exact file paths where changes happen
   - Order tasks by dependencies
   - Group related tasks together

4. After creating tasks, output a summary with task count.

## Feature Name

$ARGUMENTS
