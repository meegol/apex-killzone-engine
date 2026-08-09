"""
strategy.py — Core ICT concept implementations.

Concepts implemented:
  - Session High/Low (Asia: 7 PM–midnight ET, London Kill Zone: 2–5 AM ET)
  - Fair Value Gap (FVG) detection on 1H and 4H timeframes
  - HTF Swing Point detection (4H)
  - Liquidity Sweep detection
  - CISD (Change in State of Delivery) — candle open/close based
  - Inversion FVG (IFVG) tracking and tap detection
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class FVG:
    """A Fair Value Gap on a specific timeframe."""
    formed_time: pd.Timestamp
    fvg_type: str        # 'bullish' | 'bearish'
    top: float           # upper boundary of the gap
    bottom: float        # lower boundary of the gap
    midpoint: float      # consequent encroachment (CE) = 50% of zone
    timeframe: str       # '1H' | '4H'
    # displacement candle's open — used for CISD reference
    displacement_open: float = 0.0
    # State flags
    filled: bool = False
    inverted: bool = False   # True when it becomes an IFVG
    fill_time: Optional[pd.Timestamp] = None


@dataclass
class SwingPoint:
    """An HTF swing high or swing low on the 4H chart."""
    formed_time: pd.Timestamp
    price: float
    sp_type: str   # 'high' | 'low'
    timeframe: str = '4H'


@dataclass
class SessionLevels:
    """Asia and London Kill Zone High/Low for a single trading day."""
    date: str
    asia_high: float
    asia_low: float
    asia_high_time: pd.Timestamp
    asia_low_time: pd.Timestamp
    london_high: float
    london_low: float
    london_high_time: pd.Timestamp
    london_low_time: pd.Timestamp
    has_asia: bool = True
    has_london: bool = True


# ──────────────────────────────────────────────
# Main strategy class
# ──────────────────────────────────────────────

class ICTStrategy:
    """Encapsulates all ICT concept detection logic."""

    def __init__(self, df_5m: pd.DataFrame, df_1h: pd.DataFrame):
        self.df_5m = df_5m
        self.df_1h = df_1h
        self.df_4h = self._resample_4h(df_1h)

    # ── Resampling ──────────────────────────────

    @staticmethod
    def _resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
        """Resample 1H bars to 4H OHLCV."""
        df = df_1h.resample('4h', closed='left', label='left').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }).dropna(subset=['open', 'close'])
        return df

    # ── Session levels ──────────────────────────

    def get_session_levels(self, date: pd.Timestamp) -> Optional[SessionLevels]:
        """
        Compute Asia and London Kill Zone H/L for a given NY trading date.

        Asia  : 7:00 PM previous calendar day → midnight ET (before date)
        London: 2:00 AM → 5:00 AM ET (same trading date)
        """
        d = date.date()

        # Monday: Asia session was Friday evening → roll back 3 days
        if date.weekday() == 0:
            prev_date = date - pd.Timedelta(days=3)
        else:
            prev_date = date - pd.Timedelta(days=1)

        pd_d = prev_date.date()

        asia_start = ET.localize(datetime(pd_d.year, pd_d.month, pd_d.day, 19, 0))
        asia_end   = ET.localize(datetime(d.year,    d.month,    d.day,    0, 0))
        lon_start  = ET.localize(datetime(d.year,    d.month,    d.day,    2, 0))
        lon_end    = ET.localize(datetime(d.year,    d.month,    d.day,    5, 0))

        asia_bars = self.df_5m.loc[
            (self.df_5m.index >= asia_start) & (self.df_5m.index < asia_end)
        ]
        lon_bars = self.df_5m.loc[
            (self.df_5m.index >= lon_start) & (self.df_5m.index < lon_end)
        ]

        # We require at least some bars for each session
        has_asia   = len(asia_bars) >= 3
        has_london = len(lon_bars) >= 3

        # Fallback if session is completely missing
        if not has_asia and not has_london:
            return None

        def _hl(bars, has):
            if not has or bars.empty:
                return np.nan, np.nan, None, None
            hi_idx = bars['high'].idxmax()
            lo_idx = bars['low'].idxmin()
            return bars['high'].max(), bars['low'].min(), hi_idx, lo_idx

        ah, al, aht, alt = _hl(asia_bars, has_asia)
        lh, ll, lht, llt = _hl(lon_bars, has_london)

        return SessionLevels(
            date=str(d),
            asia_high=ah,           asia_low=al,
            asia_high_time=aht,     asia_low_time=alt,
            london_high=lh,         london_low=ll,
            london_high_time=lht,   london_low_time=llt,
            has_asia=has_asia,      has_london=has_london,
        )

    # ── Fair Value Gap detection ─────────────────

    def find_fvgs(self, as_of: pd.Timestamp) -> List[FVG]:
        """
        Return all FVGs on the 1H and 4H charts formed *strictly before* as_of.
        Only the most recent 60 candles per timeframe are considered (relevance filter).
        """
        fvgs: List[FVG] = []

        for tf, df in [('1H', self.df_1h), ('4H', self.df_4h)]:
            df_ctx = df.loc[df.index < as_of].tail(60)
            if len(df_ctx) < 3:
                continue

            for i in range(1, len(df_ctx) - 1):
                c1 = df_ctx.iloc[i - 1]
                c2 = df_ctx.iloc[i]      # displacement candle
                c3 = df_ctx.iloc[i + 1]
                formed = df_ctx.index[i]

                # Bullish FVG: gap between c1.high and c3.low
                if c1['high'] < c3['low']:
                    bot = c1['high']
                    top = c3['low']
                    size = top - bot
                    if size > 0:
                        fvgs.append(FVG(
                            formed_time=formed,
                            fvg_type='bullish',
                            top=top, bottom=bot,
                            midpoint=bot + size / 2,
                            timeframe=tf,
                            displacement_open=c2['open'],
                        ))

                # Bearish FVG: gap between c3.high and c1.low
                elif c1['low'] > c3['high']:
                    bot = c3['high']
                    top = c1['low']
                    size = top - bot
                    if size > 0:
                        fvgs.append(FVG(
                            formed_time=formed,
                            fvg_type='bearish',
                            top=top, bottom=bot,
                            midpoint=bot + size / 2,
                            timeframe=tf,
                            displacement_open=c2['open'],
                        ))

        # Deduplicate by (formed_time, fvg_type, timeframe)
        seen = set()
        unique: List[FVG] = []
        for fvg in fvgs:
            key = (fvg.formed_time, fvg.fvg_type, fvg.timeframe)
            if key not in seen:
                seen.add(key)
                unique.append(fvg)

        return unique

    # ── HTF Swing Point detection ────────────────

    def find_swing_points(
        self,
        as_of: pd.Timestamp,
        strength: int = 3,
    ) -> List[SwingPoint]:
        """
        Identify 4H swing highs and lows formed before as_of.

        strength: number of candles on EACH side that must be lower/higher.
        Only the last 80 candles are considered.
        """
        df_ctx = self.df_4h.loc[self.df_4h.index < as_of].tail(80)
        n = len(df_ctx)
        points: List[SwingPoint] = []

        for i in range(strength, n - strength):
            hi = df_ctx.iloc[i]['high']
            lo = df_ctx.iloc[i]['low']
            t  = df_ctx.index[i]

            left_highs  = [df_ctx.iloc[i - j]['high'] for j in range(1, strength + 1)]
            right_highs = [df_ctx.iloc[i + j]['high'] for j in range(1, strength + 1)]
            left_lows   = [df_ctx.iloc[i - j]['low']  for j in range(1, strength + 1)]
            right_lows  = [df_ctx.iloc[i + j]['low']  for j in range(1, strength + 1)]

            if hi > max(left_highs) and hi > max(right_highs):
                points.append(SwingPoint(formed_time=t, price=hi, sp_type='high'))

            if lo < min(left_lows) and lo < min(right_lows):
                points.append(SwingPoint(formed_time=t, price=lo, sp_type='low'))

        return points

    # ── FVG state management ─────────────────────

    @staticmethod
    def update_fvg_status(fvgs: List[FVG], bar: pd.Series, bar_time: pd.Timestamp) -> None:
        """
        Walk through all FVGs and update their filled/inverted state based on the bar.
        An FVG is "filled" when price **closes** through its entire zone.
        Once filled it becomes an IFVG (inverted).
        """
        for fvg in fvgs:
            if fvg.inverted:
                continue  # Already an IFVG — state is final

            if fvg.fvg_type == 'bullish':
                # Filled when a bar CLOSES below the bottom of the bullish FVG
                if bar['close'] < fvg.bottom:
                    fvg.filled = True
                    fvg.inverted = True
                    fvg.fill_time = bar_time
            else:  # bearish
                # Filled when a bar CLOSES above the top of the bearish FVG
                if bar['close'] > fvg.top:
                    fvg.filled = True
                    fvg.inverted = True
                    fvg.fill_time = bar_time

    # ── Sweep detection ──────────────────────────

    @staticmethod
    def check_sweep(bar: pd.Series, level: float, level_type: str) -> bool:
        """
        Returns True if the bar sweeps the given level.

        For a HIGH sweep  (targeting buy-side liquidity):
          - bar's HIGH wicks above the level AND bar CLOSES BELOW it.
        For a LOW  sweep  (targeting sell-side liquidity):
          - bar's LOW wicks below the level AND bar CLOSES ABOVE it.
        """
        if level_type == 'high':
            return bar['high'] > level and bar['close'] < level
        if level_type == 'low':
            return bar['low'] < level and bar['close'] > level
        return False

    # ── CISD detection ───────────────────────────

    @staticmethod
    def find_cisd(
        window_df: pd.DataFrame,
        sweep_type: str,
        sweep_local_idx: int,
        displacement_open: float,
        max_bars_ahead: int = 8,
    ) -> Optional[int]:
        """
        Find a CISD (Change in State of Delivery) candle after a sweep.

        ICT Definition: CISD is a candle that CLOSES on the opposite side of
        the OPENING PRICE of the displacement candles that drove price into
        the liquidity level.

        sweep_type        : 'bearish' (swept a high) | 'bullish' (swept a low)
        sweep_local_idx   : index of the sweep bar within window_df
        displacement_open : open price of the displacement candle (pre-sweep move)
        max_bars_ahead    : maximum number of bars to look forward for CISD

        Returns the local index of the confirming bar, or None.
        """
        if sweep_local_idx < 0 or sweep_local_idx >= len(window_df):
            return None

        search_start = sweep_local_idx + 1
        search_end   = min(len(window_df), sweep_local_idx + 1 + max_bars_ahead)

        for i in range(search_start, search_end):
            row = window_df.iloc[i]
            if sweep_type == 'bearish':
                # CISD: close BELOW the displacement candle's open → sell-side delivery
                if row['close'] < displacement_open:
                    return i
            else:  # bullish
                # CISD: close ABOVE the displacement candle's open → buy-side delivery
                if row['close'] > displacement_open:
                    return i

        return None

    # ── FVG tap detection ────────────────────────

    @staticmethod
    def check_fvg_tap(bar: pd.Series, fvgs: List[FVG]) -> Optional[FVG]:
        """
        Returns the first un-filled FVG that price taps into.
        Price must enter the zone (wick) but NOT close fully through it.
        """
        for fvg in fvgs:
            if fvg.filled or fvg.inverted:
                continue
            if fvg.fvg_type == 'bullish':
                # Price wicks into the bullish zone from above (pullback)
                if bar['low'] <= fvg.top and bar['close'] >= fvg.bottom:
                    return fvg
            else:  # bearish
                # Price wicks into the bearish zone from below (pullback)
                if bar['high'] >= fvg.bottom and bar['close'] <= fvg.top:
                    return fvg
        return None

    # ── IFVG tap detection ───────────────────────

    @staticmethod
    def check_ifvg_tap(bar: pd.Series, fvgs: List[FVG]) -> Optional[FVG]:
        """
        Returns the first IFVG that price re-tests.

        Bullish IFVG (was bearish FVG, now support):
          Price wicks into zone and closes at/above bottom → LONG signal
        Bearish IFVG (was bullish FVG, now resistance):
          Price wicks into zone and closes at/below top → SHORT signal
        """
        for fvg in fvgs:
            if not fvg.inverted:
                continue
            if fvg.fvg_type == 'bearish':
                # Originally bearish → now bullish IFVG (support)
                if bar['low'] <= fvg.top and bar['close'] >= fvg.bottom:
                    return fvg
            else:
                # Originally bullish → now bearish IFVG (resistance)
                if bar['high'] >= fvg.bottom and bar['close'] <= fvg.top:
                    return fvg
        return None

    # ── Utility ──────────────────────────────────

    def get_trading_days(self) -> List[pd.Timestamp]:
        """Return sorted list of unique ET trading dates in the 5m dataset."""
        dates = self.df_5m.index.normalize().unique()
        return sorted(d for d in dates if d.weekday() < 5)
