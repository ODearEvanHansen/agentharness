## astropy
- Layout: `astropy/<subpackage>/` (modeling, io/ascii, units, ...); tests in `astropy/<subpackage>/tests/`.
- Run tests: `python -m pytest astropy/<subpackage>/tests/test_x.py -q -k name -p no:cacheprovider`. Package is built in place; do not rebuild.
