"""
report_generator.py — Generates a rich, self-contained HTML dashboard
for the ICT Kill Zone backtest results.

Features:
  - Dark TradingView-inspired theme
  - Per-symbol tabs with per-RR sub-tabs
  - Equity curve, win/loss pie, monthly P&L bar, trigger breakdown
  - Full trade log table with colour-coded outcomes
  - All charts powered by Plotly.js (loaded from CDN)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

from backtester import Backtester


class ReportGenerator:
    PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js"

    # Colour palette (dark theme)
    BG        = "#0d1117"
    SURFACE   = "#161b22"
    SURFACE2  = "#21262d"
    BORDER    = "#30363d"
    TEXT      = "#e6edf3"
    TEXT_MUTED= "#8b949e"
    GREEN     = "#3fb950"
    RED       = "#f85149"
    BLUE      = "#58a6ff"
    GOLD      = "#d29922"
    PURPLE    = "#bc8cff"
    ORANGE    = "#db6d28"

    RR_COLOURS = {2.0: "#58a6ff", 3.0: "#3fb950", 4.0: "#bc8cff"}

    def __init__(self, results: Dict[str, Dict[float, List[dict]]]):
        """
        results: {symbol: {rr_target: [trade_dict, ...]}}
        """
        self.results = results
        self.run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ──────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────

    def generate(self, output_dir: str = "reports") -> str:
        os.makedirs(output_dir, exist_ok=True)
        fname = os.path.join(
            output_dir,
            f"ict_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        html = self._build_html()
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(html)
        return fname

    # ──────────────────────────────────────────────
    # HTML assembly
    # ──────────────────────────────────────────────

    def _build_html(self) -> str:
        symbols = list(self.results.keys())
        rr_targets = sorted({rr for sym in self.results.values() for rr in sym.keys()})

        # Build all chart data (Python → JSON)
        chart_data = self._build_chart_data(symbols, rr_targets)
        chart_json = json.dumps(chart_data)

        # Build HTML sections
        tabs_html  = self._symbol_tabs(symbols)
        panels_html = "".join(self._symbol_panel(sym, rr_targets) for sym in symbols)
        summary_cards = self._summary_cards(symbols, rr_targets)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ICT Kill Zone Backtester — Results</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="{self.PLOTLY_CDN}"></script>
<style>
{self._css()}
</style>
</head>
<body>

<!-- ── HEADER ────────────────────────────────── -->
<header class="site-header">
  <div class="header-inner">
    <div class="header-brand">
      <span class="logo-icon">◈</span>
      <div>
        <h1 class="header-title">ICT Kill Zone Backtester</h1>
        <p class="header-sub">9:30–11:00 AM NY · Sweep/FVG/IFVG/CISD Strategy</p>
      </div>
    </div>
    <div class="header-meta">
      <div class="meta-chip">
        <span class="meta-label">Instruments</span>
        <span class="meta-value">{" · ".join(symbols)}</span>
      </div>
      <div class="meta-chip">
        <span class="meta-label">RR Targets</span>
        <span class="meta-value">{" · ".join(f"1:{int(r)}" for r in rr_targets)}</span>
      </div>
      <div class="meta-chip">
        <span class="meta-label">Generated</span>
        <span class="meta-value">{self.run_time}</span>
      </div>
    </div>
  </div>
</header>

<!-- ── STRATEGY LEGEND ───────────────────────── -->
<section class="legend-bar">
  <div class="legend-inner">
    <div class="legend-item"><span class="badge badge-blue">Sweep + CISD</span>Price sweeps Asia/London/HTF high or low → Change in State of Delivery confirmation</div>
    <div class="legend-item"><span class="badge badge-green">FVG Tap</span>Price enters unmitigated 4H/1H Fair Value Gap → continuation signal</div>
    <div class="legend-item"><span class="badge badge-purple">IFVG</span>Inversion FVG re-test → momentum shift confirmation</div>
    <div class="legend-item"><span class="badge badge-gold">HTF Swing</span>4H Swing High/Low swept as additional liquidity target</div>
  </div>
</section>

<!-- ── GLOBAL SUMMARY CARDS ──────────────────── -->
<section class="global-summary">
  <div class="section-inner">
    <h2 class="section-title">Overall Performance Summary</h2>
    <div class="cards-grid">
      {summary_cards}
    </div>
  </div>
</section>

<!-- ── PER-SYMBOL DETAIL ─────────────────────── -->
<section class="detail-section">
  <div class="section-inner">
    <h2 class="section-title">Per-Instrument Detail</h2>

    <!-- Symbol tabs -->
    <div class="tab-bar sym-tabs" id="sym-tabs">
      {tabs_html}
    </div>

    <!-- Symbol panels -->
    <div class="panels-container">
      {panels_html}
    </div>
  </div>
</section>

<!-- ── EMBEDDED DATA + SCRIPTS ───────────────── -->
<script>
const CHART_DATA = {chart_json};
const COLORS = {{
  bg: "{self.BG}", surface: "{self.SURFACE}", surface2: "{self.SURFACE2}",
  border: "{self.BORDER}", text: "{self.TEXT}", muted: "{self.TEXT_MUTED}",
  green: "{self.GREEN}", red: "{self.RED}", blue: "{self.BLUE}",
  gold: "{self.GOLD}", purple: "{self.PURPLE}", orange: "{self.ORANGE}",
  rr: {{ 2: "{self.RR_COLOURS[2.0]}", 3: "{self.RR_COLOURS[3.0]}", 4: "{self.RR_COLOURS[4.0]}" }}
}};

{self._javascript()}
</script>
</body>
</html>"""

    # ──────────────────────────────────────────────
    # HTML fragments
    # ──────────────────────────────────────────────

    def _symbol_tabs(self, symbols: List[str]) -> str:
        tabs = []
        for i, sym in enumerate(symbols):
            active = 'active' if i == 0 else ''
            label  = sym.replace('=F', '')
            tabs.append(
                f'<button class="tab-btn {active}" '
                f'onclick="switchSymbol(this, \'{sym}\')" '
                f'data-sym="{sym}">{label}</button>'
            )
        return "\n".join(tabs)

    def _symbol_panel(self, sym: str, rr_targets: List[float]) -> str:
        rr_tab_html  = self._rr_tabs(sym, rr_targets)
        rr_panel_html = "".join(self._rr_panel(sym, rr) for rr in rr_targets)

        hidden = '' if sym == list(self.results.keys())[0] else 'hidden'
        return f"""
<div class="sym-panel {hidden}" data-sym="{sym}">
  <div class="rr-tab-bar" id="rr-tabs-{sym.replace('=','_')}">
    {rr_tab_html}
  </div>
  <div class="rr-panels">
    {rr_panel_html}
  </div>
</div>"""

    def _rr_tabs(self, sym: str, rr_targets: List[float]) -> str:
        tabs = []
        for i, rr in enumerate(rr_targets):
            active = 'active' if i == 0 else ''
            tabs.append(
                f'<button class="tab-btn rr-tab {active}" '
                f'onclick="switchRR(this, \'{sym}\', {rr})" '
                f'data-rr="{rr}">1:{int(rr)}</button>'
            )
        return "\n".join(tabs)

    def _rr_panel(self, sym: str, rr: float) -> str:
        trades = self.results.get(sym, {}).get(rr, [])
        metrics = Backtester.calc_metrics(trades)
        panel_id = f"panel_{sym.replace('=','_')}_{int(rr)}"
        chart_id = f"chart_{sym.replace('=','_')}_{int(rr)}"
        pie_id   = f"pie_{sym.replace('=','_')}_{int(rr)}"
        mbar_id  = f"mbar_{sym.replace('=','_')}_{int(rr)}"
        trg_id   = f"trg_{sym.replace('=','_')}_{int(rr)}"
        tbl_id   = f"tbl_{sym.replace('=','_')}_{int(rr)}"

        hidden   = '' if rr == sorted(self.results.get(sym, {}).keys())[0] else 'hidden'

        winsign  = '+' if metrics['total_r'] >= 0 else ''
        r_class  = 'green' if metrics['total_r'] >= 0 else 'red'
        pf_class = 'green' if metrics['profit_factor'] >= 1 else 'red'
        wr_class = 'green' if metrics['win_rate'] >= 50 else 'red'

        pf_txt = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] != float('inf') else "∞"

        metrics_html = f"""
<div class="metrics-strip">
  <div class="metric-box"><div class="metric-val">{metrics['total']}</div><div class="metric-lbl">Total Trades</div></div>
  <div class="metric-box"><div class="metric-val {wr_class}">{metrics['win_rate']}%</div><div class="metric-lbl">Win Rate</div></div>
  <div class="metric-box"><div class="metric-val {r_class}">{winsign}{metrics['total_r']}R</div><div class="metric-lbl">Total P&amp;L (R)</div></div>
  <div class="metric-box"><div class="metric-val {pf_class}">{pf_txt}</div><div class="metric-lbl">Profit Factor</div></div>
  <div class="metric-box"><div class="metric-val green">+{metrics['avg_win_r']}R</div><div class="metric-lbl">Avg Win</div></div>
  <div class="metric-box"><div class="metric-val red">{metrics['avg_loss_r']}R</div><div class="metric-lbl">Avg Loss</div></div>
  <div class="metric-box"><div class="metric-val red">-{metrics['max_drawdown_r']}R</div><div class="metric-lbl">Max Drawdown</div></div>
  <div class="metric-box"><div class="metric-val">{metrics['expectancy_r']}R</div><div class="metric-lbl">Expectancy</div></div>
  <div class="metric-box"><div class="metric-val">{metrics['sharpe']}</div><div class="metric-lbl">Sharpe (R)</div></div>
</div>"""

        table_html = self._trade_table(trades, tbl_id)

        return f"""
<div class="rr-panel {hidden}" id="{panel_id}" data-sym="{sym}" data-rr="{rr}">
  {metrics_html}

  <!-- Charts row 1: equity + pie -->
  <div class="charts-row">
    <div class="chart-card wide" id="{chart_id}"></div>
    <div class="chart-card narrow" id="{pie_id}"></div>
  </div>

  <!-- Charts row 2: monthly bar + trigger breakdown -->
  <div class="charts-row">
    <div class="chart-card half" id="{mbar_id}"></div>
    <div class="chart-card half" id="{trg_id}"></div>
  </div>

  <!-- Trade log -->
  <div class="trade-log-card">
    <div class="card-header">
      <span>Trade Log</span>
      <span class="trade-count">{len(trades)} trades</span>
    </div>
    {table_html}
  </div>
</div>"""

    def _trade_table(self, trades: List[dict], tbl_id: str) -> str:
        if not trades:
            return '<div class="empty-state">No trades found for this configuration.</div>'

        rows = []
        for i, t in enumerate(trades[:200]):   # cap display at 200
            cls  = 'win-row' if t['outcome'] == 'WIN' else 'loss-row'
            sign = '+' if t['pnl_r'] >= 0 else ''
            dir_badge = f'<span class="dir-badge dir-{"long" if t["direction"]=="LONG" else "short"}">{t["direction"]}</span>'
            conf_badge = f'<span class="conf-badge">{t["confirmation"]}</span>'
            rows.append(f"""
<tr class="{cls}">
  <td class="mono">{t['date']}</td>
  <td>{dir_badge}</td>
  <td class="mono">{t['entry']:.2f}</td>
  <td class="mono">{t['sl']:.2f}</td>
  <td class="mono">{t['tp']:.2f}</td>
  <td class="mono">{t['exit']:.2f}</td>
  <td class="pnl {'pos' if t['pnl_r']>=0 else 'neg'}">{sign}{t['pnl_r']:.2f}R</td>
  <td>{t['trigger']}</td>
  <td>{conf_badge}</td>
  <td class="mono">{t['bars_held']}</td>
</tr>""")

        header = """
<table class="trade-table" id="{tbl_id}">
  <thead>
    <tr>
      <th>Date</th><th>Dir</th><th>Entry</th><th>SL</th><th>TP</th>
      <th>Exit</th><th>P&amp;L (R)</th><th>Trigger</th><th>Confirm</th><th>Bars</th>
    </tr>
  </thead>
  <tbody>
"""
        return header.format(tbl_id=tbl_id) + "\n".join(rows) + "\n  </tbody>\n</table>"

    def _summary_cards(self, symbols: List[str], rr_targets: List[float]) -> str:
        cards = []
        for sym in symbols:
            sym_trades_all = []
            best_rr = None
            best_pf = -1

            for rr in rr_targets:
                trades = self.results.get(sym, {}).get(rr, [])
                sym_trades_all.extend(trades)
                m = Backtester.calc_metrics(trades)
                pf = m['profit_factor'] if m['profit_factor'] != float('inf') else 999
                if pf > best_pf:
                    best_pf = pf
                    best_rr = rr
                    best_metrics = m

            label = sym.replace('=F', '')
            wr_c  = 'green' if best_metrics['win_rate'] >= 50 else 'red'
            r_c   = 'green' if best_metrics['total_r'] >= 0 else 'red'
            sign  = '+' if best_metrics['total_r'] >= 0 else ''
            pf_txt = f"{best_pf:.2f}" if best_pf < 900 else "∞"

            cards.append(f"""
<div class="summary-card">
  <div class="sc-header">
    <span class="sc-symbol">{label}</span>
    <span class="sc-badge">Best: 1:{int(best_rr)}</span>
  </div>
  <div class="sc-metrics">
    <div><span class="sc-val {wr_c}">{best_metrics['win_rate']}%</span><span class="sc-lbl">Win Rate</span></div>
    <div><span class="sc-val {r_c}">{sign}{best_metrics['total_r']}R</span><span class="sc-lbl">Total R</span></div>
    <div><span class="sc-val">{pf_txt}</span><span class="sc-lbl">Prof. Factor</span></div>
    <div><span class="sc-val">{best_metrics['total']}</span><span class="sc-lbl">Trades</span></div>
  </div>
</div>""")
        return "\n".join(cards)

    # ──────────────────────────────────────────────
    # Chart data builder
    # ──────────────────────────────────────────────

    def _build_chart_data(
        self, symbols: List[str], rr_targets: List[float]
    ) -> dict:
        data = {}
        for sym in symbols:
            data[sym] = {}
            for rr in rr_targets:
                trades = self.results.get(sym, {}).get(rr, [])
                data[sym][str(rr)] = self._trades_to_chart_payload(trades)
        return data

    @staticmethod
    def _trades_to_chart_payload(trades: List[dict]) -> dict:
        if not trades:
            return {'equity': [], 'dates': [], 'monthly': {}, 'triggers': {}, 'outcomes': {}}

        pnls   = [t['pnl_r'] for t in trades]
        dates  = [t['date']  for t in trades]
        equity = list(np.cumsum(pnls))

        # Monthly P&L
        monthly: dict = {}
        for t in trades:
            mon = t['date'][:7]
            monthly[mon] = round(monthly.get(mon, 0.0) + t['pnl_r'], 2)

        # Trigger breakdown (wins vs losses per trigger)
        trigger_wins   = {}
        trigger_losses = {}
        for t in trades:
            tr = t['trigger']
            if t['outcome'] == 'WIN':
                trigger_wins[tr]   = trigger_wins.get(tr, 0) + 1
            else:
                trigger_losses[tr] = trigger_losses.get(tr, 0) + 1

        return {
            'equity':   [round(e, 3) for e in equity],
            'dates':    dates,
            'monthly':  monthly,
            'triggers': {'wins': trigger_wins, 'losses': trigger_losses},
            'outcomes': {
                'wins':   sum(1 for t in trades if t['outcome'] == 'WIN'),
                'losses': sum(1 for t in trades if t['outcome'] == 'LOSS'),
            },
        }

    # ──────────────────────────────────────────────
    # CSS
    # ──────────────────────────────────────────────

    def _css(self) -> str:
        return f"""
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg: {self.BG};
  --surface: {self.SURFACE};
  --surface2: {self.SURFACE2};
  --border: {self.BORDER};
  --text: {self.TEXT};
  --muted: {self.TEXT_MUTED};
  --green: {self.GREEN};
  --red: {self.RED};
  --blue: {self.BLUE};
  --gold: {self.GOLD};
  --purple: {self.PURPLE};
}}

body {{
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.5;
}}

/* ── HEADER ──────────────────────────────────── */
.site-header {{
  background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
  border-bottom: 1px solid var(--border);
  padding: 20px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}}
.header-inner {{
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}}
.header-brand {{
  display: flex;
  align-items: center;
  gap: 16px;
}}
.logo-icon {{
  font-size: 32px;
  color: var(--gold);
  text-shadow: 0 0 20px rgba(210,153,34,0.5);
  animation: pulse 3s ease-in-out infinite;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.6; }}
}}
.header-title {{
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, var(--text), var(--blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.header-sub {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}}
.header-meta {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}
.meta-chip {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.meta-label {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; }}
.meta-value {{ font-size: 12px; font-weight: 600; color: var(--text); font-family: 'JetBrains Mono', monospace; }}

/* ── LEGEND BAR ──────────────────────────────── */
.legend-bar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 12px 32px;
}}
.legend-inner {{
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: center;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}}
.badge {{
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}}
.badge-blue   {{ background: rgba(88,166,255,0.15); color: var(--blue); border: 1px solid rgba(88,166,255,0.3); }}
.badge-green  {{ background: rgba(63,185,80,0.15);  color: var(--green); border: 1px solid rgba(63,185,80,0.3); }}
.badge-purple {{ background: rgba(188,140,255,0.15);color: var(--purple); border: 1px solid rgba(188,140,255,0.3); }}
.badge-gold   {{ background: rgba(210,153,34,0.15); color: var(--gold); border: 1px solid rgba(210,153,34,0.3); }}

/* ── SECTIONS ────────────────────────────────── */
.global-summary, .detail-section {{
  padding: 32px;
}}
.section-inner {{
  max-width: 1600px;
  margin: 0 auto;
}}
.section-title {{
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}}

/* ── SUMMARY CARDS ───────────────────────────── */
.cards-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}}
.summary-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.2s, transform 0.2s;
}}
.summary-card:hover {{
  border-color: var(--blue);
  transform: translateY(-2px);
}}
.sc-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}}
.sc-symbol {{
  font-size: 18px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: var(--blue);
}}
.sc-badge {{
  font-size: 10px;
  background: rgba(210,153,34,0.2);
  color: var(--gold);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}}
.sc-metrics {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}}
.sc-metrics > div {{
  display: flex;
  flex-direction: column;
  gap: 2px;
}}
.sc-val {{
  font-size: 18px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}}
.sc-lbl {{
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}}

/* ── TAB BAR ─────────────────────────────────── */
.tab-bar {{
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}}
.tab-btn {{
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--muted);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  transition: color 0.2s, border-color 0.2s;
  margin-bottom: -1px;
}}
.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{ color: var(--blue); border-bottom-color: var(--blue); }}
.rr-tab.active {{ color: var(--gold); border-bottom-color: var(--gold); }}

/* ── METRICS STRIP ───────────────────────────── */
.metrics-strip {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}}
.metric-box {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  text-align: center;
  transition: border-color 0.2s;
}}
.metric-box:hover {{ border-color: var(--border); }}
.metric-val {{
  font-size: 20px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.2;
}}
.metric-lbl {{
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-top: 4px;
}}

/* ── COLOUR HELPERS ──────────────────────────── */
.green {{ color: var(--green); }}
.red   {{ color: var(--red); }}
.blue  {{ color: var(--blue); }}

/* ── CHARTS ──────────────────────────────────── */
.charts-row {{
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}}
.chart-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  min-height: 300px;
  overflow: hidden;
}}
.chart-card.wide   {{ flex: 2; }}
.chart-card.narrow {{ flex: 1; }}
.chart-card.half   {{ flex: 1; }}

/* ── TRADE LOG ───────────────────────────────── */
.trade-log-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  margin-top: 8px;
}}
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  font-size: 13px;
}}
.trade-count {{
  font-size: 11px;
  color: var(--muted);
  background: var(--surface2);
  padding: 2px 8px;
  border-radius: 4px;
}}
.trade-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}}
.trade-table thead tr {{
  background: var(--surface2);
}}
.trade-table th {{
  padding: 10px 14px;
  text-align: left;
  color: var(--muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
}}
.trade-table td {{
  padding: 9px 14px;
  border-bottom: 1px solid rgba(48,54,61,0.5);
  font-family: 'JetBrains Mono', monospace;
}}
.win-row  {{ background: rgba(63,185,80,0.04); }}
.loss-row {{ background: rgba(248,81,73,0.04); }}
.win-row:hover  {{ background: rgba(63,185,80,0.08); }}
.loss-row:hover {{ background: rgba(248,81,73,0.08); }}
.pnl.pos {{ color: var(--green); font-weight: 600; }}
.pnl.neg {{ color: var(--red);   font-weight: 600; }}
.mono {{ font-family: 'JetBrains Mono', monospace; }}

.dir-badge {{
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
}}
.dir-long  {{ background: rgba(63,185,80,0.2);  color: var(--green); }}
.dir-short {{ background: rgba(248,81,73,0.2);  color: var(--red); }}

.conf-badge {{
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(88,166,255,0.15);
  color: var(--blue);
}}

.empty-state {{
  padding: 48px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}}

.hidden {{ display: none !important; }}

@media (max-width: 768px) {{
  .charts-row {{ flex-direction: column; }}
  .site-header {{ padding: 16px; }}
  .global-summary, .detail-section {{ padding: 16px; }}
}}
"""

    # ──────────────────────────────────────────────
    # JavaScript
    # ──────────────────────────────────────────────

    def _javascript(self) -> str:
        return r"""
// ── Layout defaults for Plotly ────────────────────────────────────────
function plotLayout(title, xTitle, yTitle) {
  return {
    title: { text: title, font: { size: 13, color: COLORS.text }, x: 0.01 },
    paper_bgcolor: COLORS.surface,
    plot_bgcolor: COLORS.surface,
    font: { family: 'Inter, system-ui, sans-serif', color: COLORS.muted, size: 11 },
    xaxis: { gridcolor: COLORS.border, linecolor: COLORS.border, title: xTitle || '', tickfont: { size: 10 } },
    yaxis: { gridcolor: COLORS.border, linecolor: COLORS.border, title: yTitle || '', tickfont: { size: 10 } },
    margin: { l: 52, r: 20, t: 40, b: 40 },
    showlegend: false,
  };
}

// ── Render equity curve ───────────────────────────────────────────────
function renderEquity(elId, dates, equity, rr) {
  if (!document.getElementById(elId)) return;
  const colour = COLORS.rr[rr] || COLORS.blue;
  const zero   = Array(equity.length).fill(0);
  const trace  = {
    x: dates, y: equity,
    type: 'scatter', mode: 'lines',
    name: `Equity (1:${rr})`,
    line: { color: colour, width: 2 },
    fill: 'tozeroy',
    fillcolor: colour.replace(')', ', 0.08)').replace('rgb', 'rgba'),
    hovertemplate: '<b>%{x}</b><br>%{y:.2f}R<extra></extra>',
  };
  const zeroLine = {
    x: dates, y: zero,
    type: 'scatter', mode: 'lines',
    line: { color: COLORS.border, width: 1, dash: 'dot' },
    hoverinfo: 'skip',
  };
  const layout = plotLayout(`Equity Curve — 1:${rr} RR`, 'Trade #', 'Cumulative R');
  layout.showlegend = false;
  Plotly.newPlot(elId, [zeroLine, trace], layout, { responsive: true, displayModeBar: false });
}

// ── Render win/loss pie ───────────────────────────────────────────────
function renderPie(elId, wins, losses, rr) {
  if (!document.getElementById(elId)) return;
  const trace = {
    labels: ['Wins', 'Losses'],
    values: [wins, losses],
    type: 'pie',
    marker: { colors: [COLORS.green, COLORS.red] },
    hole: 0.55,
    textinfo: 'label+percent',
    textfont: { size: 12, color: COLORS.text },
    hovertemplate: '<b>%{label}</b>: %{value}<br>%{percent}<extra></extra>',
  };
  const layout = {
    ...plotLayout(`Win/Loss — 1:${rr}`),
    showlegend: false,
    annotations: [{
      text: `${wins}W<br>${losses}L`,
      x: 0.5, y: 0.5, showarrow: false,
      font: { size: 13, color: COLORS.text, family: 'JetBrains Mono' },
    }],
  };
  Plotly.newPlot(elId, [trace], layout, { responsive: true, displayModeBar: false });
}

// ── Render monthly P&L bar ────────────────────────────────────────────
function renderMonthly(elId, monthly, rr) {
  if (!document.getElementById(elId)) return;
  const months = Object.keys(monthly).sort();
  const vals   = months.map(m => monthly[m]);
  const colours = vals.map(v => v >= 0 ? COLORS.green : COLORS.red);
  const trace = {
    x: months, y: vals,
    type: 'bar',
    marker: { color: colours },
    hovertemplate: '<b>%{x}</b><br>%{y:.2f}R<extra></extra>',
  };
  const layout = plotLayout(`Monthly P&L (R) — 1:${rr}`, 'Month', 'R');
  Plotly.newPlot(elId, [trace], layout, { responsive: true, displayModeBar: false });
}

// ── Render trigger breakdown ──────────────────────────────────────────
function renderTriggers(elId, triggers, rr) {
  if (!document.getElementById(elId)) return;
  const allTriggers = new Set([
    ...Object.keys(triggers.wins || {}),
    ...Object.keys(triggers.losses || {}),
  ]);
  const labels = Array.from(allTriggers);
  const winVals  = labels.map(l => (triggers.wins   || {})[l] || 0);
  const lossVals = labels.map(l => (triggers.losses || {})[l] || 0);
  const traces = [
    { x: labels, y: winVals,  name: 'Wins',   type: 'bar', marker: { color: COLORS.green }, hovertemplate: '<b>%{x}</b> Win<br>%{y} trades<extra></extra>' },
    { x: labels, y: lossVals, name: 'Losses', type: 'bar', marker: { color: COLORS.red },   hovertemplate: '<b>%{x}</b> Loss<br>%{y} trades<extra></extra>' },
  ];
  const layout = { ...plotLayout(`Trigger Breakdown — 1:${rr}`, 'Trigger', 'Trades'), barmode: 'group', showlegend: true };
  Plotly.newPlot(elId, traces, layout, { responsive: true, displayModeBar: false });
}

// ── Render all charts for a given symbol+RR panel ────────────────────
function renderPanel(sym, rr) {
  const key = String(rr);
  const d = (CHART_DATA[sym] || {})[key] || {};
  const sfx = sym.replace('=', '_') + '_' + parseInt(rr);

  renderEquity   (`chart_${sfx}`, d.dates || [], d.equity || [], rr);
  renderPie      (`pie_${sfx}`,   (d.outcomes||{}).wins||0, (d.outcomes||{}).losses||0, rr);
  renderMonthly  (`mbar_${sfx}`,  d.monthly || {}, rr);
  renderTriggers (`trg_${sfx}`,   d.triggers || {}, rr);
}

// ── Tab switching ─────────────────────────────────────────────────────
function switchSymbol(btn, sym) {
  document.querySelectorAll('.tab-btn[data-sym]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.sym-panel').forEach(p => {
    p.classList.toggle('hidden', p.dataset.sym !== sym);
  });
  // Activate first RR tab for this symbol
  const firstRRBtn = document.querySelector(`.rr-tab[data-rr]`);
  if (firstRRBtn) {
    const rr = parseFloat(firstRRBtn.dataset.rr);
    activateRR(sym, rr);
  }
}

function switchRR(btn, sym, rr) {
  const container = btn.closest('.rr-tab-bar');
  container.querySelectorAll('.rr-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activateRR(sym, rr);
}

function activateRR(sym, rr) {
  const sfx = sym.replace('=', '_');
  document.querySelectorAll(`.rr-panel[data-sym="${sym}"]`).forEach(p => {
    const active = parseFloat(p.dataset.rr) === rr;
    p.classList.toggle('hidden', !active);
    if (active) renderPanel(sym, rr);
  });
}

// ── Initial render on page load ───────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  const firstSymBtn = document.querySelector('.tab-btn[data-sym]');
  if (!firstSymBtn) return;
  const sym = firstSymBtn.dataset.sym;
  firstSymBtn.classList.add('active');

  // Render first RR panel for first symbol
  const firstRRBtn = document.querySelector('.rr-tab');
  if (firstRRBtn) {
    const rr = parseFloat(firstRRBtn.dataset.rr);
    firstRRBtn.classList.add('active');
    renderPanel(sym, rr);
  }
});
"""
