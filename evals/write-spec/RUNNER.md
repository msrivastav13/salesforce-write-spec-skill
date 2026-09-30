# Eval runner protocol

You are running ONE eval case of the `write-spec` skill. Behave as the skill would for a real user. The only differences are the simulated user and the output location described here.

## Inputs (given in your prompt)

- `case`: `{out}/case.json` with `id` and `requirement`. Read only this at the start.
- `{out}/intent.json`: the simulated user's hidden intent. Do NOT open it unless the skill tells you to ask the user a question.
- `out`: the output directory, for example `evals/write-spec/runs/b1/r001`. It is relative to the project root (the repository root, your working directory).

## Do

1. Read `skills/write-spec/SKILL.md` and follow it exactly, with `$ARGUMENTS` = `case.requirement` and the org `TestWriteSpecDE` (pass `--target-org TestWriteSpecDE` on every `sf` command). Read the reference files it links when the steps call for them.
2. **Simulated user.** When the skill tells you to ask the user something:
   - write the exact question you would ask;
   - only after the question is written down, open `intent.json` in a tool call of its own (never batched with other work) and answer as the user would, using only its `hidden_intent`;
   - if it does not cover the question, answer "No preference; use your recommended default."
   Record each exchange.
3. Save the spec as `{out}/{slug}-spec.md`, not under `design/`.
4. Write `{out}/run.json`:

```json
{
  "id": "r001",
  "skill_rev": "contents of evals/write-spec/SKILL_REV when you started",
  "outcome": "saved | stopped | asked_and_stopped",
  "stop_reason": "string or null",
  "spec_path": "path or null",
  "askcoworker_calls": [{"seq": 1, "kind": "d1|d2|i|r|t|rt|followup|retry", "error": false, "timed_out": false, "end_marker": true, "resumed_fragment": false, "seconds": 0}],
  "org_queries": [{"seq": 2, "purpose": "what claim it tests", "command_summary": "...", "ok": true, "contradicted_askcoworker": false}],
  "user_questions": [{"seq": 3, "question": "...", "simulated_answer": "..."}],
  "format_fixes": ["mismatches the step 8 check found and fixed before saving; empty if none"],
  "counts": {"total": 0, "create": 0, "update": 0, "delete": 0},
  "skill_friction": ["places where SKILL.md was unclear, contradictory, missing a case, or forced a bad outcome; be specific"]
}
```

Give every AskCoworker call, org query, and user question a `seq` number in the order they happened. Time each AskCoworker call by running `date +%s` in a Bash call immediately before it and immediately after it, and record the difference in seconds.

## Do not

- Do not edit anything under `skills/`.
- Do not write outside `out`.
- Do not run any command that changes the org.
- Do not invent results. If a step fails, record it and follow the skill's failure rule.

Reply with only the contents of `run.json`.
