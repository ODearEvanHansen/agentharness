from data import load_rows
r = load_rows('people.csv')
assert len(r) == 2
assert r[0]['note'] == 'first programmer, arguably', r[0]
assert r[1]['name'] == 'Hopper, Grace' and r[1]['city'] == 'New York', r[1]
print('ok')
