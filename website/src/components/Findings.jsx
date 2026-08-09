import { findings } from '../data'

const glass = {
  background: 'rgba(40,40,40,0.55)',
  backdropFilter: 'blur(20px) saturate(140%)',
  WebkitBackdropFilter: 'blur(20px) saturate(140%)',
  border: '1px solid rgba(168,153,132,0.15)',
  borderRadius: 12,
}

export default function Findings() {
  return (
    <section id="findings" style={{ padding: '80px 40px' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>
          analysis
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: '#ebdbb2', letterSpacing: -0.5, marginBottom: 40 }}>
          key findings
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {findings.map(f => (
            <div key={f.num} style={{ ...glass, padding: 28 }}>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984', marginBottom: 10 }}>{f.num}</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 16, fontWeight: 700, color: '#ebdbb2', marginBottom: 10 }}>{f.title}</div>
              <div style={{ fontSize: 14, color: '#a89984', lineHeight: 1.75 }}>{f.body}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
