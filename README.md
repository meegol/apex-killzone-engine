# apex-killzone-engine

ICT Kill Zone strategy backtester for NQ, ES, MNQ, and MES futures.
Tests whether the NY open 9:30–11 AM window produces an edge using sweeps, FVGs, IFVGs, and CISD confirmation.

**[→ live strategy website](https://meegol.github.io/apex-killzone-engine)**

---

## what it does

Pulls 5-minute intraday data from Yahoo Finance and backtests one strategy:

- Mark Asia (7 PM–midnight ET) and London Kill Zone (2–5 AM ET) highs and lows
- Mark 4H and 1H Fair Value Gaps formed before the kill zone
- Find 4H HTF swing highs and lows as additional liquidity targets
- Between 9:30–11:00 AM ET, watch for price to sweep one of those levels or tap into an FVG
- Require CISD or IFVG confirmation before entry
- Simulate the trade at 1:2, 1:3, and 1:4 risk:reward simultaneously

Three filters & one risk management rule cut the low-quality signals:

1. **HTF 4H bias** — only trade with the 4H trend direction
2. **Premium/discount** — shorts above the session midpoint, longs below it
3. **Displacement strength** — the confirmation candle must be 1.3× the average body size
4. **Breakeven (BE) stop @ +1.5R** — trailing stop moves to entry once price reaches +1.5R profit point to eliminate winner-turned-loser drawdown

---

## strict win rate metric

Win rates strictly measure full target completions (`WIN` at 1:4 target). Partial EOD closes and Breakevens (`+0.0R`) do not artificially inflate the Win Rate.

---

## results (59 trading days, May–Aug 2026)

All instruments profitable after filtering. Without filters, 3 of 4 lose money.

| Symbol | RR   | Trades | Win Rate | Total R  | Profit Factor | Max DD   | Expectancy |
|--------|------|--------|----------|----------|---------------|----------|------------|
| NQ=F   | 1:2  | 52     | 59.6%    | +26.84R  | 2.36          | -9.67R   | +0.516R    |
| NQ=F   | 1:3  | 52     | 55.8%    | +31.55R  | 2.46          | -12.67R  | +0.607R    |
| NQ=F   | 1:4  | 52     | 51.9%    | +31.96R  | 2.35          | -12.67R  | +0.615R    |
| ES=F   | 1:2  | 64     | 54.7%    | +37.6R   | 2.53          | -6.8R    | +0.588R    |
| ES=F   | 1:3  | 64     | 53.1%    | +49.36R  | 2.96          | -6.8R    | +0.771R    |
| ES=F   | 1:4  | 64     | 51.6%    | +56.4R   | 3.16          | -6.8R    | +0.881R    |
| MNQ=F  | 1:2  | 53     | 62.3%    | +28.74R  | 2.53          | -6.8R    | +0.542R    |
| MNQ=F  | 1:3  | 53     | 56.6%    | +33.81R  | 2.55          | -8.8R    | +0.638R    |
| MNQ=F  | 1:4  | 53     | 54.7%    | +40.3R   | 2.77          | -7.8R    | +0.760R    |
| MES=F  | 1:2  | 64     | 56.2%    | +40.06R  | 2.69          | -4.15R   | +0.626R    |
| MES=F  | 1:3  | 64     | 54.7%    | +53.64R  | 3.22          | -4.15R   | +0.838R    |
| **MES=F**  | **1:4**  | **64**     | **53.1%**    | **+60.6R**   | **3.41**          | **-4.15R**   | **+0.947R**    |

MES=F 1:4 was the top performer — highest total R, highest profit factor, lowest drawdown of any instrument.

### filter impact (NQ 1:4 example)

| | Trades | Win Rate | Total R | Profit Factor |
|--|--------|----------|---------|---------------|
| no filters | 160 | 29% | -10.8R | 0.90 |
| filtered | 52 | 51.9% | +31.96R | 2.35 |

---

## setup

```bash
git clone https://github.com/meegol/apex-killzone-engine
cd apex-killzone-engine
pip install -r requirements.txt
python main.py
```

Outputs a self-contained HTML report to `reports/`. Open it in any browser.

### changing instruments or RR targets

Edit the top of `main.py`:

```python
SYMBOLS    = ['NQ=F', 'ES=F', 'MNQ=F', 'MES=F']
RR_TARGETS = [2.0, 3.0, 4.0]
```

Any yfinance-compatible symbol works. Equity indices, ETFs, crypto futures — as long as they have intraday data.

### adjusting filters

The `_apply_filters()` method in `backtester.py` controls HTF bias and premium/discount.
The displacement multiplier is in `_check_displacement_strength()`:

```python
def _check_displacement_strength(self, ..., multiplier=1.3):
```

Lower it to allow weaker confirmation candles, raise it to be more selective.

---

## data sources

Default is yfinance — no API key, works out of the box.

| Source | Free history | Notes |
|--------|-------------|-------|
| yfinance | 60 days (5m) | default, unofficial Yahoo scraper |
| Alpaca Markets | 5+ years (1m/5m) | free paper account, best free option |
| Polygon.io | full history | $29/mo starter, institutional quality |
| Twelve Data | ~1 year | 800 req/day free tier |
| CSV / local | unlimited | load any OHLCV into pandas, pass to `ICTStrategy` |

To use your own data source, replace `DataFetcher._get()`. The strategy only needs two DataFrames with `[open, high, low, close, volume]` columns and a tz-aware ET index.

---

## project structure

```
meegol-backtest/
├── main.py            # entry point
├── data_fetcher.py    # yfinance wrapper
├── strategy.py        # FVG detection, sweeps, CISD, IFVG, swing points
├── backtester.py      # trade simulation, filters, live console output
├── report_generator.py# HTML report with Plotly.js charts
├── requirements.txt
├── docs/
│   └── index.html     # results website
└── reports/           # generated HTML reports (gitignored)
```

---

## key findings

1. **Filters are not optional.** The raw strategy loses money. The filters are where the edge lives.
2. **Higher RR consistently performs better.** 1:4 beats 1:2 on total R across all 4 instruments. Win rates hold above 50% even at 1:4.
3. **MES=F has the best risk-adjusted performance.** Lowest max drawdown (-4.15R), highest PF (3.41), highest expectancy (0.947R).
4. **NQ has the highest win rate** (59.6% at 1:2) despite fewer trades — high volatility kills more weak setups at the filter stage.
5. **~60% of raw signals are noise.** The HTF bias filter alone blocks the majority. Most losing trades were counter-trend.
6. **59 days is not enough to declare an edge.** The sample needs 1–2 years of data to be statistically meaningful. Results are directionally promising, not conclusive.

---

## disclaimer

This is for research purposes. Not financial advice. Past backtested performance does not guarantee future results.
