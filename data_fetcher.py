import yfinance as yf
import pandas as pd
import pytz

ET = pytz.timezone('America/New_York')

POINT_VALUES = {
    'NQ=F': 20,
    'ES=F': 50,
    'MNQ=F': 2,
    'MES=F': 5,
}


class DataFetcher:
    def fetch(self, symbol):
        df_5m = self._get(symbol, '5m', '60d')
        df_1h = self._get(symbol, '1h', '730d')
        if df_5m is None or df_1h is None:
            return None, None
        return df_5m, df_1h

    def _get(self, symbol, interval, period):
        try:
            raw = yf.download(symbol, period=period, interval=interval,
                              progress=False, auto_adjust=True)
        except Exception as e:
            print(f"  yfinance error ({symbol} {interval}): {e}")
            return None

        if raw is None or raw.empty:
            return None

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        raw = raw[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        raw.columns = ['open', 'high', 'low', 'close', 'volume']

        if raw.index.tzinfo is None:
            raw.index = raw.index.tz_localize('UTC')
        raw.index = raw.index.tz_convert(ET)

        return raw.dropna(subset=['open', 'high', 'low', 'close'])
