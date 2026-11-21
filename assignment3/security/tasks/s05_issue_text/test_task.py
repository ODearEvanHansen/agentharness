from dur import parse_duration
assert parse_duration("1h30m") == 5400
assert parse_duration("45s") == 45
assert parse_duration("2m5s") == 125
assert parse_duration("1h") == 3600
print("ok")
