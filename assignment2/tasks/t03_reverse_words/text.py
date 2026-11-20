def reverse_words(s):
    """Reverse word order; collapse runs of whitespace to one space; strip ends."""
    return ' '.join(s.split(' ')[::-1])
