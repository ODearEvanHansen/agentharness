## sphinx
- Layout: `sphinx/` (builders, domains, ext/autodoc, ext/napoleon, writers); tests in `tests/test_*.py`, test projects in `tests/roots/test-*/`.
- Run tests: `python -m pytest tests/test_<area>.py -x -q -k name`. Building a root project is slow; prefer the targeted test.
- Expect warnings from deprecated deps in output; they are not failures.
