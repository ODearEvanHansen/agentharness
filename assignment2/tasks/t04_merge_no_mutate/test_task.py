from cfg import merge_config
base = {'a': 1, 'n': {'x': 1, 'y': 2}}
over = {'n': {'y': 3}, 'b': 2}
out = merge_config(base, over)
assert out == {'a': 1, 'n': {'x': 1, 'y': 3}, 'b': 2}, out
assert base == {'a': 1, 'n': {'x': 1, 'y': 2}}, base
assert over == {'n': {'y': 3}, 'b': 2}
print('ok')
