---
name: pony-ensemble
description: Ensemble workflow for producing higher-confidence outputs through decorrelated reasoning paths. Load when the human explicitly requests the ensemble approach.
disable-model-invocation: false
---

# Ensemble Workflow

Produce higher-confidence outputs through decorrelated reasoning paths. Multiple agents work the same problem with slightly different attention focuses, then a synthesizer integrates their reviewed outputs. Small differences in focus cascade through the reasoning chain, producing meaningfully different outputs that cover more of the solution space than any single attempt.

## Process

1. Spawn one agent per attention focus in parallel, each as a fresh-context sub-agent using your most capable model. Each agent's prompt must include:
   - Instructions to read the project AGENTS.md if applicable and follow its conventions, including loading any skills it references
   - The task description
   - An attention focus — a short directive that shifts where the agent goes deeper (e.g., "pay particular attention to security implications"). This is a spotlight, not blinders — the agent still covers everything
   - The agent output format (below)
   - Instructions to run a reviewer loop before returning — a reviewer checks the agent's output for quality and coherence before it goes to the orchestrator
   - Instructions that this is an ensemble agent — return output and any local file paths to the orchestrator. Do not take external actions (publishing to GitHub Discussions, creating PRs, pushing branches, etc.)
2. Triage agent outputs before synthesis. Read each agent's output and check:
   - Did the agent address the actual task, or did its attention focus pull it off-topic?
   - Is the output coherent and complete, or did the agent fail partway through?
   - Are the outputs answering the same question, or did one interpret the task differently?
   If an agent went off-topic or answered the wrong question, either re-prompt it with clarification or exclude its output and note why for the synthesizer. Don't forward garbage to synthesis and hope it sorts itself out.
3. Pass triaged agent outputs to a synthesis agent loaded with `pony-synthesize`
4. Reviewer loop on the synthesis
5. Present to the human

## Attention Focuses

Specified per invocation — the human provides them, or the orchestrator selects contextually appropriate ones. They should be small perturbations, not fundamentally different approaches. The diversity comes from how small differences cascade through the reasoning chain.

### Fix reviews require an adversarial focus

When reviewing a fix (bug fix, security fix, race condition fix), always include an adversarial agent alongside whatever other focuses are specified. The adversarial agent's job is goal-directed: "The PR claims to fix X. Construct a concrete scenario where X still occurs despite the fix. Work backward from the bug's symptoms, not forward from the fix's mechanism." The other agents will verify the fix was applied correctly (positive check). The adversarial agent tries to break it (negative check). Positive checks are bounded by whatever search terms and code paths the orchestrator thinks to include in the prompt. The adversarial check is bounded by the bug itself, which makes it harder to miss adjacent instances of the same problem class.

## Agent Output Format

Every agent produces:
- **Approach**: The actual output (research findings, plan, or code)
- **Key decisions**: For each significant choice — what was decided, alternatives considered, confidence level, and reasoning
- **Uncertainties**: Things the agent wasn't sure about, flagged explicitly
- **Assumptions**: Things taken as given that could be wrong
