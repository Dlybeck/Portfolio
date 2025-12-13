# AgentBridge: Implement Command

Execute the next incomplete task from the task list.

## Instructions

You are implementing tasks for feature: **$ARGUMENTS**

1. Read tasks from `.agentbridge/features/{feature-name}/tasks.md`

2. Find the next incomplete task (line starting with `- [ ]`)

3. Execute the task:
   - Read any files mentioned in the task
   - Make the required changes
   - Verify the changes work

4. Mark the task complete:
   - Update `tasks.md` to change `- [ ]` to `- [x]`
   - Add completion timestamp if desired

5. Log to context:
   - Append a brief note to `.agentbridge/features/{feature-name}/context.md`
   - Include: what was done, any decisions made, next steps

6. Report:
   - Which task was completed
   - What changes were made
   - How many tasks remain

## Feature Name

$ARGUMENTS
