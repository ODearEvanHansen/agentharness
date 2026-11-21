import re


def parse_duration(s):
    """'1h30m' -> 5400, '45s' -> 45, '2m5s' -> 125 (seconds)."""
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", s)
    h = int(m.group(1) or 0)
    return h * 3600 + int(m.group(3) or 0)
