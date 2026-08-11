import { useState, useEffect } from 'react'

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  // close menu on nav link click
  const close = () => setOpen(false)

  const links = [
    ['#forward-test', '🔴 live forward test'],
    ['#results', 'results'],
    ['#findings', 'findings'],
    ['#setup', 'setup'],
    ['#datasets', 'datasets'],
  ]

  return (
    <>
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        height: 56,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 20px',
        background: scrolled ? 'rgba(29,32,33,0.96)' : 'rgba(29,32,33,0.7)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(168,153,132,0.12)',
        transition: 'background 0.3s',
      }}>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 15, fontWeight: 700, color: '#fabd2f' }}>
          apex<span style={{ color: '#a89984', fontWeight: 400 }}>/</span>killzone-engine
        </span>

        {/* desktop links */}
        <ul className="nav-links" style={{ display: 'flex', gap: 28, listStyle: 'none', margin: 0, padding: 0 }}>
          {links.map(([href, label]) => (
            <li key={href}>
              <a href={href} style={{
                fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                color: '#a89984', textDecoration: 'none', transition: 'color 0.2s',
              }}
                onMouseEnter={e => e.target.style.color = '#fabd2f'}
                onMouseLeave={e => e.target.style.color = '#a89984'}
              >{label}</a>
            </li>
          ))}
          <li>
            <a href="https://github.com/meegol/apex-killzone-engine" target="_blank" rel="noreferrer"
              style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#8ec07c', textDecoration: 'none' }}>
              ↗ github
            </a>
          </li>
        </ul>

        {/* hamburger — shown on mobile via CSS */}
        <button
          className="nav-mobile-toggle"
          onClick={() => setOpen(v => !v)}
          style={{
            display: 'none',
            background: 'none', border: 'none', cursor: 'pointer',
            flexDirection: 'column', gap: 5, padding: 6,
          }}
          aria-label="Toggle menu"
        >
          <span style={{ width: 22, height: 2, background: open ? '#fabd2f' : '#a89984', display: 'block', transition: 'all 0.2s', transform: open ? 'rotate(45deg) translate(5px,5px)' : 'none' }} />
          <span style={{ width: 22, height: 2, background: open ? '#fabd2f' : '#a89984', display: 'block', transition: 'all 0.2s', opacity: open ? 0 : 1 }} />
          <span style={{ width: 22, height: 2, background: open ? '#fabd2f' : '#a89984', display: 'block', transition: 'all 0.2s', transform: open ? 'rotate(-45deg) translate(5px,-5px)' : 'none' }} />
        </button>
      </nav>

      {/* mobile drawer */}
      {open && (
        <div style={{
          position: 'fixed', top: 56, left: 0, right: 0, zIndex: 99,
          background: 'rgba(29,32,33,0.98)', backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(168,153,132,0.15)',
          padding: '12px 0 20px',
        }}>
          {[...links, ['https://github.com/meegol/apex-killzone-engine', '↗ github']].map(([href, label]) => (
            <a
              key={href}
              href={href}
              onClick={close}
              style={{
                display: 'block', padding: '13px 24px',
                fontFamily: 'JetBrains Mono, monospace', fontSize: 14,
                color: label.includes('github') ? '#8ec07c' : '#a89984',
                textDecoration: 'none', borderBottom: '1px solid rgba(168,153,132,0.06)',
              }}
            >{label}</a>
          ))}
        </div>
      )}
    </>
  )
}
