# the-poster-for-a-place-that-isnt-there

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/garyadrianto1/the-poster-for-a-place-that-isnt-there/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/garyadrianto1/the-poster-for-a-place-that-isnt-there/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for **Aerfall**, a place that isn't there — where the falls
rise. A luminous column of water climbs out of a dark valley pool, up
through a dusk cloud bank, into the sky. `main.py` renders the whole
poster procedurally to `/output/entry.png` (1024×1024, under 1 MiB).

## Run it

```sh
python3 main.py
```

Python 3.13, Pillow only. Deterministic (two runs produce byte-identical
output), no network, no input files. Fixed seed `20261121` drives every
random choice.
