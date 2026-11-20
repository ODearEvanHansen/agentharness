from dur import parse_duration
assert parse_duration('1h30m') == 5400
assert parse_duration('45s') == 45
assert parse_duration('1h2m3s') == 3723
assert parse_duration('2h') == 7200
for bad in ['', 'h', '1x', '30m1h', '1h1h', 'abc']:
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('accepted ' + repr(bad))
print('ok')
