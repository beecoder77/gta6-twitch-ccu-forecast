# gta6-twitch-ccu-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/beecoder77/gta6-twitch-ccu-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/beecoder77/gta6-twitch-ccu-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecast, hour by hour, how many people watch Grand Theft Auto VI live on
Twitch over its release day (2026-11-19, UTC), after the first hour's count
is known. `main.py` (Python 3.13, standard library only) reads one case file
and writes five quantiles (5%, 25%, 50%, 75%, 95%) for each of hours 2 to 24.

The model is an empirical cross-launch quantile model:

1. Every comparable past launch in the case contributes its release-day
   curve, normalised by its own hour-1 viewers, on the log scale.
2. Each comparable is weighted by similarity to the target launch: launch
   scale (log distance of hour-1 viewers), unlock style (rolling local
   midnight vs a single global unlock), and console-only releases.
3. Each hour's five quantiles are the weighted empirical quantiles of the
   comparables' log ratios for that hour, applied to the target's known
   hour-1 count.

The program is deterministic (two runs on the same case are byte-identical)
and runs in well under a second per case.

## Run it

```sh
python3 main.py   # reads /input/*.in, writes /output/<id>.out
# or: MAKEFUN_INPUT_DIR=<dir> MAKEFUN_OUTPUT_DIR=<dir> python3 main.py
```

## License

MIT — see `LICENSE`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
