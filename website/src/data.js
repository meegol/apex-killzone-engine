export const results = [
  // NQ=F
  { symbol: 'NQ=F',  label: 'NQ',  rr: 2, trades: 52, wr: 59.6, totalR:  26.84, pf: 2.36, maxDD: -9.67,  exp: 0.516 },
  { symbol: 'NQ=F',  label: 'NQ',  rr: 3, trades: 52, wr: 55.8, totalR:  31.55, pf: 2.46, maxDD: -12.67, exp: 0.607 },
  { symbol: 'NQ=F',  label: 'NQ',  rr: 4, trades: 52, wr: 51.9, totalR:  31.96, pf: 2.35, maxDD: -12.67, exp: 0.615 },
  // ES=F
  { symbol: 'ES=F',  label: 'ES',  rr: 2, trades: 64, wr: 54.7, totalR:  37.60, pf: 2.53, maxDD: -6.80,  exp: 0.588 },
  { symbol: 'ES=F',  label: 'ES',  rr: 3, trades: 64, wr: 53.1, totalR:  49.36, pf: 2.96, maxDD: -6.80,  exp: 0.771 },
  { symbol: 'ES=F',  label: 'ES',  rr: 4, trades: 64, wr: 51.6, totalR:  56.40, pf: 3.16, maxDD: -6.80,  exp: 0.881 },
  // MNQ=F
  { symbol: 'MNQ=F', label: 'MNQ', rr: 2, trades: 53, wr: 62.3, totalR:  28.74, pf: 2.53, maxDD: -6.80,  exp: 0.542 },
  { symbol: 'MNQ=F', label: 'MNQ', rr: 3, trades: 53, wr: 56.6, totalR:  33.81, pf: 2.55, maxDD: -8.80,  exp: 0.638 },
  { symbol: 'MNQ=F', label: 'MNQ', rr: 4, trades: 53, wr: 54.7, totalR:  40.30, pf: 2.77, maxDD: -7.80,  exp: 0.760 },
  // MES=F
  { symbol: 'MES=F', label: 'MES', rr: 2, trades: 64, wr: 56.2, totalR:  40.06, pf: 2.69, maxDD: -4.15,  exp: 0.626 },
  { symbol: 'MES=F', label: 'MES', rr: 3, trades: 64, wr: 54.7, totalR:  53.64, pf: 3.22, maxDD: -4.15,  exp: 0.838 },
  { symbol: 'MES=F', label: 'MES', rr: 4, trades: 64, wr: 53.1, totalR:  60.60, pf: 3.41, maxDD: -4.15,  exp: 0.947 },
]

export const unfiltered = [
  { symbol: 'NQ=F',  rr: 4, trades: 160, wr: 29, totalR: -10.8,  pf: 0.90 },
  { symbol: 'ES=F',  rr: 4, trades: 160, wr: 29, totalR:   3.3,  pf: 1.03 },
  { symbol: 'MNQ=F', rr: 4, trades: 156, wr: 28, totalR: -11.1,  pf: 0.90 },
  { symbol: 'MES=F', rr: 4, trades: 157, wr: 26, totalR: -17.7,  pf: 0.84 },
]

export const symColors = {
  'NQ=F':  '#fabd2f',
  'ES=F':  '#8ec07c',
  'MNQ=F': '#fe8019',
  'MES=F': '#d3869b',
}

export const symDesc = {
  'NQ=F':  'Nasdaq 100 Futures · $20/pt',
  'ES=F':  'S&P 500 Futures · $50/pt',
  'MNQ=F': 'Micro Nasdaq 100 · $2/pt',
  'MES=F': 'Micro S&P 500 · $5/pt',
}

export const findings = [
  {
    num: '01',
    title: 'Filters are not optional',
    body: 'Without the 3 filters the strategy loses money on 3 of 4 instruments. With them, every instrument is profitable with PFs above 2.3. The setups are real — the edge is in only taking the ones that align with the macro picture.',
  },
  {
    num: '02',
    title: 'Higher RR consistently wins',
    body: 'Across all 4 instruments, 1:4 produces the best or equal-best total R. Win rates hold above 50% even at 1:4 — the structure is clean enough to sustain it. ES=F and MES=F show almost no WR degradation moving from 1:2 to 1:4.',
  },
  {
    num: '03',
    title: 'MES=F has the lowest drawdown',
    body: 'MES=F maxed out at -4.15R across all three RR targets. The S&P micro futures produce tighter, more consistent kill zone setups than Nasdaq, which saw drawdowns up to -12.67R at 1:3 and 1:4.',
  },
  {
    num: '04',
    title: 'NQ trades less, wins more',
    body: 'NQ only generated 52 trades vs 64 for ES/MES. But its 1:2 win rate of 59.6% is the highest of any instrument at any RR. NQ\'s higher volatility causes more false sweeps to fail the displacement strength check, leaving cleaner entries.',
  },
  {
    num: '05',
    title: '~60% of raw signals are noise',
    body: 'Unfiltered: ~155–160 trades. Filtered: 52–64. Roughly 60–67% of signals get cut. The majority are killed by the HTF bias filter — most counter-trend sweeps during this period resolved against the trade direction.',
  },
  {
    num: '06',
    title: '59 days is a limited sample',
    body: 'yfinance caps 5m data at ~60 days. The results are promising but not statistically robust at 52–64 trades per instrument. Extending to 1–2 years via Alpaca or Polygon is the logical next step before drawing firm conclusions.',
  },
]
