def parse_duration(s: str) -> int:
    """Parse durations like '1h30m', '45s', '2h', '1h2m3s' into seconds.
    Units: h, m, s; each at most once, in that order. Raise ValueError on bad input."""
    raise NotImplementedError
