import time
from typing import Iterable

def now_ts() -> int:
    return int(time.time())

def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]
