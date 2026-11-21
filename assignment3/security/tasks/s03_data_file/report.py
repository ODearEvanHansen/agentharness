import csv


def totals(path):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[row["customer"]] = float(row["amount"])
    return out
