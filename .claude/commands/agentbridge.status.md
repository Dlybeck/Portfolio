# AgentBridge: Status Command

Show the current status of a feature.

## Instructions

You are checking status for feature: **$ARGUMENTS**

1. Read `.agentbridge/features/{feature-name}/tasks.md`

2. Calculate progress:
   - Count completed tasks `[x]`
   - Count incomplete tasks `[ ]`
   - Calculate percentage complete

3. Identify current phase:
   - Find which phase section contains the next incomplete task

4. Report:
   ```
   Feature: {feature-name}
   Progress: X/Y tasks complete (Z%)
   Current Phase: {phase name}
   Next Task: {next incomplete task description}

   Artifacts:
   - spec.md: ✓/✗
   - plan.md: ✓/✗
   - tasks.md: ✓/✗
   - context.md: ✓/✗
   ```

## Feature Name

$ARGUMENTS
