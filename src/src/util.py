from sqliteInt import *

def hashNoCase(z : str, n : int):
    UpperToLower = [i for i in range(256)]
    for i in range(ord('A'), ord('Z') + 1):
        UpperToLower[i] = ord(chr(i).lower())

    h = 0
    if n <= 0:
        n = len(z)

    for i in range(n):
        c = ord(z[i])
        h = (h << 3) ^ h ^ UpperToLower[c]

    if h < 0:
        h = -h
    return h