# Contributing to Aegis Smart Stadium OS

Thank you for your interest in contributing to the Aegis Smart Stadium OS project! We welcome code contributions, documentation improvements, issue reports, and feature requests.

---

## 1. Development Guidelines

- **Coding Standard**: We follow PEP8 guidelines for Python code and ESLint/TypeScript standard structures for frontend code.
- **Testing**: All submissions must pass the regression test suites.
  - Run backend tests: `python tests/backend/run_tests.py`
  - Run frontend tests: `pnpm run test`
- **Linting**: Ensure linting checks pass cleanly via `pnpm run lint` before creating commits.

---

## 2. Code Review & Submission Process

1. **Fork & Branch**: Fork the repository and create your feature branch: `git checkout -b feature/my-new-feature`.
2. **Commit Messages**: Write clear, descriptive commit messages starting with semantic tags (e.g. `feat:`, `fix:`, `docs:`, `chore:`).
3. **Pull Request**: Open a Pull Request targeting the `main` branch. Ensure the description lists the issues solved and changes introduced.
