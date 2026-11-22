## sympy
- Layout: `sympy/<module>/`; tests in `sympy/<module>/tests/test_*.py`.
- Run tests: `python bin/test sympy/<module>/tests/test_x.py -k name` (or `python -m pytest` on the same file). Avoid running the whole suite.
- Printing/str/repr changes often need matching updates in the relevant printer (`sympy/printing/`).
