def hashNoCase(tableName: str, n: int) -> int:
    h = 0
    tableName.lower()
    if n <= 0:
        n = len(tableName)

    for i in range(n):
        h = h << 3 ^ h ^ ord(tableName[i])

    if h < 0:
        h = -h

    return h
