import { useState, useEffect } from 'react'

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 100,
      height: 56,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 40px',
      background: scrolled ? 'rgba(29,32,33,0.92)' : 'rgba(29,32,33,0.7)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(168,153,132,0.12)',
      transition: 'background 0.3s',
    }}>
      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 15, fontWeight: 700, color: '#fabd2f' }}>
        meegol<span style={{ color: '#a89984', fontWeight: 400 }}>/</span>backtest
      </span>
      <ul style={{ display: 'flex', gap: 32, listStyle: 'none', margin: 0, padding: 0 }}>
        {[['#results','results'],['#findings','findings'],['#setup','setup'],['#datasets','datasets']].map(([href, label]) => (
          <li key={href}>
            <a href={href} style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
              color: '#a89984', textDecoration: 'none',
              transition: 'color 0.2s',
            }}
              onMouseEnter={e => e.target.style.color = '#fabd2f'}
              onMouseLeave={e => e.target.style.color = '#a89984'}
            >{label}</a>
          </li>
        ))}
        <li>
          <a href="https://github.com/meegol/meegol-backtest" target="_blank" rel="noreferrer"
            style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#8ec07c', textDecoration: 'none' }}>
            ↗ github
          </a>
        </li>
      </ul>
    </nav>
  )
}
