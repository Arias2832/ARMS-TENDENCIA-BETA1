"""
ARMS v1.0 - MT5 Connection and Data Download
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os


class MT5Connector:
    """MT5 connection and data download handler"""

    def __init__(self):
        self.connected = False

    def initialize(self, login=None, password="", server=""):
        """Initialize MT5 connection"""
        if not mt5.initialize():
            print(f"❌ Error initializing MT5: {mt5.last_error()}")
            return False

        if login is not None:
            if not mt5.login(login, password, server):
                print(f"❌ Login error: {mt5.last_error()}")
                mt5.shutdown()
                return False

        self.connected = True
        account_info = mt5.account_info()
        if account_info:
            print(f"✅ Connected to MT5 - Account: {account_info.login} | Server: {account_info.server}")

        return True

    def download_historical_data(self, symbol, timeframe, start_date, end_date):
        """Download historical data from MT5"""
        if not self.connected:
            print("❌ No MT5 connection")
            return None

        print(f"📊 Downloading {symbol} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

        if rates is None or len(rates) == 0:
            print(f"❌ Download error: {mt5.last_error()}")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={
            'time': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        }, inplace=True)

        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

        print(f"✅ {len(df)} candles downloaded ({df['datetime'].iloc[0]} - {df['datetime'].iloc[-1]})")
        self._validate_data(df)
        return df

    def _validate_data(self, df):
        """Validate downloaded data integrity"""
        null_counts = df.isnull().sum()
        duplicates = df['datetime'].duplicated().sum()
        chronological = df['datetime'].is_monotonic_increasing

        issues = []
        if null_counts.sum() > 0:
            issues.append(f"{null_counts.sum()} null values")
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate timestamps")
        if not chronological:
            issues.append("data out of order")

        if issues:
            print(f"⚠️ Warnings: {', '.join(issues)}")

    def save_to_csv(self, df, filepath):
        """Save DataFrame to CSV"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)
        print(f"💾 Data saved: {filepath} ({os.path.getsize(filepath) / 1024:.1f} KB)")

    def shutdown(self):
        """Close MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("🔌 Disconnected from MT5")
