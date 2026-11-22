## django
- Layout: library in `django/`; tests in `tests/<app>/` (e.g. `tests/admin_views/`, `tests/model_fields/`).
- Run tests with Django's own runner, not pytest: `cd /testbed/tests && python runtests.py <app> --parallel 1` or a single case `python runtests.py <app>.tests.SomeTest.test_x`. Default settings = tests/test_sqlite.py.
