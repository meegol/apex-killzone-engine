# strategy.py â€” ICT concept detection (FVG, sweep, CISD, session levels)

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import pytz

ET = pytz.timezone('America/New_York')




@dataclass
class FVG:
    formed_time: pd.Timestamp
    fvg_type: str        # 'bullish' | 'bearish'
    top: float           # upper boundary of the gap
    bottom: float        # lower boundary of the gap
    midpoint: float      # consequent encroachment (CE) = 50% of zone
    timeframe: str       # '1H' | '4H'
    # displacement candle's open â€” used for CISD reference
    displacement_open: float = 0.0
    # State flags
    filled: bool = False
    inverted: bool = False   # True when it becomes an IFVG
    fill_time: Optional[pd.Timestamp] = None


@dataclass
class SwingPoint:
    formed_time: pd.Timestamp
    price: float
    sp_type: str   # 'high' | 'low'
    timeframe: str = '4H'


@dataclass
class SessionLevels:
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




class ICTStrategy:

    def __init__(self, df_5m: pd.DataFrame, df_1h: pd.DataFrame):
        self.df_5m = df_5m
        self.df_1h = df_1h
        self.df_4h = self._resample_4h(df_1h)

    # â”€â”€ Resampling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
        df = df_1h.resample('4h', closed='left', label='left').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }).dropna(subset=['open', 'close'])
        return df

    # â”€â”€ Session levels â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_session_levels(self, date: pd.Timestamp) -> Optional[SessionLevels]:
        # Asia: 7 PM prev day â†’ midnight; London: 2â€“5 AM; both ET
        d = date.date()

        # Monday: Asia session was Friday evening â†’ roll back 3 days
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

    # â”€â”€ Fair Value Gap detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # â”€â”€ HTF Swing Point detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def find_swing_points(
        self,
        as_of: pd.Timestamp,
        strength: int = 3,
    ) -> List[SwingPoint]:
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

    # —————————————————————————————

    @staticmethod
    def update_fvg_status(fvgs: List[FVG], bar: pd.Series, bar_time: pd.Timestamp) -> None:
        for fvg in fvgs:
            if fvg.inverted:
                continue
            if fvg.fvg_type == 'bullish':
                if bar['close'] < fvg.bottom:
                    fvg.filled = True
                    fvg.inverted = True
                    fvg.fill_time = bar_time
            else:
                if bar['close'] > fvg.top:
                    fvg.filled = True
                    fvg.inverted = True
                    fvg.fill_time = bar_time

    # —————————————————————————————

    @staticmethod
    def check_sweep(bar: pd.Series, level: float, level_type: str) -> bool:
        if level_type == 'high':
            return bar['high'] > level and bar['close'] < level
        if level_type == 'low':
            return bar['low'] < level and bar['close'] > level
        return False

    # —————————————————————————————

    @staticmethod
    def find_cisd(
        window_df: pd.DataFrame,
        sweep_type: str,
        sweep_local_idx: int,
        displacement_open: float,
        max_bars_ahead: int = 8,
    ) -> Optional[int]:
        if sweep_local_idx < 0 or sweep_local_idx >= len(window_df):
            return None

        search_start = sweep_local_idx + 1
        search_end   = min(len(window_df), sweep_local_idx + 1 + max_bars_ahead)

        for i in range(search_start, search_end):
            row = window_df.iloc[i]
            if sweep_type == 'bearish':
                if row['close'] < displacement_open:
                    return i
            else:
                if row['close'] > displacement_open:
                    return i

        return None

    # —————————————————————————————

    @staticmethod
    def check_fvg_tap(bar: pd.Series, fvgs: List[FVG]) -> Optional[FVG]:
        for fvg in fvgs:
            if fvg.filled or fvg.inverted:
                continue
            if fvg.fvg_type == 'bullish':
                if bar['low'] <= fvg.top and bar['close'] >= fvg.bottom:
                    return fvg
            else:
                if bar['high'] >= fvg.bottom and bar['close'] <= fvg.top:
                    return fvg
        return None

    # —————————————————————————————

    @staticmethod
    def check_ifvg_tap(bar: pd.Series, fvgs: List[FVG]) -> Optional[FVG]:
        for fvg in fvgs:
            if not fvg.inverted:
                continue
            if fvg.fvg_type == 'bearish':
                if bar['low'] <= fvg.top and bar['close'] >= fvg.bottom:
                    return fvg
            else:
                if bar['high'] >= fvg.bottom and bar['close'] <= fvg.top:
                    return fvg
        return None

    # —————————————————————————————

    def get_trading_days(self) -> List[pd.Timestamp]:
        dates = self.df_5m.index.normalize().unique()
        return sorted(d for d in dates if d.weekday() < 5)
