import re


def slugify(s):
    """Lowercase, keep [a-z0-9], join words with single "-", strip leading/trailing "-"."""
    return re.sub(r"[^a-z0-9]", "-", s)
