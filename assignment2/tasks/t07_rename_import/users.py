from util import normalize

def key(user):
    return normalize(user['name'])
