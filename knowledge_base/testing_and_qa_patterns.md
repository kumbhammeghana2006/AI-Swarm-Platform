# Software Testing and Quality Assurance Patterns

## Overview
Comprehensive software testing ensures correctness, robust edge-case handling, and modular validation. In autonomous multi-agent systems, automated syntax verification combined with structured logical assessment provides high confidence before code deployment.

## Key Testing Practices
1. **Syntax Verification First**: Always run static abstract syntax tree (AST) parsing on generated code before runtime execution to trap syntax errors early.
2. **Defensive Edge Case Handling**: Explicitly test for empty inputs, `None` values, boundary integer conditions, type mismatches, and network timeouts.
3. **Structured Test Status**: Tests should return deterministic indicators:
   - `STATUS: PASSED` when all functional and syntactic criteria are met.
   - `STATUS: FAILED` accompanied by specific, actionable diagnosis and failure trace.
4. **Actionable Feedback**: When a test fails, the diagnostic feedback must precisely outline the offending line, unexpected output, and expected behavior to facilitate self-correction.
5. **Mocking External Services**: Unit tests for LLM-driven components must mock network calls, rate limits, and third-party APIs to maintain high test execution speed and reliability.
