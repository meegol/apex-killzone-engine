# forward_test.py — runs the ICT strategy on recent data and writes forwardTest.json

import sys
import io
import os
import json
import pytz
from datetime import datetime, timedelta
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import DataFetcher
from strategy import ICTStrategy
from backtester import Backtester
from discord_signals import dispatch_trade_alerts

ET = pytz.timezone('America/New_York')
SYMBOLS = ['NQ=F', 'ES=F', 'MNQ=F', 'MES=F']
RR_TARGET = 4.0  # Best performing RR ratio from historical backtest (1:4)


def run_forward_test():
    fetcher = DataFetcher()
    now_et = datetime.now(ET)
    
    all_symbol_trades = []
    symbol_summaries = {}
    equity_curve = []
    running_cumulative_r = 0.0

    fetched_dfs = {}
    for sym in SYMBOLS:
        print(f"  Fetching intraday data for {sym}...")
        df_5m, df_1h = fetcher.fetch(sym)
        if df_5m is None or df_5m.empty or df_1h is None or df_1h.empty:
            print(f"  [WARN] No data for {sym}, skipping.")
            continue

        fetched_dfs[sym] = df_5m
        strategy = ICTStrategy(df_5m, df_1h)
        bt = Backtester(strategy, rr_targets=[RR_TARGET], symbol=sym)
        
        results = bt.run()
        trades_14 = results.get(RR_TARGET, [])
        m = Backtester.calc_metrics(trades_14)
        symbol_summaries[sym] = {
            'symbol': sym,
            'trades': m['total'],
            'win_rate': m['win_rate'],
            'total_r': m['total_r'],
            'profit_factor': m['profit_factor'],
            'max_drawdown': m['max_drawdown_r'],
            'expectancy': m['expectancy_r'],
        }

        for t in trades_14:
            t['symbol'] = sym
            all_symbol_trades.append(t)

    # Build forward test equity points & attach candle slices for live chart view
    trade_history = []
    for idx, t in enumerate(all_symbol_trades, 1):
        running_cumulative_r += t['pnl_r']
        running_cumulative_r = round(running_cumulative_r, 2)

        # Slice 5m bars around trade for chart modal view
        sym = t['symbol']
        entry_time = t['entry_time']
        exit_time = t['exit_time'] if isinstance(t['exit_time'], pd.Timestamp) else entry_time + pd.Timedelta(hours=2)
        df_5m_sym = fetched_dfs.get(sym)
        bars_list = []
        if df_5m_sym is not None and not df_5m_sym.empty:
            if getattr(df_5m_sym.index, 'tz', None) is not None:
                if entry_time.tzinfo is None:
                    entry_time = ET.localize(entry_time)
                if isinstance(exit_time, pd.Timestamp) and exit_time.tzinfo is None:
                    exit_time = ET.localize(exit_time)
            elif entry_time.tzinfo is not None:
                entry_time = entry_time.tz_localize(None)
                if isinstance(exit_time, pd.Timestamp):
                    exit_time = exit_time.tz_localize(None)

            trade_dt = entry_time.date()
            if getattr(df_5m_sym.index, 'tz', None) is not None:
                start_slice = ET.localize(datetime(trade_dt.year, trade_dt.month, trade_dt.day, 9, 0))
                end_slice = ET.localize(datetime(trade_dt.year, trade_dt.month, trade_dt.day, 16, 15))
            else:
                start_slice = datetime(trade_dt.year, trade_dt.month, trade_dt.day, 9, 0)
                end_slice = datetime(trade_dt.year, trade_dt.month, trade_dt.day, 16, 15)

            slice_df = df_5m_sym.loc[(df_5m_sym.index >= start_slice) & (df_5m_sym.index <= end_slice)]
            
            if slice_df.empty:
                slice_df = df_5m_sym.iloc[-60:]
            
            for btime, b in slice_df.iterrows():
                unix_sec = int(btime.timestamp())
                bars_list.append({
                    'time': unix_sec,
                    'time_str': btime.strftime('%H:%M'),
                    'full_time': btime.strftime('%Y-%m-%d %H:%M ET'),
                    'open': round(float(b['open']), 2),
                    'high': round(float(b['high']), 2),
                    'low': round(float(b['low']), 2),
                    'close': round(float(b['close']), 2),
                })
        
        trade_item = {
            'id': idx,
            'date': t['date'],
            'entry_time': t['entry_time'].strftime('%Y-%m-%d %H:%M ET'),
            'exit_time': t['exit_time'].strftime('%Y-%m-%d %H:%M ET') if isinstance(t['exit_time'], pd.Timestamp) else 'Open',
            'symbol': t['symbol'],
            'direction': t['direction'],
            'entry': t['entry'],
            'exit': t['exit'],
            'sl': t['sl'],
            'tp': t['tp'],
            'risk_pts': t['risk_pts'],
            'outcome': t['outcome'],
            'pnl_r': t['pnl_r'],
            'reason': t['reason'],
            'trigger': t['trigger'],
            'confirmation': t['confirmation'],
            'cumulative_r': running_cumulative_r,
            'bars': bars_list,
        }
        trade_history.append(trade_item)
        equity_curve.append({'trade': idx, 'date': t['date'], 'symbol': t['symbol'], 'cumulative_r': running_cumulative_r})
    wins = [t for t in all_symbol_trades if t['pnl_r'] > 0]
    total_trades = len(all_symbol_trades)
    win_rate = round(len(wins) / total_trades * 100, 1) if total_trades > 0 else 0.0
    total_r = round(sum(t['pnl_r'] for t in all_symbol_trades), 2)
    
    gross_profit = sum(t['pnl_r'] for t in wins) if wins else 0.0
    gross_loss = abs(sum(t['pnl_r'] for t in all_symbol_trades if t['pnl_r'] <= 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float('inf')

    recent_feed = list(reversed(trade_history[-15:])) if trade_history else []

    payload = {
        'last_updated': now_et.strftime('%Y-%m-%d %H:%M:%S ET'),
        'status': 'ACTIVE',
        'execution_frequency': 'Daily post-market (5:00 PM ET)',
        'target_rr': '1:4',
        'metrics': {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_r': total_r,
            'profit_factor': profit_factor if profit_factor != float('inf') else 999.0,
            'winning_trades': len(wins),
            'losing_trades': total_trades - len(wins),
        },
        'symbol_summaries': symbol_summaries,
        'equity_curve': equity_curve,
        'recent_feed': recent_feed,
        'all_trades': trade_history,
    }

    json_path_src = os.path.join(os.path.dirname(__file__), 'website', 'src', 'data', 'forwardTest.json')
    os.makedirs(os.path.dirname(json_path_src), exist_ok=True)
    with open(json_path_src, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    print(f"  [OK] Saved live forward test JSON to {json_path_src}")

    json_path_docs = os.path.join(os.path.dirname(__file__), 'docs', 'data', 'forwardTest.json')
    os.makedirs(os.path.dirname(json_path_docs), exist_ok=True)
    with open(json_path_docs, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    print(f"  [OK] Saved live forward test JSON to {json_path_docs}")

    # Generate public API JSON endpoints (/api/trades.json)
    try:
        from generate_api import generate_api_data
        generate_api_data()
    except Exception as e:
        print(f"  [WARN] Failed to generate API data: {e}")

    # Dispatch Discord Webhook alerts for new entries & outcomes
    dispatch_trade_alerts(trade_history)

    print("  done.\n")


if __name__ == "__main__":
    run_forward_test()
