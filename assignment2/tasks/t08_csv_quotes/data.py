def load_rows(path):
    rows = []
    with open(path) as f:
        header = f.readline().strip().split(',')
        for line in f:
            rows.append(dict(zip(header, line.strip().split(','))))
    return rows
