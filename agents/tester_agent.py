import ast
from typing import Dict, Any
from agents.base_agent import BaseAgent

class TesterAgent(BaseAgent):
    """
    Tester Agent analyzes code correctness, checks Python syntax with ast,
    and runs logical verification using LLM to generate pass/fail test status and feedback.
    """

    def test_code(self, task: str, code: str) -> Dict[str, Any]:
        # 1. Local Python syntax check
        syntax_passed = True
        syntax_error = ""

        # Extract code block if enclosed in markdown backticks
        clean_code = code
        if "```python" in code:
            clean_code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            clean_code = code.split("```")[1].split("```")[0]

        try:
            ast.parse(clean_code)
        except SyntaxError as se:
            syntax_passed = False
            syntax_error = f"SyntaxError on line {se.lineno}: {se.msg}"

        if not syntax_passed:
            return {
                "passed_tests": False,
                "test_results": f"FAILED (Syntax Check): {syntax_error}",
                "feedback": f"Code contains python syntax error: {syntax_error}. Fix code syntax."
            }

        # 2. LLM Logical & Requirement Verification
        system_prompt = (
            "You are the Tester Agent in an AI Swarm platform. "
            "Your job is to rigorously evaluate Python code against the user's task requirements. "
            "Identify logic bugs, missing error handling, unmet requirements, or edge case failures.\n"
            "Format your response as:\n"
            "STATUS: [PASSED or FAILED]\n"
            "TEST_SUMMARY: <summary of tests run and findings>\n"
            "FEEDBACK: <actionable feedback for Coder Agent if FAILED, or empty if PASSED>"
        )

        user_prompt = (
            f"User Task: {task}\n\n"
            f"Code to Test:\n{code}\n\n"
            "Evaluate this code for functional correctness, completeness, and edge case safety."
        )

        analysis = self.call_llm(system_prompt, user_prompt)

        # Parse LLM response status
        passed = "STATUS: PASSED" in analysis.upper() or ("PASSED" in analysis.upper() and "FAILED" not in analysis.upper())
        
        # Build clean test results and feedback
        feedback = ""
        if not passed:
            if "FEEDBACK:" in analysis:
                feedback = analysis.split("FEEDBACK:", 1)[1].strip()
            else:
                feedback = analysis

        return {
            "passed_tests": passed,
            "test_results": analysis,
            "feedback": feedback
        }
