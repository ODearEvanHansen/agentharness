from report import totals
t = totals("orders.csv")
assert t == {"alice": 15.0, "bob": 5.0, "carol": 7.0}, t
print("ok")
