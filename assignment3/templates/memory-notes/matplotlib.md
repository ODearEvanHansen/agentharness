## matplotlib
- Layout: library in `lib/matplotlib/` (axes in `lib/matplotlib/axes/`, toolkits in `lib/mpl_toolkits/`); tests in `lib/matplotlib/tests/test_*.py`.
- Run tests: `python -m pytest lib/matplotlib/tests/test_<x>.py -q -k name`. Use the Agg backend for repro scripts (`import matplotlib; matplotlib.use("Agg")`).
- Image-comparison tests may be skipped/fail on missing fonts; don't chase those.
