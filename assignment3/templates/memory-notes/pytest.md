## pytest
- Layout: source in `src/_pytest/` (python.py collects modules/packages, nodes.py, main.py); tests in `testing/`.
- Run tests: `python -m pytest testing/test_x.py -q -k name`. The `pytester` fixture builds throwaway test projects inside tests.
