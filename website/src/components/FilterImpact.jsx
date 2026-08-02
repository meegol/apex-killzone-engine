import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { unfiltered, results, symColors } from '../data'
import { useFadeIn } from '../hooks'

const glass = {
  background: 'rgba(40,40,40,0.55)',
  backdropFilter: 'blur(20px) saturate(140%)',
  WebkitBackdropFilter: 'blur(20px) saturate(140%)',
  border: '1px solid rgba(168,153,132,0.15)',
  borderRadius: 12,
}

const syms = ['NQ=F', 'ES=F', 'MNQ=F', 'MES=F']
const symShort = { 'NQ=F': 'NQ', 'ES=F': 'ES', 'MNQ=F': 'MNQ', 'MES=F': 'MES' }

const compareData = syms.map(sym => {
  const uf = unfiltered.find(r => r.symbol === sym)
  const fi = results.find(r => r.symbol === sym && r.rr === 4)
  return {
    name: symShort[sym],
    'unfiltered': uf.totalR,
    'filtered': fi.totalR,
    color: symColors[sym],
  }
})

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ ...glass, padding: '10px 14px', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#a89984', marginBottom: 4 }}>{label} (1:4)</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.value >= 0 ? '#b8bb26' : '#fb4934' }}>
          {p.name}: {p.value > 0 ? '+' : ''}{p.value}R
        </div>
      ))}
    </div>
  )
}

export default function FilterImpact() {
  const [ref, visible] = useFadeIn()

  return (
    <section style={{ padding: '80px 40px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
          filter impact
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5, marginBottom: 16 }}>
          before vs after filters
        </div>
        <p style={{ color: '#a89984', fontSize: 14, lineHeight: 1.8, maxWidth: 700, marginBottom: 36 }}>
          Without filters the strategy was unprofitable across most instruments — around 30% win rate
          and negative expectancy. Three filters cut trade count by ~60% and flipped every instrument
          to profitable with profit factors above 2.3.
        </p>

        {/* comparison chart */}
        <div style={{ ...glass, padding: 28, marginBottom: 24 }} ref={ref}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
            total R at 1:4 — unfiltered vs filtered
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={compareData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,153,132,0.08)" />
              <XAxis dataKey="name" stroke="#a89984" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }} />
              <YAxis stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} tickFormatter={v => `${v > 0 ? '+' : ''}${v}R`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="unfiltered" name="unfiltered" radius={[3,3,0,0]}>
                {compareData.map((d) => (
                  <Cell key={d.name} fill={d.unfiltered >= 0 ? 'rgba(152,151,26,0.5)' : 'rgba(204,36,29,0.6)'} />
                ))}
              </Bar>
              <Bar dataKey="filtered" name="filtered" radius={[3,3,0,0]}>
                {compareData.map((d) => (
                  <Cell key={d.name} fill={d.color} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* comparison table */}
        <div style={{ ...glass, overflow: 'hidden', marginBottom: 48 }}>
          <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(168,153,132,0.12)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93' }}>
            side-by-side at 1:4 RR
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(168,153,132,0.12)' }}>
                  {['Symbol','','Trades','Win Rate','Total R','Profit Factor','','Trades','Win Rate','Total R','Profit Factor'].map((h, i) => (
                    <th key={i} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 10, color: i === 5 ? '#fb4934' : i > 5 ? '#b8bb26' : '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
                <tr style={{ borderBottom: '1px solid rgba(168,153,132,0.08)' }}>
                  <th style={{ padding: '4px 14px 10px', fontSize: 10, color: '#a89984' }} />
                  <th style={{ padding: '4px 14px 10px', fontSize: 10, color: '#fb4934' }}>UNFILTERED</th>
                  <th colSpan={3} />
                  <th style={{ padding: '4px 14px 10px', fontSize: 10, color: '#fb4934' }} />
                  <th style={{ padding: '4px 14px 10px', fontSize: 10, color: '#b8bb26' }}>FILTERED</th>
                  <th colSpan={3} />
                </tr>
              </thead>
              <tbody>
                {syms.map(sym => {
                  const uf = unfiltered.find(r => r.symbol === sym)
                  const fi = results.find(r => r.symbol === sym && r.rr === 4)
                  return (
                    <tr key={sym} style={{ borderBottom: '1px solid rgba(168,153,132,0.06)' }}>
                      <td style={{ padding: '11px 14px', color: symColors[sym] }}>{sym}</td>
                      <td style={{ padding: '11px 14px', color: '#a89984' }} />
                      <td style={{ padding: '11px 14px', color: '#a89984' }}>{uf.trades}</td>
                      <td style={{ padding: '11px 14px', color: '#fb4934' }}>{uf.wr}%</td>
                      <td style={{ padding: '11px 14px', color: uf.totalR >= 0 ? '#b8bb26' : '#fb4934' }}>{uf.totalR > 0 ? '+' : ''}{uf.totalR}R</td>
                      <td style={{ padding: '11px 14px', color: uf.pf >= 1 ? '#b8bb26' : '#fb4934' }}>{uf.pf}</td>
                      <td style={{ padding: '11px 14px', color: '#a89984', fontSize: 16 }}>→</td>
                      <td style={{ padding: '11px 14px', color: '#b8bb26', fontWeight: 600 }}>{fi.trades}</td>
                      <td style={{ padding: '11px 14px', color: '#b8bb26', fontWeight: 600 }}>{fi.wr}%</td>
                      <td style={{ padding: '11px 14px', color: '#b8bb26', fontWeight: 600 }}>+{fi.totalR}R</td>
                      <td style={{ padding: '11px 14px', color: '#b8bb26', fontWeight: 600 }}>{fi.pf}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* filter cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            ['◈', 'HTF 4H Bias', '#fabd2f', 'Only trade with the 4H trend direction. If the last two 4H closes are ascending → longs only. Descending → shorts only. Counter-trend setups are skipped entirely — they account for the majority of filtered-out losses.'],
            ['◇', 'Premium / Discount', '#8ec07c', 'The London Kill Zone range is split at its midpoint. Shorts only above the midpoint (premium). Longs only below it (discount). No equilibrium trades. This single filter eliminates a large class of mean-reversion traps.'],
            ['△', 'Displacement Strength', '#fe8019', 'The CISD candle body must be at least 1.3× the 20-bar average body size. Weak, indecisive reversals that lack institutional conviction are discarded. Tune the multiplier in backtester.py.'],
          ].map(([icon, name, color, desc]) => (
            <div key={name} style={{ ...glass, padding: 24 }}>
              <div style={{ fontSize: 20, marginBottom: 12, color }}>{icon}</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700, color: '#ebdbb2', marginBottom: 8 }}>{name}</div>
              <div style={{ fontSize: 13, color: '#a89984', lineHeight: 1.7 }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
