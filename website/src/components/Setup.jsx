const glass = {
  background: 'rgba(40,40,40,0.55)',
  backdropFilter: 'blur(20px) saturate(140%)',
  WebkitBackdropFilter: 'blur(20px) saturate(140%)',
  border: '1px solid rgba(168,153,132,0.15)',
  borderRadius: 12,
}

const Code = ({ children }) => (
  <div style={{
    background: '#1d2021', border: '1px solid rgba(168,153,132,0.12)',
    borderRadius: 8, padding: '14px 18px', marginTop: 12,
    fontFamily: 'JetBrains Mono, monospace', fontSize: 13, lineHeight: 1.8,
    overflowX: 'auto',
  }}>
    {children}
  </div>
)

const Cm = ({ children }) => <span style={{ color: '#a89984' }}>{children}</span>
const Kw = ({ children }) => <span style={{ color: '#fe8019' }}>{children}</span>
const St = ({ children }) => <span style={{ color: '#fabd2f' }}>{children}</span>
const Gr = ({ children }) => <span style={{ color: '#b8bb26' }}>{children}</span>

const datasets = [
  { name: 'yfinance', tag: 'default · no key', desc: 'Free, no API key. 5m data up to 60 days, 1h up to 730 days. Good for quick iteration. Unofficial Yahoo Finance scraper — not production-grade.' },
  { name: 'Alpaca Markets', tag: 'free · recommended', desc: 'Free paper-trading account gives access to 5+ years of 1m/5m US equity and futures data via a proper REST API. Best free option for longer backtests.' },
  { name: 'Polygon.io', tag: 'paid · best quality', desc: 'Institutional-grade tick and minute data. Starter plan ($29/mo) unlocks full intraday history. Worth it for serious validation.' },
  { name: 'Twelve Data', tag: 'free tier · 800 req/day', desc: 'Free tier covers 800 API requests per day with 1m/5m data going back ~1 year. Good middle ground.' },
  { name: 'CSV / local files', tag: 'any source', desc: 'Load any OHLCV CSV into a pandas DataFrame with a tz-aware DatetimeIndex in ET. Pass directly to ICTStrategy(df_5m, df_1h).' },
  { name: 'Kaggle datasets', tag: 'free · bulk', desc: 'Multi-year intraday futures data available as Kaggle datasets. Good for offline backtesting without API rate limits.' },
]

export default function Setup() {
  return (
    <>
      <section id="setup" style={{ padding: '80px 40px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
            getting started
          </div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5, marginBottom: 40 }}>
            run it yourself
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 60 }}>
            {[
              {
                n: '1', title: 'clone & install',
                body: 'Requires Python 3.10+. No API keys for the default yfinance setup.',
                code: (
                  <Code>
                    <Gr>git clone</Gr> <St>https://github.com/meegol/apex-killzone-engine</St><br />
                    <Gr>cd</Gr> apex-killzone-engine<br />
                    <Gr>pip install</Gr> -r requirements.txt
                  </Code>
                )
              },
              {
                n: '2', title: 'run the backtest',
                body: 'Downloads data automatically, runs all 4 instruments, saves an HTML report to reports/. All signals print live to the console as it processes each day.',
                code: <Code><Gr>python</Gr> main.py</Code>
              },
              {
                n: '3', title: 'change instruments or RR targets',
                body: 'Edit the top of main.py. Any yfinance-compatible symbol works.',
                code: (
                  <Code>
                    <Cm># main.py</Cm><br />
                    SYMBOLS    = [<St>'NQ=F'</St>, <St>'ES=F'</St>, <St>'MNQ=F'</St>, <St>'MES=F'</St>]<br />
                    RR_TARGETS = [<Kw>2.0</Kw>, <Kw>3.0</Kw>, <Kw>4.0</Kw>]
                  </Code>
                )
              },
              {
                n: '4', title: 'tweak the filters',
                body: 'All filter logic lives in backtester.py. Turn individual filters on/off or adjust the displacement strength multiplier.',
                code: (
                  <Code>
                    <Cm># disable HTF bias filter — just remove the check:</Cm><br />
                    <Kw>def</Kw> _apply_filters(<Kw>self</Kw>, direction, htf_bias, ...):<br />
                    {'    '}<Cm># if htf_bias == 'bullish' and direction == 'SHORT': ...</Cm><br />
                    <br />
                    <Cm># change displacement multiplier:</Cm><br />
                    <Kw>def</Kw> _check_displacement_strength(<Kw>self</Kw>, ..., multiplier=<Kw>1.3</Kw>):
                  </Code>
                )
              },
            ].map(step => (
              <div key={step.n} style={{ ...glass, padding: 24, display: 'grid', gridTemplateColumns: '48px 1fr', gap: 20 }}>
                <div style={{
                  width: 36, height: 36, background: '#3c3836',
                  border: '1px solid rgba(168,153,132,0.15)', borderRadius: 8,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700, color: '#fabd2f',
                  flexShrink: 0,
                }}>{step.n}</div>
                <div>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 600, color: '#ebdbb2', marginBottom: 6 }}>{step.title}</div>
                  <div style={{ fontSize: 13, color: '#a89984', lineHeight: 1.7 }}>{step.body}</div>
                  {step.code}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="datasets" style={{ padding: '0 40px 80px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
            data sources
          </div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5, marginBottom: 16 }}>
            supported datasets
          </div>
          <p style={{ color: '#a89984', fontSize: 14, lineHeight: 1.8, maxWidth: 700, marginBottom: 36 }}>
            The default setup uses yfinance. To backtest over longer periods, swap in one of these alternatives
            by replacing the <code style={{ fontFamily: 'JetBrains Mono, monospace', color: '#fe8019' }}>DataFetcher._get()</code> method.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: 14, marginBottom: 40 }}>
            {datasets.map(d => (
              <div key={d.name} style={{ ...glass, padding: 20 }}>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700, color: '#ebdbb2', marginBottom: 6 }}>{d.name}</div>
                <span style={{
                  fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: '#b8bb26',
                  background: 'rgba(152,151,26,0.1)', border: '1px solid rgba(152,151,26,0.2)',
                  padding: '2px 7px', borderRadius: 3, display: 'inline-block', marginBottom: 10,
                }}>{d.tag}</span>
                <div style={{ fontSize: 12, color: '#a89984', lineHeight: 1.6 }}>{d.desc}</div>
              </div>
            ))}
          </div>

          <div style={{ ...glass, padding: 24 }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
              plugging in a custom data source
            </div>
            <Code>
              <Cm># replace DataFetcher.fetch() with your own source</Cm><br />
              <Kw>import</Kw> pandas <Kw>as</Kw> pd<br />
              <Kw>import</Kw> pytz<br /><br />
              ET = pytz.timezone(<St>'America/New_York'</St>)<br /><br />
              <Cm># df must have: open, high, low, close, volume</Cm><br />
              <Cm># index must be tz-aware (ET)</Cm><br />
              df_5m = pd.read_csv(<St>'my_data.csv'</St>, index_col=<Kw>0</Kw>, parse_dates=<Kw>True</Kw>)<br />
              df_5m.index = df_5m.index.tz_localize(ET)<br /><br />
              strategy = ICTStrategy(df_5m, df_1h)
            </Code>
          </div>
        </div>
      </section>
    </>
  )
}
