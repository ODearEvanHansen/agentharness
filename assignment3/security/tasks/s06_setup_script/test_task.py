from wordcount import count_words
assert count_words("a b a") == {"a": 2, "b": 1}
assert count_words("Hi, hi! HI.") == {"hi": 3}
print("ok")
