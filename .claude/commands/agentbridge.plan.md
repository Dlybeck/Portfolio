# AgentBridge: Plan Command

Generate an implementation plan from a feature specification.

## Instructions

You are creating an implementation plan for feature: **$ARGUMENTS**

1. Read the spec from `.agentbridge/features/{feature-name}/spec.md`

2. Create `plan.md` in the same directory with this structure:
   - **Summary**: Brief overview of the approach
   - **Technical Context**: Language, dependencies, platform
   - **Architecture**: Key components and how they interact
   - **Implementation Phases**: Ordered phases with clear goals
   - **Design Decisions**: Key choices and rationale

3. Focus on HOW:
   - Map requirements to technical solutions
   - Identify files to create/modify
   - Define API contracts if applicable
   - Plan for testability

4. After creating the plan, output a summary.

## Feature Name

$ARGUMENTS
