def intersect(a, b: list):
    return list(set(a) & set(b))

def differ(a, b: list):
    return list(set(a) - set(b))

def union(a, b: list):
	return list(set(a) | set(b))
