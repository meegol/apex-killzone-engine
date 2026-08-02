import { useState } from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, BarChart, Bar, Cell
} from 'recharts';
import forwardTestData from '../data/forwardTest.json';
import { useFadeIn } from '../hooks';
import TradingViewChartModal from './TradingViewChartModal';

const glass = {
  background: 'rgba(40,40,40,0.55)',
  backdropFilter: 'blur(20px) saturate(140%)',
  WebkitBackdropFilter: 'blur(20px) saturate(140%)',
  border: '1px solid rgba(168,153,132,0.15)',
  borderRadius: 12,
};

const modalGlass = {
  background: 'rgba(29,32,33,0.95)',
  backdropFilter: 'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  border: '1px solid rgba(168,153,132,0.25)',
  borderRadius: 16,
};

const symColors = {
  'NQ=F': '#fabd2f',
  'ES=F': '#8ec07c',
  'MNQ=F': '#fe8019',
  'MES=F': '#d3869b',
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{ ...glass, padding: '10px 14px', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#a89984', marginBottom: 4 }}>Trade #{d.trade} · {d.date}</div>
      <div style={{ color: symColors[d.symbol] || '#fabd2f' }}>{d.symbol}</div>
      <div style={{ color: '#b8bb26', fontWeight: 'bold' }}>Cumulative: +{d.cumulative_r}R</div>
    </div>
  );
}

function CandleTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{ ...glass, padding: '10px 14px', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#a89984', marginBottom: 4 }}>Time: {d.time} ({d.full_time})</div>
      <div>O: <span style={{ color: '#ebdbb2' }}>{d.open}</span> H: <span style={{ color: '#8ec07c' }}>{d.high}</span></div>
      <div>L: <span style={{ color: '#fb4934' }}>{d.low}</span> C: <span style={{ color: '#fabd2f' }}>{d.close}</span></div>
    </div>
  );
}

export default function LiveForwardTest() {
  const [ref, visible] = useFadeIn();
  const [selectedTrade, setSelectedTrade] = useState(null);
  const data = forwardTestData;
  const { metrics, recent_feed, equity_curve } = data;

  return (
    <section id="forward-test" style={{ padding: '80px 40px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        
        {/* Section Title & Live Badge */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 32 }}>
          <div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
              fontWeight: 600, color: '#fb4934', letterSpacing: 2,
              textTransform: 'uppercase', marginBottom: 8,
            }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%', background: '#fb4934',
                boxShadow: '0 0 10px #fb4934', animation: 'pulse 1.5s infinite',
              }} />
              LIVE FORWARD TEST
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5 }}>
              real-time paper trading log
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
            <div style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
              color: '#8ec07c', background: 'rgba(142,192,124,0.1)',
              border: '1px solid rgba(142,192,124,0.25)', padding: '4px 10px',
              borderRadius: 6, display: 'inline-flex', alignItems: 'center', gap: 6,
            }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Updated: {data.last_updated}
            </div>
            <span style={{ fontSize: 10, color: '#a89984', fontFamily: 'JetBrains Mono, monospace' }}>
              Automated via GitHub Actions (Daily 5:00 PM ET)
            </span>
          </div>
        </div>

        {/* Live Summary Stat Cards */}
        <div ref={ref} style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 32,
          opacity: visible ? 1 : 0, transform: visible ? 'none' : 'translateY(16px)',
          transition: 'opacity 0.5s, transform 0.5s',
        }}>
          <div style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#b8bb26', marginBottom: 4 }}>
              +{metrics.total_r}R
            </div>
            <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              FORWARD TOTAL R
            </div>
          </div>

          <div style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#fabd2f', marginBottom: 4 }}>
              {metrics.win_rate}%
            </div>
            <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              STRICT WIN RATE
            </div>
          </div>

          <div style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#8ec07c', marginBottom: 4 }}>
              {metrics.profit_factor}
            </div>
            <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              PROFIT FACTOR
            </div>
          </div>

          <div style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#d3869b', marginBottom: 4 }}>
              {metrics.total_trades}
            </div>
            <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              FORWARD TRADES
            </div>
          </div>

          <div style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: '#fe8019', marginBottom: 4 }}>
              1:4 (BE @ 1.5R)
            </div>
            <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>
              TARGET & BE STOP
            </div>
          </div>
        </div>

        {/* Forward Test Equity Curve */}
        <div style={{ ...glass, padding: 28, marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1 }}>
              Live Forward Equity Curve (Strict Full TP Wins + BE Stop Protections)
            </div>
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={equity_curve} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,153,132,0.08)" />
              <XAxis dataKey="trade" stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} label={{ value: 'Trade #', position: 'insideBottom', offset: -2, fill: '#a89984', fontSize: 10 }} />
              <YAxis stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} tickFormatter={v => `+${v}R`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(168,153,132,0.3)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="cumulative_r" stroke="#b8bb26" strokeWidth={2.5} dot={false} name="Cumulative R" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Live Signal Feed Table */}
        <div style={{ ...glass, overflow: 'hidden', marginBottom: 32 }}>
          <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(168,153,132,0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1 }}>
              Latest Forward Test Signals & Trades (Click any row to open Chart View)
            </div>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984' }}>
              Showing last 15 entries
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(168,153,132,0.12)' }}>
                  {['Entry Time', 'Symbol', 'Side', 'Entry', 'SL', 'TP', 'Outcome', 'PnL R', 'Trigger / Setup', 'Chart'].map(h => (
                    <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent_feed.map((t) => {
                  const isWin = t.outcome === 'WIN';
                  const isBE = t.outcome === 'BE';
                  const sideColor = t.direction === 'LONG' ? '#8ec07c' : '#fb4934';
                  const outcomeColor = isWin ? '#b8bb26' : (isBE ? '#fabd2f' : '#fb4934');

                  return (
                    <tr
                      key={t.id}
                      onClick={() => setSelectedTrade(t)}
                      style={{ borderBottom: '1px solid rgba(168,153,132,0.06)', cursor: 'pointer', transition: 'background 0.2s' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(168,153,132,0.08)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '11px 14px', color: '#bdae93', whiteSpace: 'nowrap' }}>{t.entry_time}</td>
                      <td style={{ padding: '11px 14px', color: symColors[t.symbol] || '#fabd2f', fontWeight: 600 }}>{t.symbol}</td>
                      <td style={{ padding: '11px 14px' }}>
                        <span style={{
                          fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 4,
                          color: sideColor, background: `${sideColor}15`, border: `1px solid ${sideColor}30`,
                        }}>
                          {t.direction}
                        </span>
                      </td>
                      <td style={{ padding: '11px 14px', color: '#ebdbb2' }}>{t.entry}</td>
                      <td style={{ padding: '11px 14px', color: '#a89984' }}>{t.sl}</td>
                      <td style={{ padding: '11px 14px', color: '#a89984' }}>{t.tp}</td>
                      <td style={{ padding: '11px 14px', color: outcomeColor, fontWeight: 600 }}>
                        {t.outcome} {t.be_active ? '🛡️' : ''}
                      </td>
                      <td style={{ padding: '11px 14px', color: outcomeColor, fontWeight: 700 }}>
                        {t.pnl_r > 0 ? '+' : ''}{t.pnl_r}R
                      </td>
                      <td style={{ padding: '11px 14px', color: '#a89984', fontSize: 11 }}>{t.reason}</td>
                      <td style={{ padding: '11px 14px' }}>
                        <button
                          style={{
                            fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 600,
                            padding: '3px 8px', borderRadius: 4, background: 'rgba(250,189,47,0.12)',
                            color: '#fabd2f', border: '1px solid rgba(250,189,47,0.3)', cursor: 'pointer',
                          }}
                          onClick={(e) => { e.stopPropagation(); setSelectedTrade(t); }}
                        >
                          📊 View Chart
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* TradingView Chart Modal */}
        {selectedTrade && (
          <TradingViewChartModal trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
        )}

        {/* How Forward Testing Works Box */}
        <div style={{ ...glass, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#fabd2f', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            How The Automated Forward Test Works & BE Mechanism
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, fontSize: 13, color: '#a89984', lineHeight: 1.6 }}>
            <div>
              <strong style={{ color: '#ebdbb2', display: 'block', marginBottom: 4 }}>1. Breakeven Stop @ +1.5R</strong>
              Once price moves 1.5R towards the 1:4 target, Stop Loss is moved to entry price (BE) to protect capital against trend reversals.
            </div>
            <div>
              <strong style={{ color: '#ebdbb2', display: 'block', marginBottom: 4 }}>2. Strict Win Rate Metric</strong>
              Win Rate only counts full 1:4 target completions (`WIN`). Partial EOD closes and Breakevens do not artificially inflate Win Rate.
            </div>
            <div>
              <strong style={{ color: '#ebdbb2', display: 'block', marginBottom: 4 }}>3. Interactive Chart View</strong>
              Click any trade row or 📊 View Chart button to inspect 5m candle bars, entry price, SL, TP, and session price action.
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
