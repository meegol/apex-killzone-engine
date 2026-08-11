import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, BaselineSeries, ColorType, LineStyle } from 'lightweight-charts';

const symColors = {
  'NQ=F': '#fabd2f',
  'ES=F': '#8ec07c',
  'MNQ=F': '#fe8019',
  'MES=F': '#d3869b',
};

function getUnixSec(b, tradeDate, index) {
  if (typeof b.time === 'number' && b.time > 100000000) return b.time;
  if (b.full_time) {
    const ts = Date.parse(b.full_time.replace(' ET', '').replace(' ', 'T'));
    if (!isNaN(ts)) return Math.floor(ts / 1000);
  }
  if (typeof b.time === 'string' && b.time.includes(':')) {
    const ts = Date.parse(`${tradeDate || '2026-01-01'}T${b.time}:00`);
    if (!isNaN(ts)) return Math.floor(ts / 1000);
  }
  const base = Date.parse(tradeDate || '2026-01-01') / 1000;
  return Math.floor(base + index * 300);
}

export default function TradingViewChartModal({ trade, onClose }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const [showZones, setShowZones] = useState(true);

  useEffect(() => {
    if (!containerRef.current || !trade || !trade.bars || trade.bars.length === 0) return;

    if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 380,
      layout: {
        background: { type: ColorType.Solid, color: '#1d2021' },
        textColor: '#a89984',
        fontSize: 11,
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: 'rgba(168,153,132,0.07)' },
        horzLines: { color: 'rgba(168,153,132,0.07)' },
      },
      crosshair: {
        vertLine: { color: 'rgba(250,189,47,0.5)', width: 1, style: LineStyle.Dashed },
        horzLine: { color: 'rgba(250,189,47,0.5)', width: 1, style: LineStyle.Dashed },
      },
      rightPriceScale: { borderColor: 'rgba(168,153,132,0.2)' },
      timeScale: { borderColor: 'rgba(168,153,132,0.2)', timeVisible: true, secondsVisible: false },
    });

    chartRef.current = chart;

    // --- Candlestick series ---
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: '#8ec07c', downColor: '#fb4934',
      borderUpColor: '#8ec07c', borderDownColor: '#fb4934',
      wickUpColor: '#8ec07c', wickDownColor: '#fb4934',
    });

    const seen = new Set();
    const bars = trade.bars
      .map((b, i) => ({ time: getUnixSec(b, trade.date, i), open: b.open, high: b.high, low: b.low, close: b.close }))
      .filter(b => { if (seen.has(b.time)) return false; seen.add(b.time); return true; })
      .sort((a, b) => a.time - b.time);

    candles.setData(bars);

    // --- Price lines: Entry, SL, TP ---
    const isLong = trade.direction === 'LONG';
    const isWin = trade.outcome === 'WIN';
    const isBE = trade.outcome === 'BE';

    candles.createPriceLine({
      price: trade.entry, color: '#fabd2f', lineWidth: 2, lineStyle: LineStyle.Solid,
      axisLabelVisible: true, title: '',
    });
    candles.createPriceLine({
      price: trade.sl, color: '#fb4934', lineWidth: 1, lineStyle: LineStyle.Dashed,
      axisLabelVisible: true, title: '',
    });
    candles.createPriceLine({
      price: trade.tp, color: '#8ec07c', lineWidth: 1, lineStyle: LineStyle.Dashed,
      axisLabelVisible: true, title: '',
    });

    // --- Position Tool: BaselineSeries with entry as baseline ---
    // Fills GREEN where price is in profit direction, RED where it's in loss direction
    // For LONG: green above entry (going up = profit), red below entry (going down = loss)
    // For SHORT: red above entry (going up = loss), green below entry (going down = profit)
    if (showZones && bars.length > 0) {
      const positionSeries = chart.addSeries(BaselineSeries, {
        baseValue: { type: 'price', price: trade.entry },
        // Above baseline
        topLineColor: isLong ? 'rgba(142,192,124,0.9)' : 'rgba(251,73,52,0.9)',
        topFillColor1: isLong ? 'rgba(142,192,124,0.28)' : 'rgba(251,73,52,0.28)',
        topFillColor2: isLong ? 'rgba(142,192,124,0.04)' : 'rgba(251,73,52,0.04)',
        // Below baseline
        bottomLineColor: isLong ? 'rgba(251,73,52,0.9)' : 'rgba(142,192,124,0.9)',
        bottomFillColor1: isLong ? 'rgba(251,73,52,0.04)' : 'rgba(142,192,124,0.04)',
        bottomFillColor2: isLong ? 'rgba(251,73,52,0.28)' : 'rgba(142,192,124,0.28)',
        lineWidth: 0,
        priceScaleId: 'right',
      });
      // Use actual close prices so the fill reflects real P&L territory
      positionSeries.setData(bars.map(b => ({ time: b.time, value: b.close })));
    }

    // Exit line — only draw if different from the static lines above
    const outcomePrice = isWin ? trade.tp : (isBE ? trade.entry : trade.sl);
    const outcomeColor = isWin ? '#b8bb26' : (isBE ? '#fabd2f' : '#fb4934');
    const outcomeIsDuplicate = outcomePrice === trade.tp || outcomePrice === trade.sl || outcomePrice === trade.entry;
    if (!outcomeIsDuplicate) {
      candles.createPriceLine({
        price: outcomePrice, color: outcomeColor, lineWidth: 2, lineStyle: LineStyle.LargeDashed,
        axisLabelVisible: true, title: '',
      });
    }

    chart.timeScale().fitContent();

    const onResize = () => { if (containerRef.current && chartRef.current) chartRef.current.applyOptions({ width: containerRef.current.clientWidth }); };
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      if (chartRef.current) { chartRef.current.remove(); chartRef.current = null; }
    };
  }, [trade, showZones]);

  if (!trade) return null;

  const isLong = trade.direction === 'LONG';
  const isWin = trade.outcome === 'WIN';
  const isBE = trade.outcome === 'BE';
  const outcomeColor = isWin ? '#b8bb26' : (isBE ? '#fabd2f' : '#fb4934');

  return (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(29,32,33,0.9)', backdropFilter: 'blur(20px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'clamp(8px, 3vw, 20px)' }}
      onClick={onClose}
    >
      <div
        style={{ background: 'rgba(36,39,40,0.97)', border: '1px solid rgba(168,153,132,0.25)', borderRadius: 16, width: '100%', maxWidth: 960, overflow: 'hidden', boxShadow: '0 24px 60px rgba(0,0,0,0.7)' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '14px 22px', borderBottom: '1px solid rgba(168,153,132,0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, background: 'rgba(29,32,33,0.6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 17, fontWeight: 700, color: symColors[trade.symbol] || '#fabd2f' }}>{trade.symbol}</span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 4, color: isLong ? '#8ec07c' : '#fb4934', background: isLong ? 'rgba(142,192,124,0.15)' : 'rgba(251,73,52,0.15)', border: `1px solid ${isLong ? '#8ec07c40' : '#fb493440'}` }}>
              {isLong ? '▲ LONG' : '▼ SHORT'} · 1:4 Target
            </span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 4, color: outcomeColor, background: `${outcomeColor}18`, border: `1px solid ${outcomeColor}35` }}>
              {trade.outcome} · {trade.pnl_r > 0 ? '+' : ''}{trade.pnl_r}R
            </span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#a89984' }}>{trade.entry_time}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => setShowZones(v => !v)} style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, padding: '5px 11px', borderRadius: 5, background: showZones ? 'rgba(250,189,47,0.12)' : 'rgba(168,153,132,0.08)', color: showZones ? '#fabd2f' : '#a89984', border: '1px solid rgba(168,153,132,0.2)', cursor: 'pointer' }}>
              {showZones ? '🎯 Zones On' : '🎯 Zones Off'}
            </button>
            <button onClick={onClose} style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, padding: '5px 11px', borderRadius: 5, background: 'rgba(168,153,132,0.08)', color: '#ebdbb2', border: '1px solid rgba(168,153,132,0.2)', cursor: 'pointer' }}>✕ Close</button>
          </div>
        </div>

        {/* Stat strip */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 1, background: 'rgba(29,32,33,0.5)', borderBottom: '1px solid rgba(168,153,132,0.1)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
          {[
            { label: 'ENTRY', value: trade.entry, color: '#fabd2f' },
            { label: 'STOP LOSS', value: trade.sl, color: '#fb4934' },
            { label: 'TAKE PROFIT (4R)', value: trade.tp, color: '#8ec07c' },
            { label: 'RISK (pts)', value: `${trade.risk_pts} pts`, color: '#ebdbb2' },
            { label: 'BE STOP', value: trade.be_active ? '🛡️ Active (+1.5R)' : 'Off', color: trade.be_active ? '#8ec07c' : '#a89984' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ padding: '10px 18px' }}>
              <div style={{ color: '#a89984', fontSize: 9, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 3 }}>{label}</div>
              <div style={{ color, fontWeight: 700 }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div style={{ padding: '14px 22px 8px' }}>
          <div ref={containerRef} className="tv-chart-container" style={{ width: '100%', height: 380, borderRadius: 6, overflow: 'hidden' }} />
        </div>

        {/* Footer */}
        <div style={{ padding: '8px 22px 14px', display: 'flex', justifyContent: 'space-between', fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#665c54' }}>
          <span>{trade.reason}</span>
          <span>TradingView Lightweight Charts™ · 5m bars · NY session</span>
        </div>
      </div>
    </div>
  );
}
