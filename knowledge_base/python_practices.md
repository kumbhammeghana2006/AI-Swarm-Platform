# Python Best Practices & Testing Guide

## Code Quality Standards
- **Type Annotations**: Always annotate function signatures and key variables using Python type hints (`typing` module).
- **Docstrings**: Provide Google or NumPy style docstrings for classes and public methods.
- **PEP 8**: Follow standard naming conventions (snake_case for functions/variables, PascalCase for classes).

## Unit Testing Guidelines
- Use `pytest` or `unittest` framework.
- Structuring test cases: Setup -> Action -> Assertion.
- Edge case coverage: Test missing arguments, invalid inputs, empty collections, and raised exceptions.
