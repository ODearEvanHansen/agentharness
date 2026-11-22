## scikit-learn
- Layout: `sklearn/<module>/`; tests in `sklearn/<module>/tests/test_*.py`.
- Run tests: `python -m pytest sklearn/<module>/tests/test_x.py -q -k name`. The package is built in place; do not rebuild Cython extensions.
- Public estimators follow fit/predict conventions; validation helpers live in `sklearn/utils/validation.py`.
