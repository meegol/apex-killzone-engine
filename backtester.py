"""
backtester.py — ICT Kill Zone Strategy Backtester (Filtered + Live Output)

Filters applied on top of base signals:
  1. Premium/Discount (PD) Zone — only SHORT in premium, LONG in discount
  2. HTF 4H Trend Bias         — trade with the 4H trend direction only
  3. Displacement Strength     — CISD candle must be > 1.5x avg body size
  4. Confluence Bonus          — sweeps that align with an HTF FVG score higher

Live output shows every day, every signal, every filter check, every trade result.
"""

from __future__ import annotations

import copy
import sys
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import pytz

from strategy import FVG, ICTStrategy, SessionLevels, SwingPoint

ET = pytz.timezone('America/New_York')

MAX_TRADES_PER_DAY = 3

# ANSI colours (works in most modern terminals)
C = {
    'reset':  '\033[0m',
    'bold':   '\033[1m',
    'dim':    '\033[2m',
    'green':  '\033[92m',
    'red':    '\033[91m',
    'yellow': '\033[93m',
    'blue':   '\033[94m',
    'cyan':   '\033[96m',
    'magenta':'\033[95m',
    'white':  '\033[97m',
    'gray':   '\033[90m',
}


def _p(*args, **kwargs):
    """Print and immediately flush so output appears live."""
    print(*args, **kwargs)
    sys.stdout.flush()


def _col(text: str, colour: str) -> str:
    return f"{C.get(colour, '')}{text}{C['reset']}"


class Backtester:
    def __init__(
        self,
        strategy: ICTStrategy,
        rr_targets: List[float] = (2.0, 3.0, 4.0),
        symbol: str = '',
    ):
        self.strategy   = strategy
        self.rr_targets = list(rr_targets)
        self.df_5m      = strategy.df_5m
        self.symbol     = symbol

    # ──────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────

    def run(self) -> Dict[float, List[dict]]:
        """Run full backtest with live console output."""
        all_trades: Dict[float, List[dict]] = {rr: [] for rr in self.rr_targets}
        days = self.strategy.get_trading_days()
        total_setups = 0

        _p()
        _p(_col(f"  {'DATE':<12} {'SESSION LEVELS':<42} {'SETUPS':>6} {'RUNNING R (1:2 / 1:3 / 1:4)'}", 'dim'))
        _p(_col("  " + "-" * 90, 'gray'))

        running_r = {rr: 0.0 for rr in self.rr_targets}

        for date in days:
            try:
                day_trades, day_summary = self._process_day(date, running_r)
            except Exception as exc:
                _p(_col(f"  {str(date.date()):<12} [ERROR] {exc}", 'red'))
                continue

            for rr, trades in day_trades.items():
                all_trades[rr].extend(trades)
                running_r[rr] = round(running_r[rr] + sum(t['pnl_r'] for t in trades), 2)

            total_setups += day_summary['setups']
            self._print_day_line(date, day_summary, running_r)

        _p(_col("  " + "-" * 90, 'gray'))
        _p()
        self._print_final_summary(all_trades)

        return all_trades

    # ──────────────────────────────────────────────
    # Per-day processing
    # ──────────────────────────────────────────────

    def _process_day(
        self, date: pd.Timestamp, running_r: dict
    ):
        d = date.date()

        kz_start = ET.localize(datetime(d.year, d.month, d.day, 9, 30))
        kz_end   = ET.localize(datetime(d.year, d.month, d.day, 11,  0))
        eod      = ET.localize(datetime(d.year, d.month, d.day, 16,  0))
        ctx_start= ET.localize(datetime(d.year, d.month, d.day,  7,  0))

        context_bars = self.df_5m.loc[
            (self.df_5m.index >= ctx_start) & (self.df_5m.index < kz_end)
        ]
        kz_bars = self.df_5m.loc[
            (self.df_5m.index >= kz_start) & (self.df_5m.index < kz_end)
        ]

        empty_result = {rr: [] for rr in self.rr_targets}
        summary = {'setups': 0, 'levels': '', 'signals': [], 'filtered': 0}

        if kz_bars.empty:
            summary['levels'] = 'no KZ bars'
            return empty_result, summary

        kz_range = kz_bars['high'].max() - kz_bars['low'].min()
        if kz_range <= 0:
            summary['levels'] = 'zero range'
            return empty_result, summary

        levels     = self.strategy.get_session_levels(date)
        fvgs_orig  = self.strategy.find_fvgs(as_of=kz_start)
        swing_pts  = self.strategy.find_swing_points(as_of=kz_start)

        # HTF 4H bias
        htf_bias = self._htf_bias(date)

        # Build PD zone from London range (or 4H range fallback)
        pd_mid = self._pd_midpoint(levels, kz_bars)

        # Session levels summary string for display
        summary['levels'] = self._fmt_levels(levels)
        summary['htf_bias'] = htf_bias

        key_levels = self._build_key_levels(levels, swing_pts, kz_bars)
        fvgs = copy.deepcopy(fvgs_orig)
        ctx_idx_map = {ts: i for i, ts in enumerate(context_bars.index)}

        entries_taken: set = set()
        setups: List[dict] = []
        signals_log: List[str] = []
        filtered_count = 0

        for bar_time, bar in kz_bars.iterrows():
            ICTStrategy.update_fvg_status(fvgs, bar, bar_time)
            ctx_i = ctx_idx_map.get(bar_time, -1)
            if ctx_i < 0:
                continue
            if len(setups) >= MAX_TRADES_PER_DAY:
                break

            # ── SWEEP + CISD ───────────────────────────────────────
            for lvl in key_levels:
                if lvl['label'] in entries_taken:
                    continue
                if not ICTStrategy.check_sweep(bar, lvl['price'], lvl['type']):
                    continue

                sweep_type  = 'bearish' if lvl['type'] == 'high' else 'bullish'
                direction   = 'SHORT' if sweep_type == 'bearish' else 'LONG'

                # ── FILTERS ────────────────────────────────────────
                fail_reason = self._apply_filters(
                    direction, htf_bias, bar['close'], pd_mid,
                    context_bars, ctx_i
                )

                log_entry = (
                    f"{bar_time.strftime('%H:%M')} "
                    f"[SWEEP ] {lvl['label']} @ {lvl['price']:.2f}  "
                    f"H:{bar['high']:.2f} C:{bar['close']:.2f} → {sweep_type.upper()}"
                )

                if fail_reason:
                    filtered_count += 1
                    signals_log.append(log_entry + f"  {_col('[FILTERED: ' + fail_reason + ']', 'yellow')}")
                    continue

                # ── FIND CISD ──────────────────────────────────────
                disp_open = self._get_displacement_open(context_bars, ctx_i, sweep_type)
                ctx_window = context_bars.iloc[max(0, ctx_i - 5): min(len(context_bars), ctx_i + 10)]
                local_sweep = min(5, ctx_i)

                cisd_local = ICTStrategy.find_cisd(
                    ctx_window, sweep_type, local_sweep,
                    displacement_open=disp_open, max_bars_ahead=8
                )

                # ── DISPLACEMENT STRENGTH CHECK ────────────────────
                disp_ok = True
                if cisd_local is not None and cisd_local < len(ctx_window):
                    disp_ok = self._check_displacement_strength(context_bars, ctx_i, sweep_type)

                if cisd_local is None or cisd_local >= len(ctx_window) or not disp_ok:
                    reason = "no CISD" if cisd_local is None else "weak displacement"
                    signals_log.append(log_entry + f"  {_col('[NO CONFIRM: ' + reason + ']', 'gray')}")
                    continue

                conf_time = ctx_window.index[cisd_local]
                if conf_time > kz_end:
                    signals_log.append(log_entry + f"  {_col('[NO CONFIRM: outside KZ]', 'gray')}")
                    continue

                conf_bar = ctx_window.iloc[cisd_local]
                setup = self._build_sweep_setup(
                    bar, bar_time, conf_bar, conf_time,
                    sweep_type, lvl['label'], kz_range
                )
                if setup:
                    setups.append(setup)
                    entries_taken.add(lvl['label'])
                    signals_log.append(
                        log_entry +
                        f"  {_col('[CISD @ ' + conf_time.strftime('%H:%M') + ']', 'cyan')}"
                    )

            # ── FVG TAP ────────────────────────────────────────────
            fvg_hit = ICTStrategy.check_fvg_tap(bar, fvgs)
            fvg_key = f'FVG_{fvg_hit.formed_time}' if fvg_hit else None
            if fvg_hit and fvg_key not in entries_taken:
                direction = 'LONG' if fvg_hit.fvg_type == 'bullish' else 'SHORT'
                fail_reason = self._apply_filters(
                    direction, htf_bias, bar['close'], pd_mid, context_bars, ctx_i
                )
                log_entry = (
                    f"{bar_time.strftime('%H:%M')} "
                    f"[{fvg_hit.timeframe} FVG] {fvg_hit.fvg_type.upper()} "
                    f"zone {fvg_hit.bottom:.2f}-{fvg_hit.top:.2f}"
                )
                if fail_reason:
                    filtered_count += 1
                    signals_log.append(log_entry + f"  {_col('[FILTERED: ' + fail_reason + ']', 'yellow')}")
                else:
                    setup = self._build_fvg_setup(bar, bar_time, fvg_hit, kz_range, 'FVG')
                    if setup:
                        setups.append(setup)
                        entries_taken.add(fvg_key)
                        signals_log.append(log_entry + f"  {_col('[ENTERED]', 'cyan')}")

            # ── IFVG TAP ───────────────────────────────────────────
            ifvg_hit = ICTStrategy.check_ifvg_tap(bar, fvgs)
            ifvg_key = f'IFVG_{ifvg_hit.formed_time}' if ifvg_hit else None
            if ifvg_hit and ifvg_key not in entries_taken:
                direction = 'LONG' if ifvg_hit.fvg_type == 'bearish' else 'SHORT'
                fail_reason = self._apply_filters(
                    direction, htf_bias, bar['close'], pd_mid, context_bars, ctx_i
                )
                log_entry = (
                    f"{bar_time.strftime('%H:%M')} "
                    f"[{ifvg_hit.timeframe} IFVG] inverted {ifvg_hit.fvg_type.upper()} "
                    f"zone {ifvg_hit.bottom:.2f}-{ifvg_hit.top:.2f}"
                )
                if fail_reason:
                    filtered_count += 1
                    signals_log.append(log_entry + f"  {_col('[FILTERED: ' + fail_reason + ']', 'yellow')}")
                else:
                    setup = self._build_fvg_setup(bar, bar_time, ifvg_hit, kz_range, 'IFVG')
                    if setup:
                        setups.append(setup)
                        entries_taken.add(ifvg_key)
                        signals_log.append(log_entry + f"  {_col('[ENTERED]', 'cyan')}")

        # ── SIMULATE TRADES ────────────────────────────────────────
        forward_pool = self.df_5m.loc[self.df_5m.index <= eod]
        all_day_trades: Dict[float, List[dict]] = {rr: [] for rr in self.rr_targets}

        for setup in setups:
            fwd = forward_pool.loc[forward_pool.index > setup['entry_time']]
            trade_results = {}
            for rr in self.rr_targets:
                trade = self._simulate_trade(setup, fwd, rr)
                if trade:
                    all_day_trades[rr].append(trade)
                    trade_results[rr] = trade

            # Print trade detail block
            if trade_results:
                _p()
                _p(_col(f"    >>> {date.strftime('%Y-%m-%d %A')}", 'bold'))
                _p(_col(f"        HTF Bias: {htf_bias.upper()}", 'blue'))
                _p(_col(f"        {summary['levels']}", 'dim'))

                # Print all signals for this day
                for sig in signals_log:
                    _p(f"        {sig}")
                signals_log.clear()  # only print once

                first_trade = next(iter(trade_results.values()))
                dir_col = 'green' if first_trade['direction'] == 'LONG' else 'red'
                _p(
                    f"        {_col(first_trade['direction'], dir_col)} "
                    f"Entry:{first_trade['entry']:.2f}  "
                    f"SL:{first_trade['sl']:.2f}  "
                    f"Risk:{first_trade['risk_pts']:.1f}pts  "
                    f"[{first_trade['reason']}]"
                )
                for rr, t in sorted(trade_results.items()):
                    outcome_col = 'green' if t['outcome'] == 'WIN' else 'red'
                    sign = '+' if t['pnl_r'] >= 0 else ''
                    _p(
                        f"        {_col(f'1:{int(rr)}', 'yellow')} "
                        f"TP:{t['tp']:.2f}  "
                        f"{_col(t['outcome'], outcome_col)}  "
                        f"{_col(sign + str(t['pnl_r']) + 'R', outcome_col)}  "
                        f"exit@{t['exit_time'].strftime('%H:%M') if t['exit_time'] else '?'}"
                    )
                _p()

        # Print remaining signals (days with signals but no entries)
        if signals_log and not setups:
            for sig in signals_log:
                pass  # suppress signal-only days to keep output clean

        summary['setups']   = len(setups)
        summary['filtered'] = filtered_count
        summary['signals']  = signals_log

        return all_day_trades, summary

    # ──────────────────────────────────────────────
    # Filters
    # ──────────────────────────────────────────────

    def _htf_bias(self, date: pd.Timestamp) -> str:
        """
        4H trend bias via last two 4H swing structure points.
        If the last 4H swing high is above the previous → bullish.
        If the last 4H swing low is below the previous  → bearish.
        Returns 'bullish', 'bearish', or 'neutral'.
        """
        kz_start = ET.localize(datetime(date.date().year, date.date().month, date.date().day, 9, 30))
        df4 = self.strategy.df_4h.loc[self.strategy.df_4h.index < kz_start].tail(6)
        if len(df4) < 4:
            return 'neutral'

        closes = df4['close'].values
        # Simple: last close vs close 2 bars ago
        if closes[-1] > closes[-3]:
            return 'bullish'
        elif closes[-1] < closes[-3]:
            return 'bearish'
        return 'neutral'

    def _pd_midpoint(self, levels: Optional[SessionLevels], kz_bars: pd.DataFrame) -> Optional[float]:
        """Premium/Discount midpoint. Uses London range if available, else KZ range."""
        if levels and levels.has_london and not np.isnan(levels.london_high):
            return (levels.london_high + levels.london_low) / 2
        return (kz_bars['high'].max() + kz_bars['low'].min()) / 2

    def _apply_filters(
        self,
        direction: str,
        htf_bias: str,
        current_price: float,
        pd_mid: Optional[float],
        context_bars: pd.DataFrame,
        ctx_i: int,
    ) -> Optional[str]:
        """
        Run all filters. Returns None if setup passes, or a reason string if it fails.

        Filter 1 — HTF Bias: trade WITH the 4H trend only.
        Filter 2 — PD Zone: SHORT only in premium (above mid), LONG only in discount (below mid).
        """
        # Filter 1: HTF bias
        if htf_bias == 'bullish' and direction == 'SHORT':
            return 'HTF bias bullish'
        if htf_bias == 'bearish' and direction == 'LONG':
            return 'HTF bias bearish'

        # Filter 2: Premium / Discount
        if pd_mid is not None:
            if direction == 'SHORT' and current_price < pd_mid:
                return 'price in discount (need premium for short)'
            if direction == 'LONG' and current_price > pd_mid:
                return 'price in premium (need discount for long)'

        return None  # All filters passed

    def _check_displacement_strength(
        self,
        context_bars: pd.DataFrame,
        sweep_ctx_idx: int,
        sweep_type: str,
        multiplier: float = 1.3,
    ) -> bool:
        """
        Returns True if the displacement move into the sweep was strong
        (average body size of last 3 bars before sweep > multiplier × 20-bar avg).
        """
        lookback = 20
        start = max(0, sweep_ctx_idx - lookback)
        segment = context_bars.iloc[start: sweep_ctx_idx + 1]
        if len(segment) < 5:
            return True  # can't assess, allow through

        bodies = (segment['close'] - segment['open']).abs()
        avg_body = bodies.mean()
        if avg_body <= 0:
            return True

        last_3 = bodies.iloc[-3:].mean()
        return last_3 >= avg_body * multiplier

    # ──────────────────────────────────────────────
    # Setup builders
    # ──────────────────────────────────────────────

    @staticmethod
    def _get_displacement_open(context_bars, sweep_ctx_idx, sweep_type, lookback=5):
        start   = max(0, sweep_ctx_idx - lookback)
        segment = context_bars.iloc[start: sweep_ctx_idx + 1]
        if segment.empty:
            return context_bars.iloc[sweep_ctx_idx]['open']
        if sweep_type == 'bearish':
            idx = segment['open'].idxmin()
        else:
            idx = segment['open'].idxmax()
        return segment.loc[idx, 'open']

    @staticmethod
    def _build_key_levels(levels, swing_pts, kz_bars):
        kl = []
        if levels:
            if levels.has_asia and not np.isnan(levels.asia_high):
                kl.append({'price': levels.asia_high, 'type': 'high', 'label': 'Asia High'})
            if levels.has_asia and not np.isnan(levels.asia_low):
                kl.append({'price': levels.asia_low,  'type': 'low',  'label': 'Asia Low'})
            if levels.has_london and not np.isnan(levels.london_high):
                kl.append({'price': levels.london_high, 'type': 'high', 'label': 'London High'})
            if levels.has_london and not np.isnan(levels.london_low):
                kl.append({'price': levels.london_low,  'type': 'low',  'label': 'London Low'})
        kz_mid   = (kz_bars['high'].max() + kz_bars['low'].min()) / 2
        kz_range = kz_bars['high'].max() - kz_bars['low'].min()
        for sp in swing_pts[-20:]:
            if abs(sp.price - kz_mid) < kz_range * 5:
                kl.append({
                    'price': sp.price,
                    'type':  sp.sp_type,
                    'label': f'HTF Swing {"High" if sp.sp_type == "high" else "Low"}'
                })
        return kl

    @staticmethod
    def _build_sweep_setup(sweep_bar, sweep_time, conf_bar, conf_time,
                           sweep_type, label, kz_range):
        buffer = kz_range * 0.05
        if sweep_type == 'bearish':
            entry, sl, direction = conf_bar['close'], sweep_bar['high'] + buffer, 'SHORT'
        else:
            entry, sl, direction = conf_bar['close'], sweep_bar['low']  - buffer, 'LONG'
        risk = abs(entry - sl)
        if risk <= 0 or risk > kz_range * 3:
            return None
        return {
            'entry_time': conf_time, 'entry': entry, 'sl': sl,
            'risk': risk, 'direction': direction,
            'trigger': label, 'confirmation': 'CISD',
            'reason': f'Sweep {label} + CISD',
        }

    @staticmethod
    def _build_fvg_setup(bar, bar_time, fvg, kz_range, tag):
        zone_size = fvg.top - fvg.bottom
        buffer    = zone_size * 0.1
        if tag == 'FVG':
            if fvg.fvg_type == 'bullish':
                entry, sl, direction = bar['close'], fvg.bottom - buffer, 'LONG'
            else:
                entry, sl, direction = bar['close'], fvg.top   + buffer, 'SHORT'
        else:
            if fvg.fvg_type == 'bearish':
                entry, sl, direction = bar['close'], fvg.bottom - buffer, 'LONG'
            else:
                entry, sl, direction = bar['close'], fvg.top   + buffer, 'SHORT'
        risk = abs(entry - sl)
        if risk <= 0 or risk > kz_range * 3:
            return None
        return {
            'entry_time': bar_time, 'entry': entry, 'sl': sl,
            'risk': risk, 'direction': direction,
            'trigger': f'{fvg.timeframe} {tag}', 'confirmation': tag,
            'reason': f'{fvg.timeframe} {tag} Tap ({fvg.fvg_type})',
        }

    # ──────────────────────────────────────────────
    # Trade simulation
    # ──────────────────────────────────────────────

    @staticmethod
    def _simulate_trade(setup, forward_bars, rr):
        if forward_bars.empty:
            return None
        entry, sl, risk, direction = setup['entry'], setup['sl'], setup['risk'], setup['direction']
        tp = entry + risk * rr if direction == 'LONG' else entry - risk * rr

        outcome = 'OPEN'
        exit_price = exit_time = None
        bars_held = 0

        for bar_time, bar in forward_bars.iterrows():
            bars_held += 1
            if direction == 'LONG':
                if bar['low'] <= sl:
                    outcome, exit_price, exit_time = 'LOSS', sl, bar_time; break
                if bar['high'] >= tp:
                    outcome, exit_price, exit_time = 'WIN',  tp, bar_time; break
            else:
                if bar['high'] >= sl:
                    outcome, exit_price, exit_time = 'LOSS', sl, bar_time; break
                if bar['low'] <= tp:
                    outcome, exit_price, exit_time = 'WIN',  tp, bar_time; break

        if outcome == 'OPEN':
            last = forward_bars.iloc[-1]
            exit_price, exit_time = last['close'], forward_bars.index[-1]
            outcome = ('WIN' if exit_price > entry else 'LOSS') if direction == 'LONG' \
                else ('WIN' if exit_price < entry else 'LOSS')

        pnl_r = (exit_price - entry) / risk if direction == 'LONG' else (entry - exit_price) / risk

        return {
            'date': str(setup['entry_time'].date()),
            'entry_time': setup['entry_time'], 'exit_time': exit_time,
            'direction': direction,
            'entry': round(entry, 2), 'exit': round(exit_price, 2),
            'sl': round(sl, 2), 'tp': round(tp, 2),
            'risk_pts': round(risk, 2), 'outcome': outcome,
            'pnl_r': round(pnl_r, 3), 'rr_target': rr,
            'trigger': setup['trigger'], 'confirmation': setup['confirmation'],
            'reason': setup['reason'], 'bars_held': bars_held,
        }

    # ──────────────────────────────────────────────
    # Display helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _fmt_levels(levels: Optional[SessionLevels]) -> str:
        if levels is None:
            return 'no session data'
        parts = []
        if levels.has_asia and not np.isnan(levels.asia_high):
            parts.append(f"Asia H:{levels.asia_high:.0f} L:{levels.asia_low:.0f}")
        if levels.has_london and not np.isnan(levels.london_high):
            parts.append(f"London H:{levels.london_high:.0f} L:{levels.london_low:.0f}")
        return "  |  ".join(parts) if parts else 'session data incomplete'

    def _print_day_line(self, date: pd.Timestamp, summary: dict, running_r: dict):
        n = summary['setups']
        f = summary['filtered']
        bias = summary.get('htf_bias', '?')

        bias_col = 'green' if bias == 'bullish' else ('red' if bias == 'bearish' else 'gray')
        n_col    = 'cyan' if n > 0 else 'gray'

        r_parts = []
        for rr in sorted(running_r.keys()):
            r = running_r[rr]
            sign = '+' if r >= 0 else ''
            col = 'green' if r >= 0 else 'red'
            r_parts.append(_col(f"{sign}{r:.1f}R", col))

        _p(
            f"  {_col(str(date.date()), 'white'):<12} "
            f"{summary['levels']:<42} "
            f"{_col(str(n) + ' trade' + ('s' if n != 1 else ''), n_col):>8}  "
            f"[{_col(bias[:4].upper(), bias_col)}]  "
            f"{' / '.join(r_parts)}"
        )

    def _print_final_summary(self, all_trades: Dict[float, List[dict]]):
        _p(_col("  =" * 45, 'gray'))
        _p(_col(f"  FINAL RESULTS — {self.symbol}", 'bold'))
        _p(_col("  =" * 45, 'gray'))
        for rr in sorted(all_trades.keys()):
            m = Backtester.calc_metrics(all_trades[rr])
            sign = '+' if m['total_r'] >= 0 else ''
            pf   = f"{m['profit_factor']:.2f}" if m['profit_factor'] != float('inf') else 'inf'
            r_col = 'green' if m['total_r'] >= 0 else 'red'
            wr_col= 'green' if m['win_rate'] >= 33 else 'red'
            _p(
                f"  1:{int(rr)}  {m['total']:3d} trades  "
                f"WR={_col(str(m['win_rate']) + '%', wr_col):<18}  "
                f"R={_col(sign + str(m['total_r']), r_col):<16}  "
                f"PF={pf}  "
                f"MaxDD=-{m['max_drawdown_r']}R  "
                f"Expectancy={m['expectancy_r']}R"
            )
        _p()

    # ──────────────────────────────────────────────
    # Metrics
    # ──────────────────────────────────────────────

    @staticmethod
    def calc_metrics(trades: List[dict]) -> dict:
        if not trades:
            return {
                'total': 0, 'wins': 0, 'losses': 0,
                'win_rate': 0.0, 'total_r': 0.0,
                'avg_win_r': 0.0, 'avg_loss_r': 0.0,
                'profit_factor': 0.0, 'max_drawdown_r': 0.0,
                'expectancy_r': 0.0, 'sharpe': 0.0,
            }
        pnls   = [t['pnl_r'] for t in trades]
        wins   = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        gross_profit = sum(wins)   if wins   else 0.0
        gross_loss   = abs(sum(losses)) if losses else 0.0
        equity       = np.cumsum(pnls)
        running_max  = np.maximum.accumulate(equity)
        max_dd       = float((running_max - equity).max()) if len(equity) > 0 else 0.0
        pnl_arr      = np.array(pnls)
        sharpe       = float(pnl_arr.mean() / pnl_arr.std()) if pnl_arr.std() > 0 else 0.0
        return {
            'total':          len(trades),
            'wins':           len(wins),
            'losses':         len(losses),
            'win_rate':       round(len(wins) / len(trades) * 100, 1),
            'total_r':        round(sum(pnls), 2),
            'avg_win_r':      round(np.mean(wins)   if wins   else 0, 2),
            'avg_loss_r':     round(np.mean(losses) if losses else 0, 2),
            'profit_factor':  round(gross_profit / gross_loss, 2) if gross_loss > 0 else float('inf'),
            'max_drawdown_r': round(max_dd, 2),
            'expectancy_r':   round(np.mean(pnls), 3),
            'sharpe':         round(sharpe, 2),
        }
