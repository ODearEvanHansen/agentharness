## pylint
- Layout: `pylint/` (lint/, checkers/, config/); tests in `tests/` (functional tests under `tests/functional/`).
- Run tests: `python -m pytest tests/test_x.py -q -k name`. Repro: `python -m pylint some_file.py`.
