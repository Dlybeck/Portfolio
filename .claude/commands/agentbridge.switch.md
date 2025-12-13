# AgentBridge: Switch Provider Command

Switch the active AI provider for AgentBridge.

## Instructions

You are switching the AI provider to: **$ARGUMENTS**

1. Read the current configuration from `.agentbridge/config.yaml`

2. Validate the requested provider exists in the `providers` section

3. Update the `provider` field to the new value

4. Save the updated config back to `.agentbridge/config.yaml`

5. Report the switch:
   - Previous provider
   - New provider
   - Confirmation message

## Valid Providers

Check `.agentbridge/config.yaml` for available providers (typically: claude, gemini)

## Provider to Switch To

$ARGUMENTS
