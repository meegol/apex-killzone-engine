const chips = [
  ['9:30–11 AM NY only', '#fabd2f'],
  ['HTF 4H bias filter', '#8ec07c'],
  ['premium / discount', '#83a598'],
  ['displacement strength', '#fe8019'],
  ['CISD + IFVG confirm', '#d3869b'],
]

export default function Hero() {
  return (
    <div style={{ padding: 'clamp(60px, 10vw, 100px) clamp(16px, 5vw, 40px) 80px', maxWidth: 1100, margin: '0 auto' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
        fontWeight: 500, color: '#8ec07c', letterSpacing: 2,
        textTransform: 'uppercase', marginBottom: 20,
      }}>
        <span style={{ display: 'inline-block', width: 20, height: 1, background: '#8ec07c' }} />
        ICT Kill Zone Backtester
      </div>

      <h1 style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 'clamp(36px, 6vw, 64px)',
        fontWeight: 700, lineHeight: 1.1,
        letterSpacing: -2, color: '#ebdbb2',
        marginBottom: 16,
      }}>
        NY Open.<br />
        <span style={{ color: '#fabd2f' }}>Kill Zone.</span><br />
        Does it work?
      </h1>

      <p style={{
        fontSize: 16, color: '#a89984', lineHeight: 1.8,
        maxWidth: 600, marginBottom: 36,
      }}>
        Backtesting an ICT-based strategy across NQ, ES, MNQ, and MES futures.
        9:30–11:00 AM New York time only. Sweeps, FVGs, IFVGs, and CISD confirmation —
        with HTF bias, premium/discount, and displacement strength filters.
        59 trading days of 5-minute data via Yahoo Finance.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 44 }}>
        {chips.map(([label, color]) => (
          <span key={label} style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
            padding: '5px 12px', borderRadius: 4,
            border: `1px solid ${color}40`,
            background: `${color}12`,
            color,
          }}>{label}</span>
        ))}
      </div>

      <div className="hero-buttons" style={{ display: 'flex', gap: 12 }}>
        <a href="#results" style={{
          fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 700,
          padding: '11px 24px', borderRadius: 6,
          background: '#fabd2f', color: '#1d2021',
          textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8,
          transition: 'background 0.2s, transform 0.2s',
        }}
          onMouseEnter={e => { e.currentTarget.style.background = '#d79921'; e.currentTarget.style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { e.currentTarget.style.background = '#fabd2f'; e.currentTarget.style.transform = 'translateY(0)' }}
        >view results</a>
        <a href="https://github.com/meegol/apex-killzone-engine" target="_blank" rel="noreferrer" style={{
          fontFamily: 'JetBrains Mono, monospace', fontSize: 13, fontWeight: 600,
          padding: '11px 24px', borderRadius: 6,
          border: '1px solid rgba(168,153,132,0.2)',
          color: '#bdae93', textDecoration: 'none',
          transition: 'border-color 0.2s, color 0.2s',
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = '#a89984'; e.currentTarget.style.color = '#ebdbb2' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(168,153,132,0.2)'; e.currentTarget.style.color = '#bdae93' }}
        >↗ github</a>
      </div>
    </div>
  )
}
