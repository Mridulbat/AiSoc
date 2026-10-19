# SentinelEdge — Repository Instructions

## Primary specification
- Read `PROJECT_SPEC.md` before implementing major features.
- Treat it as the primary source of truth for project requirements.
- Resolve conflicts by following the latest explicit user instructions and documenting necessary deviations.

## Development rules
- Implement working functionality, not just plans, mockups or placeholder code.
- Inspect existing files before modifying them. Preserve unrelated work.
- Use modular, maintainable code and appropriate type checks.
- Run relevant tests and fix failures before declaring work complete.
- Keep `PLAN.md` updated with evidence-based progress.

## Security and privacy
- No cloud AI APIs or third-party network calls during normal analysis.
- Never automatically visit submitted URLs.
- Do not log sensitive user inputs or commit secrets, datasets or model weights.
- Treat user-supplied messages as untrusted input.

## Model and hardware requirements
- The required language-model path is Llama through ExecuTorch.
- Never falsely claim that a model, test or Arm device was successfully verified.
- Clearly distinguish actual model inference from fallback explanations and demo data.

## Completion requirements
- Follow the setup and testing instructions in `PROJECT_SPEC.md`.
- Document unmet prerequisites and exact reproduction steps.
- Report implemented features, actual test results and remaining blockers.