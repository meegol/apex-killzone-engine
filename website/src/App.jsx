import Nav from './components/Nav'
import Hero from './components/Hero'
import Results from './components/Results'
import FilterImpact from './components/FilterImpact'
import Findings from './components/Findings'
import Setup from './components/Setup'

export default function App() {
  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      <Nav />
      <Hero />
      <div style={{ height: 1, background: 'rgba(168,153,132,0.08)', margin: '0 40px' }} />
      <Results />
      <div style={{ height: 1, background: 'rgba(168,153,132,0.08)', margin: '0 40px' }} />
      <FilterImpact />
      <div style={{ height: 1, background: 'rgba(168,153,132,0.08)', margin: '0 40px' }} />
      <Findings />
      <div style={{ height: 1, background: 'rgba(168,153,132,0.08)', margin: '0 40px' }} />
      <Setup />
      <footer style={{
        padding: 40, textAlign: 'center',
        fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#a89984',
        borderTop: '1px solid rgba(168,153,132,0.08)',
      }}>
        <div style={{ marginBottom: 6 }}>
          <a href="https://github.com/meegol/meegol-backtest" style={{ color: '#fabd2f', textDecoration: 'none' }}>
            github.com/meegol/meegol-backtest
          </a>
        </div>
        <div style={{ color: '#504945' }}>
          data: Yahoo Finance · period: May–Aug 2026 · 59 trading days · not financial advice
        </div>
      </footer>
    </div>
  )
}
