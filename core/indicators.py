"""
ARMS v1.0 - Technical Indicators
"""

import pandas as pd
import pandas_ta as ta


class IndicatorCalculator:
    """Technical indicator calculator"""

    def __init__(self, ema_period=20, ema_mid=50, ema_long=200, atr_period=14, 
                 adx_period=14, rsi_period=14, macd_fast=12, macd_slow=26, 
                 macd_signal=9, volume_sma=20, atr_adjustment=1.0):
        self.ema_period = ema_period
        self.ema_mid = ema_mid
        self.ema_long = ema_long
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.volume_sma = volume_sma
        self.atr_adjustment = atr_adjustment

    def calculate_ema(self, df):
        """Calculate EMAs (20, 50, 200)"""
        df['ema20'] = ta.ema(df['close'], length=self.ema_period)
        df['ema50'] = ta.ema(df['close'], length=self.ema_mid)
        df['ema200'] = ta.ema(df['close'], length=self.ema_long)
        return df

    def calculate_atr(self, df):
        """Calculate ATR using Wilder's method"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.ewm(alpha=1 / self.atr_period, min_periods=self.atr_period, adjust=False).mean()
        df['atr'] = atr * self.atr_adjustment
        return df

    def calculate_adx(self, df):
        """Calculate ADX and Directional Indicators"""
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=self.adx_period)
        df['adx'] = adx_df[f'ADX_{self.adx_period}']
        df['plus_di'] = adx_df[f'DMP_{self.adx_period}']
        df['minus_di'] = adx_df[f'DMN_{self.adx_period}']
        return df

    def calculate_rsi(self, df):
        """Calculate RSI"""
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_period)
        return df

    def calculate_macd(self, df):
        """Calculate MACD"""
        macd_df = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal)
        df['macd'] = macd_df[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        df['macd_signal'] = macd_df[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        df['macd_histogram'] = macd_df[f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        return df

    def calculate_volume(self, df):
        """Calculate volume SMA"""
        df['volume_sma'] = ta.sma(df['volume'], length=self.volume_sma)
        return df

    def calculate_all_indicators(self, df):
        """Calculate all technical indicators"""
        print("\n📊 Calculating indicators...")
        
        df = df.copy()
        df = self.calculate_ema(df)
        df = self.calculate_atr(df)
        df = self.calculate_adx(df)
        df = self.calculate_rsi(df)
        df = self.calculate_macd(df)
        df = self.calculate_volume(df)
        
        initial_rows = len(df)
        df = df.dropna()
        removed_rows = initial_rows - len(df)
        
        print(f"✅ Indicators calculated: {len(df)} valid candles ({removed_rows} removed)")
        return df

    def get_indicator_summary(self, df):
        """Display indicator summary"""
        print("\n" + "=" * 60)
        print("INDICATOR SUMMARY")
        print("=" * 60)
        
        indicators = {
            'EMA20': 'ema20',
            'EMA50': 'ema50',
            'EMA200': 'ema200',
            'ATR': 'atr',
            'ADX': 'adx',
            '+DI': 'plus_di',
            '-DI': 'minus_di',
            'RSI': 'rsi',
            'MACD': 'macd',
            'MACD Signal': 'macd_signal',
            'MACD Hist': 'macd_histogram'
        }
        
        for name, col in indicators.items():
            if col in df.columns:
                print(f"{name}: Min {df[col].min():.3f} | Max {df[col].max():.3f} | Last {df[col].iloc[-1]:.3f}")
