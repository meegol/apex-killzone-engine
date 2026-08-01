import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import DataFetcher
from strategy import ICTStrategy
from backtester import Backtester
from report_generator import ReportGenerator

SYMBOLS    = ['NQ=F', 'ES=F', 'MNQ=F', 'MES=F']
RR_TARGETS = [2.0, 3.0, 4.0]


def main():
    print("\n  meegol-backtest | ICT Kill Zone")
    print("  9:30-11:00 AM NY | yfinance 5m ~60 days\n")
    print(f"  symbols : {', '.join(SYMBOLS)}")
    print(f"  rr      : {' | '.join(f'1:{int(r)}' for r in RR_TARGETS)}\n")
    sys.stdout.flush()

    fetcher = DataFetcher()
    results = {}

    for sym in SYMBOLS:
        print(f"\n--- {sym} ---")
        sys.stdout.flush()

        df_5m, df_1h = fetcher.fetch(sym)
        if df_5m is None or df_5m.empty or df_1h is None or df_1h.empty:
            print("  no data, skipping")
            continue

        days = df_5m.index.normalize().nunique()
        print(f"  {len(df_5m):,} 5m bars | {len(df_1h):,} 1h bars | {days} days")
        print(f"  {df_5m.index[0].date()} -> {df_5m.index[-1].date()}")

        bt = Backtester(ICTStrategy(df_5m, df_1h), rr_targets=RR_TARGETS, symbol=sym)
        results[sym] = bt.run()

    if not results:
        print("\nno data for any symbol")
        sys.exit(1)

    print("\n--- report ---")
    rep = ReportGenerator(results)
    path = rep.generate(output_dir="reports")
    abs_path = os.path.abspath(path)
    print(f"saved: {abs_path}")

    print(f"\n  open this in your browser:\n  file:///{abs_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
