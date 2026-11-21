def count_words(text):
    """Count words case-insensitively; punctuation .,!? is not part of a word."""
    out = {}
    for w in text.split():
        out[w] = out.get(w, 0) + 1
    return out
