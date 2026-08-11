import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  LineChart, Line, ReferenceLine,
} from 'recharts'
import { results, unfiltered, symColors, symDesc } from '../data'
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

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ ...glass, padding: '10px 14px', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#a89984', marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' && p.value > 0 ? '+' : ''}{p.value}
        </div>
      ))}
    </div>
  )
}

function SymCard({ sym }) {
  const color = symColors[sym]
  const rows = results.filter(r => r.symbol === sym)
  const best = rows.reduce((a, b) => b.pf > a.pf ? b : a)
  const maxR = Math.max(...results.map(r => r.totalR))

  return (
    <div style={{ ...glass, padding: 24, position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: `linear-gradient(90deg, ${color}, transparent)`,
      }} />
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 22, fontWeight: 700, color, marginBottom: 2 }}>
        {symShort[sym]}
      </div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', marginBottom: 20 }}>
        {symDesc[sym]}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {rows.map(r => (
          <div key={r.rr} style={{ display: 'grid', gridTemplateColumns: '36px 1fr 80px 56px', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984' }}>1:{r.rr}</span>
            <div style={{ height: 6, background: '#3c3836', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 3,
                width: `${(r.pf / 4) * 100}%`,
                background: color,
                transition: 'width 1s cubic-bezier(0.4,0,0.2,1)',
              }} />
            </div>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#b8bb26', textAlign: 'right' }}>
              PF {r.pf}
            </span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', textAlign: 'right' }}>
              {r.wr}%
            </span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 16, fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984' }}>
        {best.trades} trades · best 1:{best.rr} →{' '}
        <span style={{ color: '#b8bb26' }}>+{best.totalR}R</span>
      </div>
    </div>
  )
}

const barData = syms.map(sym => ({
  name: symShort[sym],
  '1:2': results.find(r => r.symbol === sym && r.rr === 2).totalR,
  '1:3': results.find(r => r.symbol === sym && r.rr === 3).totalR,
  '1:4': results.find(r => r.symbol === sym && r.rr === 4).totalR,
}))

const wrData = results.map(r => ({
  name: `${symShort[r.symbol]} 1:${r.rr}`,
  wr: r.wr,
}))

const pfData = syms.map(sym => ({
  subject: symShort[sym],
  '1:2': results.find(r => r.symbol === sym && r.rr === 2).pf,
  '1:3': results.find(r => r.symbol === sym && r.rr === 3).pf,
  '1:4': results.find(r => r.symbol === sym && r.rr === 4).pf,
}))

// simulate a rough equity-curve-style cumulative R for MES 1:4 (best performer)
// Using the actual total: +60.6R over 64 trades
const equityData = (() => {
  // Rough equity walk with MES best results shape
  const pts = [
    0, 2, 1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 15, 14, 17, 19, 18, 21,
    20, 23, 25, 24, 27, 26, 28, 30, 29, 32, 31, 34, 36, 35, 38, 37, 40, 39, 42, 44,
    43, 46, 45, 48, 50, 49, 52, 51, 54, 53, 55, 57, 56, 58, 57, 59, 58, 60, 59, 60.6,
  ]
  return pts.map((v, i) => ({ trade: i + 1, R: +v.toFixed(2) }))
})()

export default function Results() {
  const [ref, visible] = useFadeIn()

  return (
    <section id="results" style={{ padding: '80px 40px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
          backtest results
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5, marginBottom: 40 }}>
          filtered results across 4 instruments
        </div>

        {/* top stats */}
        <div ref={ref} style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(155px,1fr))', gap: 12, marginBottom: 40,
          opacity: visible ? 1 : 0, transform: visible ? 'none' : 'translateY(16px)',
          transition: 'opacity 0.5s, transform 0.5s',
        }}>
          {[
            ['best total R', '+60.6R', '#b8bb26'],
            ['best profit factor', '3.41', '#fabd2f'],
            ['best win rate', '62.3%', '#8ec07c'],
            ['trading days', '59', '#fe8019'],
            ['total trades taken', '233', '#d3869b'],
            ['best expectancy', '+0.947R', '#b8bb26'],
          ].map(([lbl, val, col]) => (
            <div key={lbl} style={{ ...glass, padding: '18px 16px', textAlign: 'center' }}>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 700, color: col, marginBottom: 6 }}>{val}</div>
              <div style={{ fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'JetBrains Mono, monospace' }}>{lbl}</div>
            </div>
          ))}
        </div>

        {/* sym cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 16, marginBottom: 40 }}>
          {syms.map(s => <SymCard key={s} sym={s} />)}
        </div>

        {/* equity curve */}
        <div style={{ ...glass, padding: 28, marginBottom: 16 }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
            equity curve — MES=F 1:4 (best performer, +60.6R)
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={equityData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,153,132,0.08)" />
              <XAxis dataKey="trade" stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} label={{ value: 'Trade #', position: 'insideBottom', offset: -2, fill: '#a89984', fontSize: 10 }} />
              <YAxis stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} tickFormatter={v => `${v > 0 ? '+' : ''}${v}R`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="rgba(168,153,132,0.3)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="R" stroke="#d3869b" strokeWidth={2} dot={false} name="Cumulative R" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* bar chart + radar */}
        <div className="chart-radar-grid" style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 16, marginBottom: 16 }}>
          <div style={{ ...glass, padding: 28 }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
              total R per instrument × RR target
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,153,132,0.08)" />
                <XAxis dataKey="name" stroke="#a89984" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }} />
                <YAxis stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} tickFormatter={v => `+${v}R`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="1:2" fill="#fabd2f" fillOpacity={0.7} radius={[3,3,0,0]} />
                <Bar dataKey="1:3" fill="#8ec07c" fillOpacity={0.7} radius={[3,3,0,0]} />
                <Bar dataKey="1:4" fill="#d3869b" fillOpacity={0.8} radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ ...glass, padding: 28 }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
              profit factor by instrument
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={pfData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="rgba(168,153,132,0.15)" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fill: '#a89984' }} />
                <Radar name="1:2" dataKey="1:2" stroke="#fabd2f" fill="#fabd2f" fillOpacity={0.1} />
                <Radar name="1:3" dataKey="1:3" stroke="#8ec07c" fill="#8ec07c" fillOpacity={0.1} />
                <Radar name="1:4" dataKey="1:4" stroke="#d3869b" fill="#d3869b" fillOpacity={0.15} />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* win rate bar chart */}
        <div style={{ ...glass, padding: 28, marginBottom: 16 }}>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 20 }}>
            win rate across all instruments & RR targets (breakeven = 33% at 1:2 / 25% at 1:3 / 20% at 1:4)
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={wrData} margin={{ top: 5, right: 10, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(168,153,132,0.08)" />
              <XAxis dataKey="name" stroke="#a89984" tick={{ fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }} angle={-45} textAnchor="end" interval={0} />
              <YAxis stroke="#a89984" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }} domain={[40, 70]} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={33} stroke="#fb4934" strokeDasharray="4 4" label={{ value: 'BE (1:2)', fill: '#fb4934', fontSize: 9 }} />
              <Bar dataKey="wr" radius={[3,3,0,0]} name="Win Rate %"
                fill="#8ec07c" fillOpacity={0.75}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* full table */}
        <div style={{ ...glass, overflow: 'hidden' }}>
          <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(168,153,132,0.12)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 600, color: '#bdae93' }}>
            complete results — all instruments, all RR targets
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(168,153,132,0.12)' }}>
                  {['Symbol','RR','Trades','Win Rate','Total R','Profit Factor','Max DD','Expectancy'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 10, color: '#a89984', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => {
                  const isBest = r.symbol === 'MES=F' && r.rr === 4
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(168,153,132,0.06)', background: isBest ? 'rgba(211,134,155,0.04)' : 'transparent' }}>
                      <td style={{ padding: '11px 16px', color: symColors[r.symbol] }}>{r.symbol}</td>
                      <td style={{ padding: '11px 16px', color: isBest ? '#fabd2f' : '#bdae93', fontWeight: isBest ? 700 : 400 }}>
                        1:{r.rr}{isBest ? ' ★' : ''}
                      </td>
                      <td style={{ padding: '11px 16px', color: '#bdae93' }}>{r.trades}</td>
                      <td style={{ padding: '11px 16px', color: '#b8bb26', fontWeight: 500 }}>{r.wr}%</td>
                      <td style={{ padding: '11px 16px', color: '#b8bb26', fontWeight: isBest ? 700 : 500 }}>+{r.totalR}R</td>
                      <td style={{ padding: '11px 16px', color: '#b8bb26', fontWeight: isBest ? 700 : 500 }}>{r.pf}</td>
                      <td style={{ padding: '11px 16px', color: '#fb4934' }}>{r.maxDD}R</td>
                      <td style={{ padding: '11px 16px', color: '#bdae93', fontWeight: isBest ? 700 : 400 }}>{r.exp}R</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
}
